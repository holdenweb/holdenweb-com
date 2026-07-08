"""HTTP-vs-filesystem abstraction for site content.

Content (Markdown notes, HTML pages, and their embedded assets) lives
either in the package's `data/` directory (local dev, the default when
`CONTENT_BASE_URL` is unset) or in one or more Opalstack static apps
behind a shared Bearer token (production). Route handlers reach either
backend through the same `ContentSource` protocol.

Only `LocalContentSource` is defined here; the HTTP backend arrives in
a later commit.
"""

from __future__ import annotations

import mimetypes
import re
from logging import getLogger
from pathlib import Path
from typing import Protocol

import requests
from cachetools import TTLCache

logger = getLogger(__name__)


_ON_DISK = {"html": "html-pages", "md": "md-pages"}

_ABSOLUTE_PREFIXES = ("/", "http://", "https://", "data:", "#", "mailto:")


class ContentNotFound(LookupError):
    """The requested content does not exist upstream."""


class ContentUnavailable(RuntimeError):
    """The content backend is unreachable (network error / upstream 5xx)."""


class ContentSource(Protocol):
    def html(self, name: str) -> str: ...
    def markdown(self, name: str) -> str: ...
    def asset(self, path: str) -> tuple[bytes, str]: ...


def _check_relative(path: str) -> None:
    if not path or path.startswith("/"):
        raise ContentNotFound(path)
    for segment in path.split("/"):
        if segment in ("", "..", "."):
            raise ContentNotFound(path)


def _resolve_asset(path: str) -> str:
    head, _, tail = path.partition("/")
    on_disk = _ON_DISK.get(head)
    if on_disk is None:
        raise ContentNotFound(path)
    return f"{on_disk}/{tail}" if tail else on_disk


class LocalContentSource:
    """Reads content from `<root>/{html-pages,md-pages}/…` on disk."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def html(self, name: str) -> str:
        _check_relative(name)
        fpath = self._root / "html-pages" / f"{name}.html"
        try:
            return fpath.read_text()
        except OSError as exc:
            raise ContentNotFound(name) from exc

    def markdown(self, name: str) -> str:
        _check_relative(name)
        fpath = self._root / "md-pages" / f"{name}.md"
        try:
            return fpath.read_text()
        except OSError as exc:
            raise ContentNotFound(name) from exc

    def asset(self, path: str) -> tuple[bytes, str]:
        _check_relative(path)
        fpath = self._root / _resolve_asset(path)
        try:
            body = fpath.read_bytes()
        except OSError as exc:
            raise ContentNotFound(path) from exc
        ctype, _ = mimetypes.guess_type(str(fpath))
        return body, ctype or "application/octet-stream"


class HTTPContentSource:
    """Fetches content from an Opalstack static app behind a Bearer token.

    Both text and asset lookups are cached with distinct TTLs -- assets
    change less often than the wrapping text, so their cache is longer.
    If a fetch fails and a stale entry exists, the stale value is served
    with a warning log rather than surfacing an error.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 5.0,
        text_ttl: int = 300,
        asset_ttl: int = 3600,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {token}"
        self._text_cache: TTLCache[str, str] = TTLCache(maxsize=256, ttl=text_ttl)
        self._asset_cache: TTLCache[str, tuple[bytes, str]] = TTLCache(
            maxsize=128, ttl=asset_ttl
        )

    def html(self, name: str) -> str:
        _check_relative(name)
        return self._fetch_text(f"html/{name}.html")

    def markdown(self, name: str) -> str:
        _check_relative(name)
        return self._fetch_text(f"md/{name}.md")

    def asset(self, path: str) -> tuple[bytes, str]:
        _check_relative(path)
        # Ensure it's under a known category before hitting the network.
        _resolve_asset(path)
        cached = self._asset_cache.get(path)
        try:
            resp = self._session.get(
                f"{self._base_url}/{path}", timeout=self._timeout
            )
        except requests.RequestException as exc:
            if cached is not None:
                logger.warning(
                    "content asset %s: network error, serving stale: %s",
                    path, exc,
                )
                return cached
            raise ContentUnavailable(path) from exc
        if resp.status_code == 404:
            raise ContentNotFound(path)
        if not resp.ok:
            if cached is not None:
                logger.warning(
                    "content asset %s: upstream %s, serving stale",
                    path, resp.status_code,
                )
                return cached
            raise ContentUnavailable(f"{path}: {resp.status_code}")
        ctype = resp.headers.get("Content-Type")
        if not ctype:
            ctype, _ = mimetypes.guess_type(path)
            ctype = ctype or "application/octet-stream"
        result = (resp.content, ctype)
        self._asset_cache[path] = result
        return result

    def _fetch_text(self, path: str) -> str:
        cached = self._text_cache.get(path)
        try:
            resp = self._session.get(
                f"{self._base_url}/{path}", timeout=self._timeout
            )
        except requests.RequestException as exc:
            if cached is not None:
                logger.warning(
                    "content %s: network error, serving stale: %s", path, exc,
                )
                return cached
            raise ContentUnavailable(path) from exc
        if resp.status_code == 404:
            raise ContentNotFound(path)
        if not resp.ok:
            if cached is not None:
                logger.warning(
                    "content %s: upstream %s, serving stale",
                    path, resp.status_code,
                )
                return cached
            raise ContentUnavailable(f"{path}: {resp.status_code}")
        text = resp.text
        self._text_cache[path] = text
        return text


# src="…" / href="…" with either quoting style. Non-greedy value match
# so multiple attributes on the same tag don't get swallowed together.
_ATTR_RE = re.compile(
    r'(?P<attr>src|href)\s*=\s*(?P<q>["\'])(?P<val>[^"\']*)(?P=q)',
    re.IGNORECASE,
)


def rewrite_asset_urls(html: str, page_dir: str) -> str:
    """Rewrite relative `src`/`href` values into `/asset/html/<page_dir>/…`.

    Absolute URLs, anchors, `mailto:`, and `data:` URIs pass through
    unchanged. `page_dir` is the directory the source page lives in
    relative to `html-pages/`, with no trailing slash — empty when the
    page is at the root.
    """
    prefix = f"/asset/html/{page_dir}" if page_dir else "/asset/html"

    def _replace(m: re.Match[str]) -> str:
        val = m.group("val")
        lowered = val.lower()
        if any(lowered.startswith(p) for p in _ABSOLUTE_PREFIXES):
            return m.group(0)
        return f'{m.group("attr")}={m.group("q")}{prefix}/{val}{m.group("q")}'

    return _ATTR_RE.sub(_replace, html)
