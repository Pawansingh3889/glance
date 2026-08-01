"""DocumentService, with parsing and the network fetcher faked at their own
boundaries — same philosophy as the LLM client: nothing here needs a real Docling
model download or a real network call to prove the orchestration is correct.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.documents.enums import DocumentSourceType, DocumentStatus
from app.documents.fetcher import FetchedDocument
from app.documents.models import Document
from app.documents.parsing import DocumentParsingError, ParsedDocument
from app.documents.service import DocumentService
from app.errors import ConflictError, NotFoundError
from app.users.models import User, UserRole
from tests.fakes import document_answer

_PARSED = ParsedDocument(
    content={
        "sections": [{"heading": "Intro", "page": 1, "text": "Wear PPE at all times."}],
        "tables": [],
        "page_count": 1,
    },
    quality=0.9,
)


class FakeStorage:
    """In-memory Storage — no real disk I/O, same role FakeLLM plays for the model."""

    def __init__(self) -> None:
        self.saved: dict[str, bytes] = {}
        self.deleted: list[str] = []
        self._next = 0

    def new_key(self) -> str:
        self._next += 1
        return f"key-{self._next}"

    def save(self, key: str, data: bytes) -> None:
        self.saved[key] = data

    def read(self, key: str) -> bytes:
        return self.saved[key]

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.saved.pop(key, None)


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


async def _ready_document(session, owner: User, storage: FakeStorage) -> Document:
    document = Document(
        owner_id=owner.id,
        title="Safety Procedure.pdf",
        source_type=DocumentSourceType.upload,
        storage_key=storage.new_key(),
        content_type="application/pdf",
        size_bytes=100,
        status=DocumentStatus.ready,
        parsed_content=_PARSED.content,
        extraction_quality=_PARSED.quality,
        expires_at=datetime.now(UTC) + timedelta(hours=48),
    )
    session.add(document)
    await session.flush()
    return document


async def test_fetch_from_url_saves_parses_and_marks_ready(session, creator, storage, monkeypatch):
    async def _fake_fetch(url, settings):
        return _fetched(b"# Safety\n\nWear PPE.", "text/markdown")

    monkeypatch.setattr("app.documents.service.fetch_url", _fake_fetch)
    monkeypatch.setattr("app.documents.service.parse_document", lambda name, data: _PARSED)

    document = await DocumentService(session, storage=storage).fetch_from_url(
        "https://example.com/safety.md", creator
    )

    assert document.status is DocumentStatus.ready
    assert document.source_type is DocumentSourceType.url
    assert document.source_url == "https://example.com/safety.md"
    assert document.parsed_content == _PARSED.content
    assert document.extraction_quality == 0.9
    assert storage.saved[document.storage_key] == b"# Safety\n\nWear PPE."


async def test_a_parsing_failure_is_recorded_on_the_document_not_raised(
    session, creator, storage, monkeypatch
):
    async def _fake_fetch(url, settings):
        return _fetched(b"garbage", "application/pdf")

    monkeypatch.setattr("app.documents.service.fetch_url", _fake_fetch)

    def _fail(name, data):
        raise DocumentParsingError("Could not read this scan.")

    monkeypatch.setattr("app.documents.service.parse_document", _fail)

    document = await DocumentService(session, storage=storage).fetch_from_url(
        "https://example.com/bad.pdf", creator
    )

    assert document.status is DocumentStatus.failed
    assert document.error_message == "Could not read this scan."
    assert document.parsed_content is None


async def test_send_message_appends_both_turns_with_citations(session, creator, storage, fake_llm):
    document = await _ready_document(session, creator, storage)
    fake_llm(
        document_answer("PPE is required at all times.", [{"quote": "Wear PPE at all times."}])
    )

    updated = await DocumentService(session, storage=storage).send_message(
        document.id, "Do I need PPE?", creator
    )

    assert [m.content for m in updated.messages] == [
        "Do I need PPE?",
        "PPE is required at all times.",
    ]
    assert updated.messages[-1].citations == [
        {"quote": "Wear PPE at all times.", "page": None, "section": None}
    ]


async def test_send_message_refuses_a_document_that_is_not_ready_yet(
    session, creator, storage, fake_llm
):
    document = Document(
        owner_id=creator.id,
        title="Still parsing.pdf",
        source_type=DocumentSourceType.upload,
        storage_key=storage.new_key(),
        content_type="application/pdf",
        size_bytes=10,
        status=DocumentStatus.parsing,
        expires_at=datetime.now(UTC) + timedelta(hours=48),
    )
    session.add(document)
    await session.flush()
    fake_llm()  # no scripted turn: reaching the model at all is itself the failure

    with pytest.raises(ConflictError):
        await DocumentService(session, storage=storage).send_message(document.id, "hello?", creator)


async def test_one_owners_document_is_invisible_to_another(session, creator, storage):
    document = await _ready_document(session, creator, storage)
    stranger = User(email="stranger@test.dev", display_name="Stranger", role=UserRole.creator)
    session.add(stranger)
    await session.flush()

    with pytest.raises(NotFoundError):
        await DocumentService(session, storage=storage).get(document.id, stranger)


async def test_list_for_owner_only_returns_that_owners_documents(session, creator, storage):
    mine = await _ready_document(session, creator, storage)
    other = User(email="other-owner@test.dev", display_name="Other", role=UserRole.creator)
    session.add(other)
    await session.flush()
    await _ready_document(session, other, storage)

    listed = await DocumentService(session, storage=storage).list_for_owner(creator)

    assert [d.id for d in listed] == [mine.id]


def _fetched(content: bytes, content_type: str) -> FetchedDocument:
    return FetchedDocument(content=content, content_type=content_type, final_url="")
