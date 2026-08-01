"""Docling integration: parse an uploaded/fetched document into a structured,
citable representation, plus an honest extraction-quality score.

Run through ``asyncio.to_thread`` by the caller — Docling's conversion is CPU-bound
(layout, table structure, OCR), and this is the one place in the app that does
sustained CPU work inside a request; without the offload it would stall the event
loop, and every other in-flight request, for as long as the parse takes.
"""

import math
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from app.errors import AppError

# What Docling can parse, and what this domain accepts — used both to type-sniff an
# upload (by magic bytes, never the filename extension) and to gate a fetched URL's
# Content-Type before its body is downloaded.
SUPPORTED_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
        "text/html",
        "text/markdown",
        "text/plain",
        "text/csv",
        "image/png",
        "image/jpeg",
        "image/tiff",
    }
)


class DocumentParsingError(AppError):
    status_code = 422
    code = "document_parsing_failed"


@dataclass(frozen=True)
class ParsedDocument:
    # JSON-serializable: {"sections": [...], "tables": [...], "page_count": int|None}.
    # Stored as-is in Document.parsed_content; see render_for_prompt() for the text
    # form the chat model sees, and the frontend renders this same shape directly.
    content: dict[str, Any]
    quality: float | None


def parse_document(name: str, data: bytes) -> ParsedDocument:
    """Blocking — see the module docstring. Raises ``DocumentParsingError`` rather
    than letting a malformed or unreadable file surface a raw Docling exception.

    Takes bytes rather than a storage path or key, deliberately: parsing has no
    business knowing how or where a document is stored, only what it contains — the
    same reasoning ``Storage`` exists as its own seam in storage.py.
    """
    from docling.datamodel.document import ConversionStatus  # type: ignore[attr-defined]
    from docling.document_converter import DocumentConverter
    from docling_core.types.io import DocumentStream

    stream = DocumentStream(name=name, stream=BytesIO(data))
    result = DocumentConverter().convert(stream, raises_on_error=False)
    if result.status in (ConversionStatus.FAILURE, ConversionStatus.SKIPPED):
        reasons = "; ".join(str(e) for e in result.errors) or "unknown error"
        raise DocumentParsingError(f"Could not parse this document: {reasons}")
    return ParsedDocument(content=_to_content(result), quality=_quality(result))


def _to_content(result: Any) -> dict[str, Any]:
    doc = result.document
    sections: list[dict[str, Any]] = []
    heading: str | None = None
    for item, _level in doc.iterate_items():
        label = getattr(item, "label", None)
        label_value = getattr(label, "value", label) or "text"
        text = getattr(item, "text", None)
        if label_value in ("section_header", "title"):
            heading = text
            continue  # the heading becomes the group label, not a body line
        if text:
            sections.append(
                {"heading": heading, "page": _page_of(item), "text": text, "kind": label_value}
            )
    tables: list[dict[str, Any]] = []
    for table in doc.tables:
        try:
            grid = table.export_to_markdown(doc)
        except Exception:  # noqa: BLE001 — a table that fails to render must not sink the parse
            grid = None
        if grid:
            tables.append({"heading": heading, "page": _page_of(table), "markdown": grid})
    page_count = len(doc.pages) if doc.pages else None
    return {"sections": sections, "tables": tables, "page_count": page_count}


def _page_of(item: Any) -> int | None:
    prov = getattr(item, "prov", None)
    if not prov:
        return None
    page_no = getattr(prov[0], "page_no", None)
    return int(page_no) if page_no is not None else None


def _quality(result: Any) -> float | None:
    """Docling's own aggregate confidence score, reported as-is rather than re-derived.

    ``mean_score`` is already a NaN-safe average of whichever component scores this
    document had anything to say about (``table_score`` is meaningless with no tables
    on the page, for instance) — using it directly means this domain's notion of
    "quality" never drifts from Docling's own definition of it.
    """
    confidence = getattr(result, "confidence", None)
    if confidence is None:
        return None
    score = confidence.mean_score
    return None if math.isnan(score) else float(score)


def render_for_prompt(content: dict[str, Any]) -> str:
    """The whole document as plain text, labelled by page/section — what the chat
    model is shown. No chunking, no retrieval: the design note's point for this path
    is that a form or a short report fits in context whole, so all of it goes in."""
    lines: list[str] = []
    _UNSET = object()
    last_heading: object = _UNSET
    for block in content.get("sections", []):
        heading = block.get("heading")
        if heading != last_heading:
            page = block.get("page")
            suffix = f" — page {page}]" if page else "]"
            lines.append(f"\n[{heading or 'Untitled section'}{suffix}")
            last_heading = heading
        lines.append(str(block.get("text", "")))
    for table in content.get("tables", []):
        page = table.get("page")
        suffix = f" — page {page}]" if page else "]"
        lines.append(f"\n[Table{suffix}")
        lines.append(str(table.get("markdown", "")))
    return "\n".join(lines).strip()
