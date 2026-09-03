"""HTTP client with retry, host-scoped credentials, and download probing.

Security invariant
------------------
Credentials are attached *only* when the request URL matches a configured
:class:`AuthRule` prefix (GitHub API, GitLab API, …). Download probes construct
their own header dict with no ``Authorization``. Third-party IPA URLs must
never receive a token.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from omnisource.constants import ALIVE_CODES, RETRYABLE_CODES, USER_AGENT
from omnisource.errors import ProviderError
from omnisource.logutil import log


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Stop at the first 3xx.

    Release hosts answer ``302`` and point at a signed CDN URL. Following that
    redirect proves nothing extra, costs an extra TLS handshake per app, and
    can start streaming a 120 MB IPA into the runner. A 3xx from the origin is
    sufficient evidence that the asset exists.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


_PROBE_OPENER = urllib.request.build_opener(_NoRedirect)


@dataclass(frozen=True)
class AuthRule:
    """Attach ``header_name: header_value`` to URLs starting with ``url_prefix``."""

    url_prefix: str
    header_name: str
    header_value: str


@dataclass(frozen=True)
class ProbeResult:
    reachable: bool
    detail: str
    url: str


class HttpClient:
    """Stdlib HTTP client used by every provider and the health probe."""

    def __init__(
        self,
        *,
        user_agent: str = USER_AGENT,
        auth_rules: tuple[AuthRule, ...] = (),
        default_timeout: float = 30.0,
        retries: int = 3,
    ) -> None:
        self.user_agent = user_agent
        self.auth_rules = auth_rules
        self.default_timeout = default_timeout
        self.retries = retries
        self.requests = 0

    def _auth_headers(self, url: str) -> dict[str, str]:
        headers: dict[str, str] = {"User-Agent": self.user_agent}
        for rule in self.auth_rules:
            if url.startswith(rule.url_prefix):
                headers[rule.header_name] = rule.header_value
        return headers

    def _open(
        self,
        url: str,
        *,
        headers: dict[str, str],
        method: str = "GET",
        timeout: float | None = None,
        follow_redirects: bool = True,
    ):
        request = urllib.request.Request(url, headers=headers, method=method)
        opener = urllib.request.urlopen if follow_redirects else _PROBE_OPENER.open
        self.requests += 1
        return opener(request, timeout=timeout or self.default_timeout)

    def get_json(self, url: str, *, extra_headers: dict[str, str] | None = None, retries: int | None = None) -> Any:
        """GET a JSON endpoint with bounded exponential backoff.

        Auth headers are applied only when ``url`` matches an :class:`AuthRule`.
        """
        headers = self._auth_headers(url)
        headers["Accept"] = "application/json"
        if extra_headers:
            headers.update(extra_headers)

        attempts = retries if retries is not None else self.retries
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                with self._open(url, headers=headers) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                last_error = error
                if error.code not in RETRYABLE_CODES:
                    break
                delay = float(error.headers.get("Retry-After") or 2**attempt)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
                last_error = error
                delay = float(2**attempt)
            else:
                continue
            if attempt < attempts:
                log.warning(
                    "HTTP attempt %d/%d failed (%s); retrying in %.0fs",
                    attempt,
                    attempts,
                    last_error,
                    delay,
                )
                time.sleep(delay)

        raise ProviderError(f"HTTP request failed after {attempts} attempts: {url} ({last_error})")

    def get_bytes(self, url: str, *, limit: int = 64_000, timeout: float = 12.0) -> bytes:
        """Fetch at most ``limit`` bytes. Never used for IPA payloads."""
        headers = self._auth_headers(url)
        with self._open(url, headers=headers, timeout=timeout) as response:
            return response.read(limit)

    def probe(self, url: str, *, timeout: float = 12.0, retries: int = 2) -> ProbeResult:
        """Return reachability for a download URL, without credentials.

        Uses HEAD first; falls back to a one-byte ranged GET for hosts that
        reject HEAD, so a probe never downloads a whole IPA into the runner.
        """
        if not isinstance(url, str) or not url:
            return ProbeResult(False, "empty url", url or "")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ProbeResult(False, "not an http(s) url", url)

        headers = {"User-Agent": self.user_agent}
        detail = "unknown"
        for attempt in range(1, retries + 1):
            for method, extra in (("HEAD", {}), ("GET", {"Range": "bytes=0-0"})):
                try:
                    with self._open(
                        url,
                        headers={**headers, **extra},
                        method=method,
                        timeout=timeout,
                        follow_redirects=False,
                    ) as response:
                        if response.status in ALIVE_CODES:
                            return ProbeResult(True, f"HTTP {response.status}", url)
                        detail = f"HTTP {response.status}"
                except urllib.error.HTTPError as error:
                    detail = f"HTTP {error.code}"
                    if error.code in ALIVE_CODES:
                        return ProbeResult(True, detail, url)
                    if error.code in RETRYABLE_CODES:
                        break
                    if method == "GET":
                        return ProbeResult(False, detail, url)
                    if error.code not in {403, 405, 501}:
                        return ProbeResult(False, detail, url)
                except (urllib.error.URLError, TimeoutError, OSError) as error:
                    detail = str(getattr(error, "reason", error))
                    break
            if attempt < retries:
                time.sleep(1.5 * attempt)
        return ProbeResult(False, detail, url)


def github_accept_headers() -> dict[str, str]:
    return {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def is_http_url(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = urllib.parse.urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
