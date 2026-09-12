"""Security posture engine: hashes, binaries, downloads, provenance.

Builds ``data/security.json`` — the machine-readable security report every
release is gated on (``security.yml`` fails the pipeline when a *critical*
finding appears):

* SHA-256 verification of every recorded digest (format + provenance);
* SHA-512 verification wherever upstreams publish one;
* duplicate-binary detection (the same digest shipping under two bundle IDs
  is either a rebrand or a trojan — both deserve a human look);
* download-integrity rollup from the latest health probes;
* provenance audit (official upstream vs community build vs unknown).

Offline: all signals come from ``feeds/state.json``, ``feeds/apps.json``
and the latest health / status documents. Nothing here downloads binaries.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

SECURITY_SCHEMA_VERSION = 1

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SHA512_RE = re.compile(r"^[0-9a-f]{128}$")


def utcnow() -> str:
    """Current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _digests(entry: dict[str, Any]) -> dict[str, str]:
    found: dict[str, str] = {}
    for field, pattern in (
        ("sha256", SHA256_RE),
        ("digest", SHA256_RE),
        ("sha512", SHA512_RE),
    ):
        raw = entry.get(field)
        if isinstance(raw, str) and raw.strip():
            value = raw.strip().lower().removeprefix("sha256:").removeprefix("sha512:")
            if pattern.match(value):
                found["sha512" if field == "sha512" else "sha256"] = value
            else:
                found[f"{field}_invalid"] = raw.strip()[:128]
    text = str(entry.get("localizedDescription", ""))
    match = re.search(r"\b[0-9a-f]{64}\b", text.lower())
    if match and "sha256" not in found:
        found["sha256_changelog"] = match.group(0)
    return found


