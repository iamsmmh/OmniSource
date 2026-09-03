"""Version parsing and comparison for release/update decisions.

Semantic versions are compared according to SemVer 2.0.0, including the rule
that a pre-release is lower than the corresponding stable release. For tags
that are not SemVer, the numeric components are compared as a deterministic
fallback (for example ``ytl-ipa4`` or ``2026.09``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering

_SEMVER_RE = re.compile(
    r"^[\s]*[vV]?"
    r"(?P<major>0|[1-9]\d*)"
    r"(?:\.(?P<minor>0|[1-9]\d*))?"
    r"(?:\.(?P<patch>0|[1-9]\d*))?"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?"
    r"(?:\+(?P<build>[0-9A-Za-z.-]+))?[\s]*$"
)


def _numeric_parts(value: str) -> tuple[int, ...]:
    numbers = tuple(int(part) for part in re.findall(r"\d+", value or ""))
    return numbers or (0,)


def parse_version(value: str) -> tuple[int, ...]:
    """Compatibility helper returning numeric components."""
    return _numeric_parts(value)


@total_ordering
@dataclass(frozen=True)
class Version:
    """Comparable normalized version value."""

    raw: str
    numbers: tuple[int, ...]
    prerelease: tuple[int | str, ...] = ()
    semver: bool = False

    @classmethod
    def parse(cls, value: str | None) -> Version:
        raw = str(value or "").strip()
        match = _SEMVER_RE.match(raw)
        if not match:
            return cls(raw=raw, numbers=_numeric_parts(raw), semver=False)
        numbers = tuple(int(match.group(name) or 0) for name in ("major", "minor", "patch"))
        pre: list[int | str] = []
        if match.group("pre"):
            for part in match.group("pre").split("."):
                pre.append(int(part) if part.isdigit() else part.lower())
        return cls(raw=raw, numbers=numbers, prerelease=tuple(pre), semver=True)

    def _key(self) -> tuple[object, ...]:
        if self.semver:
            # Stable releases sort after every pre-release. Numeric pre-release
            # identifiers sort before textual identifiers per SemVer.
            pre_key: tuple[object, ...]
            if not self.prerelease:
                pre_key = (1,)
            else:
                values: list[object] = [0]
                for part in self.prerelease:
                    values.append((0, part) if isinstance(part, int) else (1, part))
                pre_key = tuple(values)
            return (1, *self.numbers, pre_key)
        return (0, self.numbers, self.raw.casefold())

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        # SemVer values are naturally comparable to each other. A non-SemVer
        # fallback deliberately remains deterministic rather than pretending a
        # tag such as ``release`` is a semantic version.
        if self.semver and other.semver:
            if self.numbers != other.numbers:
                return self.numbers < other.numbers
            if not self.prerelease:
                return bool(other.prerelease)
            if not other.prerelease:
                return True
            for left, right in zip(self.prerelease, other.prerelease, strict=False):
                if left == right:
                    continue
                if isinstance(left, int) and isinstance(right, str):
                    return True
                if isinstance(left, str) and isinstance(right, int):
                    return False
                return left < right
            return len(self.prerelease) < len(other.prerelease)
        return self._key() < other._key()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        if self.semver and other.semver:
            return self.numbers == other.numbers and self.prerelease == other.prerelease
        return self._key() == other._key()


def compare_versions(left: str, right: str) -> int:
    a, b = Version.parse(left), Version.parse(right)
    return (a > b) - (a < b)


def is_newer(candidate: str, current: str) -> bool:
    return compare_versions(candidate, current) > 0
