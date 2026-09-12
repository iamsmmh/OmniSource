"""Tests for the download-link health checker's issue lifecycle."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_SPEC = importlib.util.spec_from_file_location("health_check", _ROOT / "scripts" / "health_check.py")
assert _SPEC and _SPEC.loader, "cannot load scripts/health_check.py"
HEALTH = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(HEALTH)


class FakeSubprocess:
    """Minimal stand-in for the subprocess module used by the checker."""

    def __init__(self, *, list_stdout: str = "") -> None:
        self.list_stdout = list_stdout
        self.calls: list[list[str]] = []

    def run(self, argv, **_kwargs):
        self.calls.append(list(argv))
        if "list" in argv:
            return SimpleNamespace(stdout=self.list_stdout, returncode=0, stderr="")
        return SimpleNamespace(stdout="", returncode=0, stderr="")


def _patch(fake: FakeSubprocess):
    return (
        mock.patch.object(HEALTH, "subprocess", fake),
        mock.patch.object(HEALTH.shutil, "which", return_value="/usr/bin/gh"),
        mock.patch.dict(HEALTH.os.environ, {"GH_TOKEN": "token"}, clear=False),
    )


class IssueLifecycleTests(unittest.TestCase):
    def _run(self, fake: FakeSubprocess, action) -> None:
        patches = _patch(fake)
        with patches[0], patches[1], patches[2], contextlib.redirect_stdout(io.StringIO()):
            action()

    def test_resolve_closes_every_open_issue(self) -> None:
        fake = FakeSubprocess(list_stdout="12\n13\n")
        self._run(fake, lambda: HEALTH.resolve_issues("recovered", repo="o/r", label="broken-link"))
        closes = [call for call in fake.calls if call[1:3] == ["issue", "close"]]
        self.assertEqual(len(closes), 2)
        for call in closes:
            self.assertEqual(call[:3], ["/usr/bin/gh", "issue", "close"])
            self.assertIn("--reason", call)
        comments = [call for call in fake.calls if call[1:3] == ["issue", "comment"]]
        self.assertEqual(len(comments), 2)

    def test_resolve_is_silent_without_open_issues(self) -> None:
        fake = FakeSubprocess(list_stdout="\n")
        self._run(fake, lambda: HEALTH.resolve_issues("recovered", repo="o/r", label="broken-link"))
        self.assertEqual([call for call in fake.calls if call[1:3] == ["issue", "close"]], [])

    def test_broken_links_append_to_the_open_issue(self) -> None:
        fake = FakeSubprocess(list_stdout="7\n")
        self._run(fake, lambda: HEALTH.report_issue("broken", repo="o/r", label="broken-link", title="t"))
        self.assertEqual(next(call for call in fake.calls if call[1:3] == ["issue", "comment"])[5], "7")
        self.assertEqual([call for call in fake.calls if call[1:3] == ["issue", "create"]], [])

    def test_first_failure_creates_the_issue_with_the_label(self) -> None:
        fake = FakeSubprocess(list_stdout="")
        self._run(fake, lambda: HEALTH.report_issue("broken", repo="o/r", label="broken-link", title="t"))
        creates = [call for call in fake.calls if call[1:3] == ["issue", "create"]]
        self.assertEqual(len(creates), 1)
        self.assertIn("--label", creates[0])

    def test_green_run_closes_the_tracker(self) -> None:
        fake = FakeSubprocess(list_stdout="9\n")
        targets = [{"app": "Demo", "kind": "primary", "url": "https://example.com/demo.ipa"}]
        with (
            mock.patch.object(HEALTH, "iter_targets", return_value=targets),
            mock.patch.object(HEALTH, "probe_url", return_value=(True, "HTTP 200")),
        ):
            self._run(
                fake,
                lambda: self.assertEqual(
                    HEALTH.main(["--report-issue", "--repo", "o/r"]),
                    0,
                ),
            )
        self.assertTrue([call for call in fake.calls if call[1:3] == ["issue", "close"]])