def verify_hashes(apps: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit SHA-256 / SHA-512 coverage across the newest versions."""
    report: dict[str, Any] = {
        "apps": 0,
        "sha256": 0,
        "sha512": 0,
        "missing": [],
        "invalid": [],
    }
    for app in apps:
        if not isinstance(app, dict):
            continue
        report["apps"] += 1
        slug = str(app.get("slug") or app.get("id") or app.get("name") or "?")
        versions = app.get("versions")
        newest = versions[0] if isinstance(versions, list) and versions else app
        if not isinstance(newest, dict):
            report["missing"].append(slug)
            continue
        digests = _digests(newest)
        if "sha256" in digests or "sha256_changelog" in digests:
            report["sha256"] += 1
        else:
            report["missing"].append(slug)
        if "sha512" in digests:
            report["sha512"] += 1
        if any(key.endswith("_invalid") for key in digests):
            report["invalid"].append(slug)
    report["missing"] = sorted(report["missing"])
    report["invalid"] = sorted(report["invalid"])
    return report


def find_duplicate_binaries(apps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find digests shared by two or more distinct bundle identifiers."""
    owners: dict[str, set[str]] = {}
    for app in apps:
        if not isinstance(app, dict):
            continue
        bundle = str(app.get("bundleIdentifier", ""))
        versions = app.get("versions")
        newest = versions[0] if isinstance(versions, list) and versions else app
        if not isinstance(newest, dict):
            continue
        digest = _digests(newest).get("sha256", "")
        if bundle and digest:
            owners.setdefault(digest, set()).add(bundle)
    dupes = [{"sha256": digest, "bundles": sorted(bundles)} for digest, bundles in owners.items() if len(bundles) > 1]
    return sorted(dupes, key=lambda item: (-len(item["bundles"]), item["sha256"]))


def download_integrity(
    apps: list[dict[str, Any]],
    health: dict[str, Any] | None,
) -> dict[str, Any]:
    """Roll health probes into reachable / failing / unknown buckets."""
    health = health if isinstance(health, dict) else {}
    nodes = health.get("apps", health.get("sources", []))
    status_by_id: dict[str, str] = {}
    if isinstance(nodes, list):
        for node in nodes:
            if isinstance(node, dict):
                key = str(node.get("slug") or node.get("id") or node.get("app") or "")
                status_by_id[key] = str(node.get("status") or node.get("health") or "unknown").lower()
    elif isinstance(nodes, dict):
        status_by_id = {str(key): str(value).lower() for key, value in nodes.items()}
    integrity: dict[str, Any] = {"reachable": [], "failing": [], "unknown": []}
    for app in apps:
        if not isinstance(app, dict):
            continue
        slug = str(app.get("slug") or app.get("id") or "")
        status = status_by_id.get(slug, status_by_id.get(str(app.get("bundleIdentifier", "")), "unknown"))
        if status in ("healthy", "online", "reachable", "ok", "true"):
            integrity["reachable"].append(slug)
        elif status in ("unavailable", "offline", "failing", "failed", "false"):
            integrity["failing"].append(slug)
        else:
            integrity["unknown"].append(slug)
    for key in integrity:
        integrity[key] = sorted(integrity[key])
    return integrity


def provenance_audit(catalog_apps: list[dict[str, Any]]) -> dict[str, Any]:
    """Count official vs community vs unknown provenance declarations."""
    audit: dict[str, Any] = {"official": 0, "community": 0, "unknown": [], "total": 0}
    for app in catalog_apps:
        if not isinstance(app, dict):
            continue
        audit["total"] += 1
        verification = app.get("verification")
        method = verification.get("method", "") if isinstance(verification, dict) else ""
        build = str(app.get("build") or (verification.get("build") if isinstance(verification, dict) else ""))
        blob = f"{method} {build}".lower()
        if "community" in blob:
            audit["community"] += 1
        elif method or "official" in blob or app.get("upstream"):
            audit["official"] += 1
        else:
            audit["unknown"].append(str(app.get("slug") or app.get("name") or "?"))
    audit["unknown"] = sorted(audit["unknown"])
    return audit


def build_security_report(
    *,
    apps: list[dict[str, Any]],
    catalog_apps: list[dict[str, Any]] | None = None,
    health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the ``data/security.json`` document and its findings."""
    hashes = verify_hashes(apps)
    duplicates = find_duplicate_binaries(apps)
    downloads = download_integrity(apps, health)
    provenance = provenance_audit(catalog_apps if catalog_apps is not None else apps)
    findings: list[dict[str, Any]] = []
    for slug in hashes["invalid"]:
        findings.append(
            {"severity": "critical", "check": "hash-format", "id": slug, "detail": "recorded digest is malformed"}
        )
    for dupe in duplicates:
        findings.append(
            {
                "severity": "high",
                "check": "duplicate-binary",
                "id": ",".join(dupe["bundles"]),
                "detail": f"digest {dupe['sha256'][:16]}… ships under {len(dupe['bundles'])} bundle IDs",
            }
        )
    for slug in downloads["failing"]:
        findings.append(
            {
                "severity": "medium",
                "check": "download-unreachable",
                "id": slug,
                "detail": "latest health probe could not reach the download",
            }
        )
    for slug in hashes["missing"]:
        findings.append(
            {
                "severity": "low",
                "check": "hash-missing",
                "id": slug,
                "detail": "no SHA-256 recorded for the newest version",
            }
        )
    critical = sum(1 for item in findings if item["severity"] == "critical")
    return {
        "schemaVersion": SECURITY_SCHEMA_VERSION,
        "generatedAt": utcnow(),
        "verdict": "fail" if critical else "pass",
        "summary": {
            "apps": hashes["apps"],
            "sha256": hashes["sha256"],
            "sha512": hashes["sha512"],
            "hashesMissing": len(hashes["missing"]),
            "hashesInvalid": len(hashes["invalid"]),
            "duplicateBinaries": len(duplicates),
            "downloadsFailing": len(downloads["failing"]),
            "provenanceOfficial": provenance["official"],
            "provenanceCommunity": provenance["community"],
            "provenanceUnknown": len(provenance["unknown"]),
        },
        "hashes": hashes,
        "duplicateBinaries": duplicates,
        "downloads": downloads,
        "provenance": provenance,
        "findings": findings,
    }
