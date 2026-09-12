#!/usr/bin/env python3
"""Verify quarantined discovery candidates and optionally publish them.

This is the explicit boundary after structural discovery validation:

    discovered -> validating -> quarantined/verified -> published

Only a verified HTTPS feed whose remote envelope and app metadata pass the
remote validators can be published. Repository pages and release pages are
useful discovery evidence, but they are not feed publication inputs until a
feed URL is discovered and verified. The output is a source registry input;
it never writes ``catalog.json`` or a client feed directly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from omnisource import autodiscovery
from omnisource.io import read_json, write_json_stable
from omnisource.quarantine import (
    DISCOVERED,
    PUBLISHED,
    QUARANTINED,
    VALIDATING,
    VERIFIED,
    QuarantineStore,
    can_publish,
)
from omnisource.remote_validation import validate_remote_feed

ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--store", default=str(ROOT / "data" / "discovered_sources.json"))
    parser.add_argument("--quarantine", default=str(ROOT / "data" / "quarantine"))
    parser.add_argument("--published", default=str(ROOT / "data" / "published_sources.json"))
    parser.add_argument("--source-id", action="append", default=[], help="verify only this source ID (repeatable)")
    parser.add_argument("--limit", type=int, default=0, help="maximum candidates to inspect; zero means all")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--max-bytes", type=int, default=4_000_000)
    parser.add_argument("--publish", action="store_true", help="promote verified records to PUBLISHED")
    parser.add_argument("--recheck-verified", action="store_true", help="fetch already verified records again")
    parser.add_argument("--dry-run", action="store_true", help="perform checks without writing any output")
    return parser.parse_args(argv)


def _records(path: Path) -> list[dict[str, Any]]:
    document = read_json(path)
    if not isinstance(document, dict) or not isinstance(document.get("sources"), list):
        return []
    return [item for item in document["sources"] if isinstance(item, dict)]


def _source_url(record: dict[str, Any]) -> str:
    return str(record.get("source_url") or record.get("sourceUrl") or record.get("url") or "")


def _transition_or_put(
    store: QuarantineStore,
    record: dict[str, Any],
    status: str,
    *,
    errors: list[str] | None = None,
    **updates: Any,
) -> dict[str, Any]:
    source_id = str(record.get("source_id") or "")
    current = store.get(source_id)
    if current is None:
        return store.put({**record, **updates}, status=status, errors=errors or [])
    return store.transition(source_id, status, errors=errors or [], **updates)


def _fail(store: QuarantineStore, record: dict[str, Any], errors: list[str], *, dry_run: bool) -> dict[str, Any]:
    if dry_run:
        return {**record, "status": QUARANTINED, "errors": errors}
    current = store.get(str(record.get("source_id") or ""))
    if current is None:
        return store.put(record, status=QUARANTINED, errors=errors)
    # Every verification attempt begins in VALIDATING, so this transition is
    # legal for both a new candidate and a previously quarantined candidate.
    if current.get("status") == QUARANTINED:
        store.transition(str(record["source_id"]), VALIDATING, errors=[])
    return store.transition(str(record["source_id"]), QUARANTINED, errors=errors, verification_status="unverified")


def _verify_one(record: dict[str, Any], store: QuarantineStore, args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    source_id = str(record.get("source_id") or "")
    url = _source_url(record)
    current = store.get(source_id) if not args.dry_run else None
    if args.publish and not args.recheck_verified and current and current.get("status") == VERIFIED:
        allowed, failures = can_publish(current)
        if allowed:
            if args.dry_run:
                return {**current, "status": PUBLISHED}, "published"
            return store.transition(source_id, PUBLISHED, published_at=autodiscovery.utcnow()), "published"
        result = _fail(store, current, failures, dry_run=args.dry_run)
        return result, "quarantined"
    if not urlsplit(url).path.lower().endswith(".json"):
        result = _fail(
            store,
            record,
            ["candidate is not a feed URL; repository/page evidence needs a feed URL before verification"],
            dry_run=args.dry_run,
        )
        return result, "quarantined"

    if not args.dry_run:
        if current is None:
            current = store.put(record, status=VALIDATING, errors=[])
        if current and current.get("status") in {QUARANTINED, VERIFIED, PUBLISHED}:
            if current.get("status") in {VERIFIED, PUBLISHED}:
                store.transition(source_id, QUARANTINED, errors=[])
            store.transition(source_id, VALIDATING, errors=[])
        elif current and current.get("status") == DISCOVERED:
            store.transition(source_id, VALIDATING, errors=[])

    try:
        payload = autodiscovery.fetch_json(url, timeout=max(1, args.timeout), max_bytes=max(1, args.max_bytes))
    except Exception as exc:  # provider errors are a quarantine finding, not a crash
        result = _fail(store, record, [f"feed fetch failed: {exc}"], dry_run=args.dry_run)
        return result, "quarantined"

    errors = validate_remote_feed(payload, url=url)
    if errors:
        result = _fail(store, record, errors, dry_run=args.dry_run)
        return result, "quarantined"

    payload_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    updates = {
        "verification_status": "verified",
        "health": "online",
        "health_status": "online",
        "verified_at": autodiscovery.utcnow(),
        "feed_sha256": hashlib.sha256(payload_bytes).hexdigest(),
        "app_count": len(payload.get("apps", [])) if isinstance(payload, dict) else 0,
        "errors": [],
    }
    if args.dry_run:
        verified = {**record, **updates, "status": VERIFIED}
    else:
        current = store.get(source_id)
        if (current and current.get("status") == QUARANTINED) or (current and current.get("status") == DISCOVERED):
            store.transition(source_id, VALIDATING, errors=[])
        verified = store.transition(source_id, VERIFIED, **updates)

    if args.publish:
        allowed, failures = can_publish(verified)
        if not allowed:
            result = _fail(store, verified, failures, dry_run=args.dry_run)
            return result, "quarantined"
        if args.dry_run:
            return {**verified, "status": PUBLISHED, "published_at": autodiscovery.utcnow()}, "published"
        published = store.transition(source_id, PUBLISHED, published_at=autodiscovery.utcnow())
        return published, "published"
    return verified, "verified"


def _write_outputs(records: list[dict[str, Any]], published_path: Path) -> None:
    publishable = [
        record
        for record in records
        if record.get("status") == PUBLISHED
        and record.get("verification_status") in {"verified", "trusted", "official"}
        and not record.get("errors")
    ]
    document = {
        "schemaVersion": 1,
        "generatedAt": autodiscovery.utcnow(),
        "count": len(publishable),
        "sources": sorted(publishable, key=lambda item: str(item.get("source_id", ""))),
    }
    write_json_stable(published_path, document)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.limit < 0:
        raise SystemExit("--limit must be non-negative")
    store_path = Path(args.store)
    quarantine = QuarantineStore(Path(args.quarantine))
    candidates = _records(store_path)
    selected_ids = {str(value) for value in args.source_id}
    candidates = [item for item in candidates if not selected_ids or str(item.get("source_id")) in selected_ids]
    if not args.recheck_verified:
        allowed_statuses = {DISCOVERED, VALIDATING, QUARANTINED}
        if args.publish:
            allowed_statuses.add(VERIFIED)
        candidates = [item for item in candidates if str(item.get("status") or VALIDATING) in allowed_statuses]
    if args.limit:
        candidates = candidates[: args.limit]

    counts = {"verified": 0, "published": 0, "quarantined": 0, "skipped": 0}
    by_id = {str(item.get("source_id")): dict(item) for item in _records(store_path)}
    for candidate in candidates:
        result, outcome = _verify_one(candidate, quarantine, args)
        counts[outcome] = counts.get(outcome, 0) + 1
        by_id[str(candidate.get("source_id"))] = result

    if not args.dry_run:
        current_quarantine = {str(item.get("source_id")): item for item in quarantine.load().get("sources", [])}
        for source_id, record in current_quarantine.items():
            if source_id in by_id:
                by_id[source_id] = record
        output_records = sorted(by_id.values(), key=lambda item: str(item.get("source_id", "")))
        # Keep the discovery registry auditable, but only the separate
        # published projection is consumed by registry/publication builders.
        write_json_stable(
            store_path,
            {
                "schemaVersion": 1,
                "generatedAt": autodiscovery.utcnow(),
                "count": len(output_records),
                "sources": output_records,
            },
        )
        _write_outputs(output_records, Path(args.published))

    print(
        "verification: "
        + ", ".join(f"{key}={value}" for key, value in counts.items())
        + (" (dry run)" if args.dry_run else f"; published projection={args.published}")
    )
    # Quarantine is an expected, fail-closed outcome for repository evidence,
    # dead feeds, and malformed upstreams. The validation/publication gates
    # remain successful because no quarantined record is published.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
