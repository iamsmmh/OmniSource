"""Tests for the Phase 3/6/7/8/9/10 intelligence modules."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import unittest

from omnisource.collections import build_collection_pages, build_collections_doc
from omnisource.compare import build_compare_pages, render_compare_page, render_compare_redirect
from omnisource.dead_apps import (
    build_dead_apps_doc,
    classify_age,
    prune_superseded_removals,
    release_change,
)
from omnisource.domain import App, Catalog
from omnisource.duplicates import master_feed_selection
from omnisource.health_score import annotate_health_doc, build_health_scores, compute_health_score
from omnisource.integrity import (
    build_integrity_doc,
    integrity_errors,
    metadata_checks,
    select_verification_targets,
    verification_due,
)
from omnisource.verification import compute_trust_score, trust_badge


def _app(slug: str = "demo", **extra) -> App:
    raw = {
        "slug": slug,
        "name": f"App {slug.title()}",
        "bundleIdentifier": f"com.example.{slug}",
        "developerName": "Dev",
        "icon": "Icon.png",
        "category": "utilities",
        "status": "stable",
        "localizedDescription": "A description.",
        "shortDescription": "Short.",
        "compatibility": {"minOSVersion": "16.0", "clients": ["altstore"]},
        "verification": {"publisher": "Dev", "verified": True},
        **extra,
    }
    return App(slug=slug, raw=raw)


def _catalog(*apps: App) -> Catalog:
    return Catalog(source={"baseURL": "https://example.com"}, clients=[], apps=list(apps))


GOOD_NEWEST = {
    "version": "1.0.0",
    "date": "2026-09-01",
    "downloadURL": "https://example.com/app.ipa",
    "size": 1000,
    "sha256": "a" * 64,
    "source": "github",
}


class IntegrityTests(unittest.TestCase):
    def test_good_asset_passes(self) -> None:
        result = metadata_checks(_app(), dict(GOOD_NEWEST), {"downloadReachable": True})
        self.assertEqual(result["status"], "pass")
        self.assertTrue(all(result["checks"].values()))

    def test_zero_bytes_fails(self) -> None:
        newest = dict(GOOD_NEWEST, size=0)
        result = metadata_checks(_app(), newest, None)
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["checks"]["sizePositive"])

    def test_non_ipa_fails(self) -> None:
        newest = dict(GOOD_NEWEST, downloadURL="https://example.com/app.zip")
        result = metadata_checks(_app(), newest, None)
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["checks"]["installable"])

    def test_bad_digest_fails(self) -> None:
        newest = dict(GOOD_NEWEST, sha256="not-a-hex")
        result = metadata_checks(_app(), newest, None)
        self.assertEqual(result["status"], "fail")
        self.assertFalse(result["checks"]["digestFormat"])

    def test_missing_sha_is_warn(self) -> None:
        newest = dict(GOOD_NEWEST)
        newest.pop("sha256")
        result = metadata_checks(_app(), newest, None)
        self.assertEqual(result["status"], "warn")

    def test_build_doc_and_errors(self) -> None:
        catalog = _catalog(_app("demo"), _app("broken", **{"bundleIdentifier": "com.example.broken"}))
        state = {
            "demo": {"versions": [dict(GOOD_NEWEST)]},
            "broken": {"versions": [dict(GOOD_NEWEST, size=0)]},
        }
        doc = build_integrity_doc(catalog, state, {})
        self.assertEqual(doc["totals"]["fail"], 1)
        self.assertEqual(doc["totals"]["rejected"], 1)
        errors = integrity_errors(doc)
        self.assertEqual(len(errors), 1)
        self.assertIn("broken", errors[0])
        # Failing entries are sorted first.
        self.assertEqual(doc["apps"][0]["slug"], "broken")
        self.assertEqual(doc["apps"][0]["asset"]["releaseId"], "1.0.0")
        self.assertEqual(doc["apps"][0]["asset"]["source"], "github")


class HealthScoreTests(unittest.TestCase):
    def test_weights_and_status(self) -> None:
        app = _app()
        state = {
            "demo": {
                "versions": [
                    {"version": "1.0.0", "date": "2026-09-01"},
                    {"version": "0.9.0", "date": "2026-08-25"},
                ],
                "healthHistory": [{"date": "2026-09-05", "reachable": True, "latencyMs": 80}],
            }
        }
        result = compute_health_score(app, state, reachable_now=True)
        # All components near-perfect except metadata completeness -> high score.
        self.assertGreaterEqual(result["health_score"], 70)
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["weights"]["downloadSuccess"], 0.30)
        # Weights sum to 1.0 and every breakdown component is bounded 0..1.
        self.assertAlmostEqual(sum(result["weights"].values()), 1.0, places=6)
        for value in result["breakdown"].values():
            self.assertGreaterEqual(value, 0.0)
            self.assertLessEqual(value, 1.0)

    def test_unreachable_is_lower(self) -> None:
        app = _app()
        result = compute_health_score(app, {}, reachable_now=False)
        self.assertEqual(result["status"] in {"warning", "critical"}, True)
        self.assertLess(result["health_score"], 70)

    def test_archived_status(self) -> None:
        app = _app(status="deprecated")
        result = compute_health_score(app, {}, reachable_now=True)
        self.assertEqual(result["status"], "archived")

    def test_annotate(self) -> None:
        catalog = _catalog(_app())
        state = {"demo": {"versions": [dict(GOOD_NEWEST)]}}
        health_doc = {"apps": [{"slug": "demo", "downloadReachable": True}], "totals": {}}
        scores = build_health_scores(catalog, state, health_doc, {})
        annotate_health_doc(health_doc, scores)
        item = health_doc["apps"][0]
        self.assertIn("healthScore", item)
        self.assertIn("healthStatus", item)
        self.assertEqual(health_doc["totals"]["healthy"], 1)


class TrustScoreTests(unittest.TestCase):
    def test_badge_thresholds(self) -> None:
        self.assertEqual(trust_badge(9.5), "Verified")
        self.assertEqual(trust_badge(8.0), "Trusted")
        self.assertEqual(trust_badge(5.0), "Community")
        self.assertEqual(trust_badge(4.9), "Experimental")

    def test_max_score(self) -> None:
        score, badge = compute_trust_score(
            level="VERIFIED", release_count=3, consistency=1.0, uptime=1.0, hash_verified=True
        )
        self.assertEqual(score, 10.0)
        self.assertEqual(badge, "Verified")

    def test_min_score(self) -> None:
        score, badge = compute_trust_score(
            level="UNVERIFIED", release_count=0, consistency=0.0, uptime=0.0, hash_verified=False
        )
        self.assertEqual(score, 1.0)
        self.assertEqual(badge, "Experimental")


class DeadAppsTests(unittest.TestCase):
    def test_age_thresholds(self) -> None:
        self.assertEqual(classify_age(30), "healthy")
        self.assertEqual(classify_age(90), "warning")
        self.assertEqual(classify_age(180), "stale")
        self.assertEqual(classify_age(365), "archived")

    def test_rolled_back_release_is_critical(self) -> None:
        """A real takedown: upstream rolled back below the removed version."""
        app = _app()
        state = {
            "demo": {
                "versions": [{"version": "0.9", "date": "2026-09-01"}],
                "removedReleases": [{"version": "1.0", "at": "2026-09-02"}],
            }
        }
        doc = build_dead_apps_doc(_catalog(app), state, today_iso="2026-09-10")
        entry = doc["apps"][0]
        self.assertEqual(entry["classification"], "critical")
        self.assertEqual(doc["summary"]["critical"], 1)
        self.assertEqual(entry["removedReleases"], 1)

    def test_removal_with_no_current_release_is_critical(self) -> None:
        app = _app()
        state = {"demo": {"versions": [], "removedReleases": [{"version": "1.0", "at": "2026-09-02"}]}}
        doc = build_dead_apps_doc(_catalog(app), state, today_iso="2026-09-10")
        self.assertEqual(doc["apps"][0]["classification"], "critical")

    def test_superseded_release_is_not_critical(self) -> None:
        """A version bump is not a takedown (ISSUES-REPORT.md #2)."""
        app = _app()
        state = {
            "demo": {
                "versions": [{"version": "1.1", "date": "2026-09-09"}],
                "removedReleases": [{"version": "1.0", "at": "2026-09-02"}],
            }
        }
        doc = build_dead_apps_doc(_catalog(app), state, today_iso="2026-09-10")
        entry = doc["apps"][0]
        self.assertEqual(entry["classification"], "healthy")
        self.assertEqual(entry["removedReleases"], 0)
        self.assertEqual(doc["summary"]["critical"], 0)

    def test_same_version_asset_swap_is_not_critical(self) -> None:
        """A provider failover keeps the version and only renames the asset."""
        app = _app()
        state = {
            "demo": {
                "versions": [{"version": "12.9.2", "date": "2026-09-05"}],
                "removedReleases": [{"version": "12.9.2", "at": "2026-09-06"}],
                "supersededReleases": [
                    {"kind": "replaced", "version": "12.9.2", "at": "2026-09-06", "reason": "new URL"}
                ],
            }
        }
        doc = build_dead_apps_doc(_catalog(app), state, today_iso="2026-09-10")
        entry = doc["apps"][0]
        self.assertEqual(entry["classification"], "healthy")
        self.assertEqual(entry["replacedReleases"], 1)
        self.assertTrue(any("republished in place" in reason for reason in entry["reasons"]))

    def test_release_change_classification(self) -> None:
        previous = {"version": "1.0", "downloadURL": "https://example.com/1.0.ipa"}
        # Unchanged release re-synced.
        self.assertIsNone(release_change(previous, [previous]))
        # Ordinary bump.
        change = release_change(previous, [{"version": "1.1", "downloadURL": "https://example.com/1.1.ipa"}])
        self.assertEqual(change["kind"], "superseded")
        # Same version, new URL (failover / republished build).
        change = release_change(previous, [{"version": "1.0", "downloadURL": "https://example.com/other.ipa"}])
        self.assertEqual(change["kind"], "replaced")
        # Rollback.
        change = release_change(previous, [{"version": "0.9", "downloadURL": "https://example.com/0.9.ipa"}])
        self.assertEqual(change["kind"], "removed")
        # Nothing published any more.
        change = release_change(previous, [])
        self.assertEqual(change["kind"], "removed")

    def test_prune_superseded_removals_self_heals_state(self) -> None:
        state = {
            "demo": {
                "versions": [{"version": "1.1", "date": "2026-09-09"}],
                "removedReleases": [{"version": "1.0", "at": "2026-09-02"}],
            },
            "rolled-back": {
                "versions": [{"version": "0.9", "date": "2026-09-09"}],
                "removedReleases": [{"version": "1.0", "at": "2026-09-02"}],
            },
        }
        self.assertEqual(prune_superseded_removals(state), 1)
        self.assertNotIn("removedReleases", state["demo"])
        self.assertEqual(state["demo"]["supersededReleases"][0]["version"], "1.0")
        self.assertIn("removedReleases", state["rolled-back"])

    def test_fresh_app_is_healthy(self) -> None:
        app = _app()
        state = {"demo": {"versions": [{"version": "1.0", "date": "2026-09-08"}]}}
        doc = build_dead_apps_doc(_catalog(app), state, today_iso="2026-09-10")
        self.assertEqual(doc["count"], 0)
        self.assertEqual(doc["apps"][0]["classification"], "healthy")


class CollectionsTests(unittest.TestCase):
    def test_build_doc_shape(self) -> None:
        catalog = _catalog(_app("ytlite"), _app("utm"))
        doc = build_collections_doc(catalog, {})
        self.assertEqual(doc["count"], 5)
        slugs = {c["slug"] for c in doc["collections"]}
        self.assertEqual(slugs, {"youtube", "music", "emulators", "utilities", "productivity"})
        # Only apps present in the catalog are referenced.
        for collection in doc["collections"]:
            for slug in collection["appSlugs"]:
                self.assertIn(slug, {"ytlite", "utm"})

    def test_pages_generated(self) -> None:
        import tempfile

        catalog = _catalog(_app("utm"))
        with tempfile.TemporaryDirectory() as tmp:
            changed = build_collection_pages(catalog, {}, pages_dir=Path(tmp))
            names = {p.parent.name for p in changed}
            self.assertEqual(len(changed), 5)
            self.assertIn("emulators", names)
            content = (Path(tmp) / "emulators" / "index.html").read_text(encoding="utf-8")
            self.assertIn("App Utm", content)


class ComparePageTests(unittest.TestCase):
    def test_both_orders_generated(self) -> None:
        import tempfile

        catalog = _catalog(_app("aaa"), _app("bbb"))
        health_doc = {"apps": [{"slug": "aaa", "downloadReachable": True}, {"slug": "bbb", "downloadReachable": True}]}
        verification_doc = {
            "apps": [
                {"app": "aaa", "status": "VERIFIED", "trustScore": 9.0, "trustBadge": "Verified"},
                {"app": "bbb", "status": "UNVERIFIED", "trustScore": 1.0, "trustBadge": "Experimental"},
            ]
        }
        state = {
            "aaa": {"versions": [dict(GOOD_NEWEST, version="1.0")]},
            "bbb": {"versions": [dict(GOOD_NEWEST, version="2.0", size=2000)]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            changed = build_compare_pages(catalog, state, health_doc, verification_doc, pages_dir=Path(tmp))
            # One unordered pair -> 1 canonical page + 1 reverse-order stub.
            self.assertEqual(len(changed), 2)
            canonical = (Path(tmp) / "aaa-vs-bbb" / "index.html").read_text(encoding="utf-8")
            self.assertIn("App Aaa vs App Bbb", canonical)
            self.assertIn("Trust score", canonical)
            stub = (Path(tmp) / "bbb-vs-aaa" / "index.html").read_text(encoding="utf-8")
            self.assertIn('http-equiv="refresh"', stub)
            self.assertIn("aaa-vs-bbb", stub)

    def test_redirect_helper(self) -> None:
        page = render_compare_redirect("../../compare/a-vs-b/")
        self.assertIn("../../compare/a-vs-b/", page)

    def test_render_page_escaping(self) -> None:
        left = {
            "slug": "a",
            "name": "A <b>",
            "icon": "../../assets/i.png",
            "category": "other",
            "developer": "d",
            "version": "1",
            "releaseDate": "",
            "sizeBytes": 0,
            "updateFrequencyDays": 0.0,
            "verificationLevel": "UNVERIFIED",
            "trustScore": 1.0,
            "trustBadge": "Experimental",
            "healthScore": 10,
            "healthStatus": "critical",
            "features": 'x"y',
            "detailURL": "../../apps/a/",
        }
        right = dict(left, slug="b", name="B")
        page = render_compare_page(catalog=_catalog(_app("a")), left=left, right=right, base_url="https://x.dev")
        self.assertIn("&lt;b&gt;", page)
        self.assertIn("Trust score", page)


if __name__ == "__main__":
    unittest.main()


class IntegritySelectionTests(unittest.TestCase):
    """The weekly full-verification job must stay affordable (issues #3/#4)."""

    def _newest(self, **extra):
        newest = {"version": "1.0", "downloadURL": "https://example.com/app.ipa", "size": 100}
        newest.update(extra)
        return newest

    def test_never_verified_is_due_first(self) -> None:
        due, priority, reason = verification_due({}, self._newest(), stale_days=30)
        self.assertTrue(due)
        self.assertEqual(priority, 0)
        self.assertEqual(reason, "never verified")

    def test_failed_attempt_is_retried(self) -> None:
        state = {"lastFullVerification": {"at": "2026-09-11", "ok": False, "version": "1.0"}}
        due, priority, _reason = verification_due(state, self._newest(), stale_days=30)
        self.assertTrue(due)
        self.assertEqual(priority, 0)

    def test_fresh_records_are_skipped(self) -> None:
        state = {
            "lastFullVerification": {
                "at": "2026-09-10",
                "ok": True,
                "version": "1.0",
                "size": 100,
                "sha256": "a" * 64,
            }
        }
        due, priority, _reason = verification_due(
            state, self._newest(sha256="a" * 64), stale_days=30, today_iso="2026-09-12"
        )
        self.assertFalse(due)
        self.assertEqual(priority, 3)

    def test_changed_asset_is_due_before_aged_records(self) -> None:
        state = {"lastFullVerification": {"at": "2026-09-10", "ok": True, "version": "0.9"}}
        due, priority, reason = verification_due(state, self._newest(), stale_days=30, today_iso="2026-09-12")
        self.assertTrue(due)
        self.assertEqual(priority, 1)
        self.assertIn("asset changed", reason)

    def test_size_change_is_due(self) -> None:
        state = {"lastFullVerification": {"at": "2026-09-10", "ok": True, "version": "1.0", "size": 55}}
        due, priority, _reason = verification_due(state, self._newest(), stale_days=30, today_iso="2026-09-12")
        self.assertTrue(due)
        self.assertEqual(priority, 1)

    def test_aged_record_is_due(self) -> None:
        state = {"lastFullVerification": {"at": "2026-08-01", "ok": True, "version": "1.0", "size": 100}}
        due, priority, _reason = verification_due(state, self._newest(), stale_days=30, today_iso="2026-09-12")
        self.assertTrue(due)
        self.assertEqual(priority, 2)

    def test_disabled_stale_window_verifies_everything(self) -> None:
        state = {"lastFullVerification": {"at": "2026-09-11", "ok": True, "version": "1.0", "size": 100}}
        due, priority, reason = verification_due(state, self._newest(), stale_days=None, today_iso="2026-09-12")
        self.assertTrue(due)
        self.assertEqual(priority, 2)
        self.assertEqual(reason, "stale window disabled")

    def test_select_targets_orders_and_caps(self) -> None:
        catalog = _catalog(_app("fresh"), _app("changed"), _app("never"))
        state = {
            "fresh": {
                "versions": [{"version": "1.0", "date": "2026-09-01", "downloadURL": "https://example.com/f.ipa"}],
                "lastFullVerification": {"at": "2026-09-11", "ok": True, "version": "1.0", "size": 0},
            },
            "changed": {
                "versions": [{"version": "2.0", "date": "2026-09-01", "downloadURL": "https://example.com/c.ipa"}],
                "lastFullVerification": {"at": "2026-09-11", "ok": True, "version": "1.0"},
            },
            "never": {
                "versions": [{"version": "1.0", "date": "2026-09-01", "downloadURL": "https://example.com/n.ipa"}],
            },
        }
        targets = select_verification_targets(catalog, state, stale_days=30, today_iso="2026-09-12")
        # "fresh" was verified yesterday, so it is inside the stale window and
        # not re-downloaded; never-verified ranks above a changed asset.
        self.assertEqual([slug for slug, _reason in targets], ["never", "changed"])
        limited = select_verification_targets(catalog, state, stale_days=30, limit=1, today_iso="2026-09-12")
        self.assertEqual(len(limited), 1)
        self.assertEqual(limited[0][0], "never")

    def test_select_targets_ignores_apps_without_downloads(self) -> None:
        catalog = _catalog(_app("empty"))
        self.assertEqual(select_verification_targets(catalog, {"empty": {"versions": []}}, stale_days=30), [])


class MasterFeedTests(unittest.TestCase):
    """One master source cannot carry two apps with the same bundle ID (#7)."""

    def test_collision_group_keeps_only_the_recommendation(self) -> None:
        catalog = _catalog(
            _app("yt-a", bundleIdentifier="com.google.ios.youtube"),
            _app("yt-b", bundleIdentifier="com.google.ios.youtube"),
            _app("solo", bundleIdentifier="com.example.solo"),
        )
        duplicates = {
            "groups": [
                {
                    "key": "com.google.ios.youtube",
                    "type": "bundle-id",
                    "replacementRisk": True,
                    "apps": [{"app": "yt-a"}, {"app": "yt-b"}],
                    "recommended": {"app": "yt-b"},
                }
            ]
        }
        excluded = master_feed_selection(catalog, duplicates)
        self.assertEqual(excluded, {"yt-a": "com.google.ios.youtube"})

    def test_name_only_groups_are_not_excluded(self) -> None:
        catalog = _catalog(_app("one"), _app("two"))
        duplicates = {
            "groups": [
                {
                    "key": "one | two",
                    "type": "unknown",
                    "replacementRisk": False,
                    "apps": [{"app": "one"}, {"app": "two"}],
                    "recommended": {"app": "two"},
                }
            ]
        }
        self.assertEqual(master_feed_selection(catalog, duplicates), {})

    def test_catalog_can_pin_membership(self) -> None:
        catalog = _catalog(
            _app("yt-a", bundleIdentifier="com.google.ios.youtube", masterFeed=True),
            _app("yt-b", bundleIdentifier="com.google.ios.youtube"),
            _app("yt-c", bundleIdentifier="com.google.ios.youtube", masterFeed=False),
        )
        duplicates = {
            "groups": [
                {
                    "key": "com.google.ios.youtube",
                    "type": "bundle-id",
                    "replacementRisk": True,
                    "apps": [{"app": "yt-a"}, {"app": "yt-b"}, {"app": "yt-c"}],
                    "recommended": {"app": "yt-b"},
                }
            ]
        }
        excluded = master_feed_selection(catalog, duplicates)
        self.assertEqual(set(excluded), {"yt-b", "yt-c"})


class FullVerificationTests(unittest.TestCase):
    """The download path behind verify.yml must record, not crash (issue #3)."""

    SHA = "b" * 64

    def _container(self) -> Any:
        from types import SimpleNamespace

        return SimpleNamespace(settings=SimpleNamespace(health_timeout=10.0), http=object())

    def _state(self) -> dict[str, Any]:
        return {
            "demo": {
                "versions": [
                    {
                        "version": "1.0",
                        "date": "2026-09-01",
                        "downloadURL": "https://example.com/Demo.ipa",
                        "size": 7,
                        "sha256": self.SHA,
                    }
                ]
            }
        }

    def test_success_records_size_and_digest(self) -> None:
        from unittest import mock

        from omnisource import integrity as integrity_module

        state = self._state()
        catalog = _catalog(_app("demo"))
        with mock.patch.object(integrity_module, "stream_sha256", return_value=(7, self.SHA)):
            records = integrity_module.verify_downloads(self._container(), catalog, state, only={"demo"}, workers=1)
        self.assertTrue(records[0]["ok"])
        record = state["demo"]["lastFullVerification"]
        self.assertEqual(record["sha256"], self.SHA)
        self.assertEqual(record["size"], 7)
        self.assertNotIn("slug", record)
        self.assertNotIn("url", record)

    def test_hash_mismatch_is_a_failure(self) -> None:
        from unittest import mock

        from omnisource import integrity as integrity_module

        state = self._state()
        catalog = _catalog(_app("demo"))
        with mock.patch.object(integrity_module, "stream_sha256", return_value=(7, "c" * 64)):
            records = integrity_module.verify_downloads(self._container(), catalog, state, only={"demo"}, workers=1)
        self.assertFalse(records[0]["ok"])
        self.assertIn("hash mismatch", records[0]["detail"])
        self.assertFalse(state["demo"]["lastFullVerification"]["ok"])

    def test_transport_failure_is_a_result_not_an_exception(self) -> None:
        from unittest import mock

        from omnisource import integrity as integrity_module

        state = self._state()
        catalog = _catalog(_app("demo"))
        with mock.patch.object(integrity_module, "stream_sha256", side_effect=OSError("connection reset")):
            records = integrity_module.verify_downloads(self._container(), catalog, state, only={"demo"}, workers=1)
        self.assertFalse(records[0]["ok"])
        self.assertIn("corrupted download", records[0]["detail"])
        self.assertFalse(state["demo"]["lastFullVerification"]["ok"])
