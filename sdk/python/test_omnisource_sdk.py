"""Smoke tests for the OmniSource Python SDK.

The tests are offline-friendly: they read the generated ``feeds/``
directory and use it as the fake transport. CI runs this file in a sandbox
that has just executed the OmniSource pipeline.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Make the SDK importable without installing it.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from omnisource_sdk import OmniSource, OmniSourceError  # noqa: E402

# The SDK lives under sdk/python/ inside the repository.
REPO = HERE.parent.parent
FEEDS = REPO / "feeds"


def main() -> int:
    if not FEEDS.is_dir():
        print("SKIP: feeds/ directory not found; run scripts/omnisource.py first.")
        return 0

    fixtures: dict[str, object] = {}
    for path in sorted(FEEDS.glob("*.json")):
        try:
            fixtures[f"/feeds/{path.name}"] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    # The /discovery.json endpoint is published both at the root and in
    # feeds/. The Pages builder copies the canonical copy to the root.
    for candidate in (REPO / "discovery.json", FEEDS / "discovery.json"):
        if candidate.is_file():
            try:
                fixtures["/discovery.json"] = json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
            break

    def fake_fetch(url: str, *, timeout: float):
        # Match the SDK's expected protocol: returns a 4-tuple-like object.
        from omnisource_sdk import _Response
        # Strip the base URL prefix to recover the in-app path. The SDK
        # builds ``f"{base_url}/{path}"`` so the path starts after the
        # host. We strip the known base_url prefix to recover the
        # canonical key.
        base = client.base_url
        if url.startswith(base):
            path = url[len(base):]
        else:
            # Fallback: split on the first "://" + host.
            scheme_sep = url.find("://")
            after_scheme = url[scheme_sep + 3:] if scheme_sep != -1 else url
            slash = after_scheme.find("/")
            path = after_scheme[slash:] if slash != -1 else "/"
        if not path.startswith("/"):
            path = "/" + path
        if path in fixtures:
            body = json.dumps(fixtures[path])
            return _Response(ok=True, status=200, body=body, payload=fixtures[path])
        return _Response(ok=False, status=404, body="not found", payload=None)

    client = OmniSource(base_url="https://example.test/OmniSource", fetch=fake_fetch)

    cases = [
        ("search returns at least one hit for a common term", lambda: len(client.search("youtube")) > 0),
        ("get_app returns a known slug", lambda: client.get_app("uyouenhanced") is not None),
        ("get_trending has a board", lambda: isinstance(client.get_trending().get("trending"), list)),
        ("get_related is a list", lambda: isinstance(client.get_related("uyouenhanced"), list)),
        ("get_reputation has sources", lambda: isinstance(client.get_reputation().get("sources"), list)),
        ("get_health has a summary", lambda: isinstance(client.get_health().get("summary"), dict)),
        ("get_analytics has totals", lambda: isinstance(client.get_analytics().get("totals"), dict)),
        ("get_community has popular", lambda: isinstance(client.get_community().get("popular"), list)),
        ("get_install without slug returns master", lambda: isinstance(client.get_install(), dict)),
        ("get_install with slug returns a list", lambda: isinstance(client.get_install("uyouenhanced"), list)),
        ("get_search_index has documents", lambda: isinstance(client.get_search_index().get("documents"), list)),
    ]

    passed = failed = 0
    for name, fn in cases:
        try:
            ok = fn()
            if not ok:
                raise AssertionError("returned falsy")
            print(f"  ok  {name}")
            passed += 1
        except Exception as error:  # noqa: BLE001
            print(f"  fail {name}: {error}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
