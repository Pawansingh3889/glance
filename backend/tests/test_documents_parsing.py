"""Docling integration, run against real (but tiny, text-based) input.

Markdown never triggers Docling's OCR/layout model downloads, so these run fast and
offline — only a scanned PDF needs the heavier pipeline, which is why the service- and
HTTP-level tests fake ``parse_document`` instead of exercising a real parse.
"""

import pytest

from app.documents.parsing import DocumentParsingError, parse_document, render_for_prompt

_SAMPLE = b"""# Metal Detection Procedure

All product must pass through the metal detector before packing.

## Calibration

Calibrate daily using the 2.5mm ferrous test piece.

| Shift | Operator | Result |
|---|---|---|
| AM | J. Smith | Pass |
"""


def test_parse_extracts_headings_and_body_text():
    parsed = parse_document("sample.md", _SAMPLE)

    headings = {s["heading"] for s in parsed.content["sections"]}
    assert headings == {"Metal Detection Procedure", "Calibration"}
    bodies = [s["text"] for s in parsed.content["sections"]]
    assert "Calibrate daily using the 2.5mm ferrous test piece." in bodies


def test_headings_are_not_duplicated_as_their_own_body_line():
    """A title/section_header item's own text becomes the group label, not also a
    body line under itself — the group label already carries it."""
    parsed = parse_document("sample.md", _SAMPLE)

    bodies = [s["text"] for s in parsed.content["sections"]]
    assert "Metal Detection Procedure" not in bodies
    assert "Calibration" not in bodies


def test_parse_extracts_tables_separately_with_their_heading_and_page():
    parsed = parse_document("sample.md", _SAMPLE)

    assert len(parsed.content["tables"]) == 1
    table = parsed.content["tables"][0]
    assert "J. Smith" in table["markdown"]
    assert table["heading"] == "Calibration"


def test_render_for_prompt_labels_sections_and_tables_by_heading():
    text = render_for_prompt(parse_document("sample.md", _SAMPLE).content)

    assert "[Metal Detection Procedure]" in text
    assert "[Calibration]" in text
    assert "[Table" in text
    assert "J. Smith" in text


def test_quality_is_reported_as_unknown_rather_than_invented():
    """Docling's confidence scores are NaN when a document type has nothing to score
    (markdown has no page/layout/OCR concept) — reported as None, not a fake number."""
    parsed = parse_document("sample.md", _SAMPLE)
    assert parsed.quality is None


def test_a_file_type_docling_does_not_recognise_fails_loudly_not_silently():
    with pytest.raises(DocumentParsingError):
        parse_document("mystery.xyz", b"\x00\x01\x02 not a real document \xff\xfe")
