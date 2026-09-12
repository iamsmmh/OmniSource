"""Safe, deterministic feature-flag evaluation.

Flags are configuration, not user profiles.  Rollouts hash a stable source or
app identifier supplied by the caller, never an account or browsing history.
The default for an unknown flag is ``False`` so a malformed configuration
fails closed.  Environment overrides are useful for emergency disablement in
CI and are parsed strictly.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Flag:
    key: str
    enabled: bool = False
    rollout: int = 100
    environments: tuple[str, ...] = ()

    def allows(self, *, subject: str = "", environment: str = "production") -> bool:
        if environment not in {"", "production"} and self.environments and environment not in self.environments:
            return False
        if not self.enabled:
            return False
        percentage = max(0, min(100, int(self.rollout)))
        if percentage >= 100:
            return True
        if not subject:
            return False
        bucket = int(hashlib.sha256(f"{self.key}:{subject}".encode()).hexdigest()[:8], 16) % 100
        return bucket < percentage


class FeatureFlags:
    """Immutable flag snapshot with explicit environment overrides."""

    def __init__(self, flags: dict[str, Flag], *, environment: str = "production") -> None:
        self.flags = dict(flags)
        self.environment = environment

    @classmethod
    def from_document(cls, document: Any, *, environment: str | None = None) -> FeatureFlags:
        raw_flags = document.get("flags", {}) if isinstance(document, dict) else {}
        values: dict[str, Flag] = {}
        if isinstance(raw_flags, dict):
            for key, raw in raw_flags.items():
                if isinstance(raw, bool):
                    raw = {"enabled": raw}
                if not isinstance(raw, dict):
                    continue
                values[str(key)] = Flag(
                    key=str(key),
                    enabled=bool(raw.get("enabled", False)),
                    rollout=int(raw.get("rollout", 100) or 0),
                    environments=tuple(str(item) for item in raw.get("environments", []) if item),
                )
        return cls(values, environment=environment or os.environ.get("OMNISOURCE_ENV", "production"))

    @classmethod
    def load(cls, root: Path, *, environment: str | None = None) -> FeatureFlags:
        # Configuration lives under config/ so root-level publication remains
        # limited to the catalog, install feed, and sitemap. Keep the root
        # path as a backwards-compatible fallback for older deployments.
        paths = (Path(root) / "config" / "feature_flags.json", Path(root) / "feature_flags.json")
        document: Any = {}
        for path in paths:
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(document, dict) and isinstance(document.get("$ref"), str):
                    reference = (path.parent / document["$ref"]).resolve()
                    document = json.loads(reference.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(document, dict):
                break
        instance = cls.from_document(document, environment=environment)
        overrides = os.environ.get("OMNISOURCE_FLAGS", "")
        if overrides:
            mutable = dict(instance.flags)
            for item in overrides.split(","):
                if "=" not in item:
                    continue
                key, value = item.split("=", 1)
                if key in mutable and value.strip().lower() in {"0", "1", "true", "false", "on", "off"}:
                    mutable[key] = Flag(
                        key=key,
                        enabled=value.strip().lower() in {"1", "true", "on"},
                        rollout=mutable[key].rollout,
                        environments=mutable[key].environments,
                    )
            instance = cls(mutable, environment=instance.environment)
        return instance

    def enabled(self, key: str, *, subject: str = "") -> bool:
        flag = self.flags.get(key)
        return flag.allows(subject=subject, environment=self.environment) if flag else False

    def as_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "flags": {
                key: {
                    "enabled": flag.enabled,
                    "rollout": flag.rollout,
                    "environments": list(flag.environments),
                }
                for key, flag in sorted(self.flags.items())
            },
        }


__all__ = ["FeatureFlags", "Flag"]
