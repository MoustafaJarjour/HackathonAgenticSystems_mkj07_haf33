"""Source text acquisition, with offline excerpt/cache paths as the default."""

from __future__ import annotations

import hashlib
import io
import os
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import httpx
from pypdf import PdfReader

from .openrouter_client import Budget, BudgetError
from .trace import Trace

MAX_BYTES = 12 * 1024 * 1024
MAX_TEXT_CHARS = 200_000


class SourceError(RuntimeError):
    """Source retrieval or extraction failed without inventing paper content."""


@dataclass(frozen=True)
class Source:
    text: str
    url: str
    method: str
    locations: tuple[str, ...] = ()


class _TextParser(HTMLParser):
    """Minimal prose extractor; scripts, styling, navigation and forms are ignored."""

    IGNORED = {"script", "style", "nav", "noscript", "form", "iframe", "svg"}
    BLOCK = {"p", "div", "section", "article", "h1", "h2", "h3", "h4", "li", "br", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.IGNORED:
            self._ignored.append(tag)
        if tag in self.BLOCK and not self._ignored:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._ignored:
            position = len(self._ignored) - 1 - self._ignored[::-1].index(tag)
            del self._ignored[position:]
        if tag in self.BLOCK and not self._ignored:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignored:
            self.parts.append(data)

    def text(self) -> str:
        text = "".join(self.parts)
        lines = [re.sub(r"[ \t\r\f\v]+", " ", line).strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)


def _extract(data: bytes, is_pdf: bool, budget: Budget) -> tuple[str, tuple[str, ...]]:
    budget.check()
    if is_pdf or data.startswith(b"%PDF-"):
        try:
            reader = PdfReader(io.BytesIO(data))
            pages: list[str] = []
            labels: list[str] = []
            total = 0
            for index, page in enumerate(reader.pages, 1):
                budget.check()
                content = page.extract_text() or ""
                label = f"Page {index}"
                pages.append(f"[{label}]\n{content}")
                labels.append(label)
                total += len(content)
                if total >= MAX_TEXT_CHARS:
                    break
            return "\n\n".join(pages), tuple(labels)
        except (SourceError, BudgetError):
            raise
        except Exception:
            # PDF errors can include arbitrary file content; do not echo them.
            raise SourceError("Could not extract text from the supplied PDF.") from None
    text = data.decode("utf-8", errors="replace")
    if re.search(r"<(?:!doctype\s+html|html|body|article|p)(?:\s|>)", text, re.I):
        parser = _TextParser()
        parser.feed(text)
        text = parser.text()
    return text, ()


def _checked(text: str, url: str, method: str, locations: tuple[str, ...], trace: Trace) -> Source:
    text = text.strip()
    if len(text) < 100:
        raise SourceError("Source extraction produced fewer than 100 characters of usable text.")
    original_length = len(text)
    text = text[:MAX_TEXT_CHARS]
    trace.event(
        "source", "extract", "ok", method=method, characters=len(text),
        truncated=original_length > MAX_TEXT_CHARS, location_count=len(locations),
    )
    return Source(text=text, url=url, method=method, locations=locations)


def _read_file(path: Path, budget: Budget) -> tuple[str, tuple[str, ...]]:
    budget.check()
    try:
        if not path.is_file():
            raise SourceError("The configured source file does not exist.")
        if path.stat().st_size > MAX_BYTES:
            raise SourceError("The source file exceeds the 12 MiB starter limit.")
        return _extract(path.read_bytes(), path.suffix.lower() == ".pdf", budget)
    except OSError:
        raise SourceError("The configured source file could not be read.") from None


def _download(url: str, budget: Budget) -> tuple[str, tuple[str, ...]]:
    budget.check()
    try:
        # Downloading is development-only and explicitly enabled by the caller.
        with httpx.Client(follow_redirects=True, max_redirects=5) as client:
            with client.stream("GET", url, timeout=max(0.1, min(30.0, budget.remaining()))) as response:
                if not 200 <= response.status_code <= 299:
                    raise SourceError(f"Source server returned HTTP {response.status_code}.")
                length = response.headers.get("content-length", "")
                if length.isdigit() and int(length) > MAX_BYTES:
                    raise SourceError("The downloaded source exceeds the 12 MiB starter limit.")
                data = bytearray()
                for chunk in response.iter_bytes():
                    budget.check()
                    data.extend(chunk)
                    if len(data) > MAX_BYTES:
                        raise SourceError("The downloaded source exceeds the 12 MiB starter limit.")
                return _extract(bytes(data), "pdf" in response.headers.get("content-type", "").lower(), budget)
    except httpx.HTTPError:
        raise SourceError("The source download failed or timed out.") from None


def _arxiv_pdf_fallback(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname not in {"arxiv.org", "www.arxiv.org", "export.arxiv.org"}:
        return None
    if parsed.path.startswith(("/abs/", "/html/")):
        identifier = parsed.path.split("/", 2)[2]
        return urlunparse((parsed.scheme, parsed.netloc, f"/pdf/{identifier}", "", "", ""))
    return None


def obtain_source(case: dict, input_path: Path, trace: Trace, budget: Budget) -> Source:
    """Use an optional excerpt, local file/cache, or explicit development fetch.

    The assignment does not define an excerpt key. These aliases are optional
    conveniences, never additional required case fields. Unknown fields remain
    untouched by the input loader.
    """
    budget.check()
    url = case["source_url"]
    for alias in ("excerpt", "source_text", "paper_excerpt"):
        inline = case.get(alias)
        if isinstance(inline, str) and inline.strip():
            return _checked(inline, url, f"inline:{alias}", (), trace)

    configured = os.environ.get("PTP_SOURCE_FILE", "").strip()
    if configured:
        path = Path(configured)
        if not path.is_absolute():
            path = input_path.parent / path
        text, locations = _read_file(path, budget)
        return _checked(text, url, "local_file", locations, trace)

    directory = os.environ.get("PTP_SOURCE_DIR", "").strip()
    if directory:
        cache = Path(directory)
        if not cache.is_absolute():
            cache = input_path.parent / cache
        name = hashlib.sha256(url.encode("utf-8")).hexdigest()
        for extension in (".txt", ".pdf"):
            candidate = cache / (name + extension)
            if candidate.is_file():
                text, locations = _read_file(candidate, budget)
                return _checked(text, url, "local_cache", locations, trace)

    if os.environ.get("PTP_ALLOW_SOURCE_FETCH") != "1":
        raise SourceError(
            "No paper text is available. The assessment permits only OpenRouter requests "
            "and does not specify the excerpt field name. Supply optional excerpt, source_text, "
            "or paper_excerpt; set PTP_SOURCE_FILE; or use a PTP_SOURCE_DIR cache. "
            "For development outside assessment only, set PTP_ALLOW_SOURCE_FETCH=1."
        )
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise SourceError("Development source fetching requires an HTTP(S) URL without credentials.")
    trace.event("source", "download", "started", method="development_http")
    fallback = _arxiv_pdf_fallback(url)
    try:
        # An arXiv /abs page is metadata, not paper text; prefer the full PDF.
        if fallback and parsed.path.startswith("/abs/"):
            text, locations = _download(fallback, budget)
        else:
            text, locations = _download(url, budget)
        return _checked(text, url, "development_http", locations, trace)
    except SourceError:
        if fallback and not parsed.path.startswith("/abs/"):
            trace.event("source", "download_fallback", "started", method="development_pdf")
            text, locations = _download(fallback, budget)
            return _checked(text, url, "development_pdf", locations, trace)
        raise
