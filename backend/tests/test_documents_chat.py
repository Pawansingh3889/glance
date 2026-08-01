"""DocumentChatService, with the LLM faked at its usual boundary.

The forced tool_turn call is exercised directly here, rather than through
DocumentService, so the retry/repair logic can be asserted precisely.
"""

import json

import pytest

from app.documents.chat import DocumentChatService
from app.llm.base import LLMError, ToolTurn

_DOC_TEXT = "[Control Measures]\nUse only with adequate ventilation. Wear nitrile gloves."


class FakeLLM:
    """Returns canned tool payloads in order (repeating the last)."""

    def __init__(self, *payloads: dict, note: str = "") -> None:
        self._payloads = list(payloads)
        self._note = note
        self.calls = 0

    async def tool_turn(self, **_):
        payload = self._payloads[min(self.calls, len(self._payloads) - 1)]
        self.calls += 1
        return ToolTurn(text=self._note, tool_name="respond_with_citations", tool_input=payload)


async def test_a_grounded_answer_returns_its_citations():
    fake = FakeLLM(
        {
            "answer": "Wear nitrile gloves.",
            "citations": [{"quote": "Wear nitrile gloves", "page": None, "section": None}],
        }
    )
    answer, citations = await DocumentChatService(llm=fake).reply(
        _DOC_TEXT, [{"role": "user", "content": "What PPE is needed?"}]
    )

    assert fake.calls == 1
    assert answer == "Wear nitrile gloves."
    assert citations[0].quote == "Wear nitrile gloves"


async def test_stringified_citations_are_decoded_not_retried():
    """A live run against llama3.2:3b emitted the right citations list JSON-encoded
    into a string — the same serialization slip generation.py already works around
    for a template's questions/options. Repaired, not burned as a retry."""
    payload = {
        "answer": "Wear nitrile gloves.",
        "citations": json.dumps([{"quote": "Wear nitrile gloves", "page": None, "section": None}]),
    }
    fake = FakeLLM(payload)
    answer, citations = await DocumentChatService(llm=fake).reply(
        _DOC_TEXT, [{"role": "user", "content": "What PPE is needed?"}]
    )

    assert fake.calls == 1  # repaired, not retried
    assert answer == "Wear nitrile gloves."
    assert citations[0].quote == "Wear nitrile gloves"


async def test_an_empty_tool_input_retries_once_then_fails_loudly():
    fake = FakeLLM({}, {})
    with pytest.raises(LLMError):
        await DocumentChatService(llm=fake).reply(_DOC_TEXT, [{"role": "user", "content": "?"}])
    assert fake.calls == 2


async def test_a_refusal_with_no_citations_is_accepted():
    fake = FakeLLM({"answer": "That's not in this document.", "citations": []})
    answer, citations = await DocumentChatService(llm=fake).reply(
        _DOC_TEXT, [{"role": "user", "content": "What's the boiling point?"}]
    )

    assert answer == "That's not in this document."
    assert citations == []
