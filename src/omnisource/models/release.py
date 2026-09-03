"""Canonical release model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .asset import Asset


@dataclass(frozen=True)
class Release:
    """A source-independent application release."""

    version: str
    build: str | None = None
    release_date: str = ""
    release_notes: str = ""
    release_url: str | None = None
    assets: tuple[Asset, ...] = ()
    source: str = ""
    is_prerelease: bool = False
    is_draft: bool = False
    tag: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "build": self.build,
            "releaseDate": self.release_date,
            "releaseNotes": self.release_notes,
            "releaseUrl": self.release_url,
            "assets": [asset.to_dict() for asset in self.assets],
            "source": self.source,
            "isPrerelease": self.is_prerelease,
            "isDraft": self.is_draft,
            "tag": self.tag,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Release:
        assets = raw.get("assets")
        return cls(
            version=str(raw.get("version") or ""),
            build=(str(raw["build"]) if raw.get("build") is not None else None),
            release_date=str(raw.get("releaseDate") or raw.get("date") or ""),
            release_notes=str(raw.get("releaseNotes") or raw.get("localizedDescription") or ""),
            release_url=(str(raw["releaseUrl"]) if raw.get("releaseUrl") else None),
            assets=tuple(Asset.from_dict(item) for item in assets if isinstance(item, dict))
            if isinstance(assets, list)
            else (),
            source=str(raw.get("source") or ""),
            is_prerelease=bool(raw.get("isPrerelease", raw.get("prerelease", False))),
            is_draft=bool(raw.get("isDraft", raw.get("draft", False))),
            tag=(str(raw["tag"]) if raw.get("tag") else None),
        )
