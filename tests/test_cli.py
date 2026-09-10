"""Tests for the OmniSource command-line interface."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from omnisource import __version__
from omnisource.cli import main, parse_args
from omnisource.errors import SyncError


class CLIParseTests(unittest.TestCase):
    def test_version_flag_is_recognized(self):
        args = parse_args(["--version"])
        self.assertTrue(args.version)

    def test_version_flag_short_circuits_before_logging(self):
        with redirect_stdout(io.StringIO()) as out:
            code = main(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue().strip(), __version__)


class CLIRunTests(unittest.TestCase):
    def test_sync_error_returns_failure_code(self):
        with (
            mock.patch("omnisource.cli.run", side_effect=SyncError("boom")),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            code = main([])
        self.assertEqual(code, 1)

    def test_keyboard_interrupt_returns_130(self):
        with (
            mock.patch("omnisource.cli.run", side_effect=KeyboardInterrupt),
            redirect_stdout(io.StringIO()),
            redirect_stderr(io.StringIO()),
        ):
            code = main([])
        self.assertEqual(code, 130)


if __name__ == "__main__":
    unittest.main()
