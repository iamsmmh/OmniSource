from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from omnisource.repository import JsonRepository, MemoryRepository, SQLiteRepository


class RepositoryTransactionTests(unittest.TestCase):
    def test_memory_rolls_back_batch(self) -> None:
        repo = MemoryRepository()
        with self.assertRaises(RuntimeError):
            with repo.transaction():
                repo.put("apps", "one", {"name": "One"})
                repo.put("apps", "two", {"name": "Two"})
                raise RuntimeError("abort")
        self.assertEqual(repo.count("apps"), 0)

    def test_json_rolls_back_disk_and_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = JsonRepository(root)
            repo.put("apps", "one", {"name": "Before"})
            before = (root / "apps.json").read_text(encoding="utf-8")
            with self.assertRaises(RuntimeError):
                with repo.transaction():
                    repo.put("apps", "one", {"name": "After"})
                    repo.put("sources", "source", {"name": "New"})
                    raise RuntimeError("abort")
            self.assertEqual((root / "apps.json").read_text(encoding="utf-8"), before)
            self.assertFalse((root / "sources.json").exists())
            self.assertEqual(repo.get("apps", "one"), {"name": "Before"})

    def test_json_commits_multiple_collections_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = JsonRepository(Path(directory))
            with repo.transaction():
                repo.put("apps", "one", {"name": "One"})
                repo.put("sources", "source", {"name": "Source"})
            self.assertEqual(repo.get("apps", "one"), {"name": "One"})
            self.assertEqual(repo.get("sources", "source"), {"name": "Source"})

    def test_sqlite_rolls_back_without_inner_commit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteRepository(Path(directory) / "repo.sqlite")
            try:
                repo.put("apps", "one", {"name": "Before"})
                with self.assertRaises(RuntimeError):
                    with repo.transaction():
                        repo.put("apps", "one", {"name": "After"})
                        repo.put("sources", "source", {"name": "New"})
                        raise RuntimeError("abort")
                self.assertEqual(repo.get("apps", "one"), {"name": "Before"})
                self.assertIsNone(repo.get("sources", "source"))
            finally:
                repo.close()

    def test_sqlite_commits_multiple_operations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteRepository(Path(directory) / "repo.sqlite")
            try:
                with repo.transaction():
                    repo.put("apps", "one", {"name": "One"})
                    repo.put("apps", "two", {"name": "Two"})
                    repo.delete("apps", "one")
                self.assertEqual(repo.list("apps"), [{"name": "Two"}])
            finally:
                repo.close()


if __name__ == "__main__":
    unittest.main()
