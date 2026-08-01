"""Upload, fetch, parse, and chat with a single session document.

The chat turn mirrors ``ConductEngine.handle_message``'s shape — append the user's
message, call the model, append its reply, commit — but with no state machine behind
it: a document-chat turn is one bounded question-and-answer, not a scripted survey
with questions and progress to track.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit
from uuid import UUID

import filetype
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.documents.chat import DocumentChatService
from app.documents.enums import DocumentSourceType, DocumentStatus
from app.documents.fetcher import fetch_url
from app.documents.models import Document, DocumentMessage
from app.documents.parsing import (
    SUPPORTED_CONTENT_TYPES,
    DocumentParsingError,
    parse_document,
    render_for_prompt,
)
from app.documents.repository import DocumentRepository
from app.documents.storage import LocalFileStorage, Storage
from app.errors import ConflictError, NotFoundError, ValidationError
from app.llm.base import LLMProtocol
from app.runs.enums import MessageRole
from app.users.models import User

logger = logging.getLogger("app.documents.service")

# filetype only recognises binary signatures; text-based formats have none of their
# own, so a declared type is trusted for them, but only once the bytes are confirmed
# to actually decode as text — see _sniff_content_type.
_TEXT_CONTENT_TYPES = frozenset({"text/html", "text/markdown", "text/plain", "text/csv"})


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        storage: Storage | None = None,
        settings: Settings | None = None,
        llm: LLMProtocol | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.storage: Storage = storage or LocalFileStorage(self.settings.documents_storage_path)
        self.repo = DocumentRepository(session)
        self._llm = llm

    async def upload(self, file: UploadFile, owner: User) -> Document:
        data = await file.read()
        if len(data) > self.settings.documents_upload_max_bytes:
            raise ValidationError("That file is larger than this service accepts.")
        content_type = _sniff_content_type(data, file.content_type)
        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise ValidationError(f"Unsupported file type: {content_type or 'unknown'}.")
        document = Document(
            owner_id=owner.id,
            title=file.filename or "Untitled document",
            source_type=DocumentSourceType.upload,
            storage_key=self.storage.new_key(),
            content_type=content_type,
            size_bytes=len(data),
            status=DocumentStatus.pending,
            expires_at=_expiry(self.settings),
        )
        return await self._store_and_parse(document, data, owner)

    async def fetch_from_url(self, url: str, owner: User) -> Document:
        fetched = await fetch_url(url, self.settings)
        document = Document(
            owner_id=owner.id,
            title=_title_from_url(url),
            source_type=DocumentSourceType.url,
            source_url=url,
            storage_key=self.storage.new_key(),
            content_type=fetched.content_type,
            size_bytes=len(fetched.content),
            status=DocumentStatus.pending,
            expires_at=_expiry(self.settings),
        )
        return await self._store_and_parse(document, fetched.content, owner)

    async def get(self, document_id: UUID, owner: User) -> Document:
        return await self._get_or_404(document_id, owner)

    async def list_for_owner(self, owner: User) -> list[Document]:
        return await self.repo.list_for_owner(owner.id)

    async def send_message(self, document_id: UUID, content: str, owner: User) -> Document:
        document = await self._get_or_404(document_id, owner)
        if document.status is not DocumentStatus.ready:
            raise ConflictError("This document is not ready to discuss yet.")

        document.messages.append(DocumentMessage(role=MessageRole.user, content=content))
        await self.session.flush()

        history = [
            {
                "role": "assistant" if m.role is MessageRole.assistant else "user",
                "content": m.content,
            }
            for m in document.messages
        ]
        document_text = render_for_prompt(document.parsed_content or {})
        chat = DocumentChatService(self._llm)
        answer, citations = await chat.reply(document_text, history)

        document.messages.append(
            DocumentMessage(
                role=MessageRole.assistant,
                content=answer,
                citations=[c.model_dump() for c in citations],
            )
        )
        await self.session.commit()
        return await self._get_or_404(document_id, owner)

    async def _store_and_parse(self, document: Document, data: bytes, owner: User) -> Document:
        # Storage and parsing are both blocking I/O/CPU work; offloaded so neither
        # stalls the event loop for other in-flight requests.
        await asyncio.to_thread(self.storage.save, document.storage_key, data)
        self.repo.add(document)
        await self.session.flush()
        document.status = DocumentStatus.parsing
        await self.session.flush()
        try:
            parsed = await asyncio.to_thread(parse_document, document.title, data)
        except DocumentParsingError as exc:
            # A parse failure is not a bug — a corrupt PDF or an unreadable scan is
            # expected input, surfaced on the document rather than raised as a 500.
            document.status = DocumentStatus.failed
            document.error_message = exc.message
            await self.session.commit()
            return await self._get_or_404(document.id, owner)
        document.parsed_content = parsed.content
        document.extraction_quality = parsed.quality
        document.status = DocumentStatus.ready
        await self.session.commit()
        # Reloaded rather than returned in place: `messages` was never touched on this
        # object before commit, so SQLAlchemy has not resolved it as loaded, and the
        # router's synchronous Pydantic serialisation cannot perform the lazy-load
        # itself — the same reason ConductEngine.start_run() re-loads after commit.
        return await self._get_or_404(document.id, owner)

    async def _get_or_404(self, document_id: UUID, owner: User) -> Document:
        document = await self.repo.get(document_id)
        # Someone else's document reads as absent rather than forbidden, so the API
        # can't be used to enumerate which ids exist — same rule as templates.
        if document is None or document.owner_id != owner.id:
            raise NotFoundError("Document not found.")
        return document


def _sniff_content_type(data: bytes, declared: str | None) -> str | None:
    """Identify what was actually uploaded from its bytes — magic bytes, never the
    filename or a client-supplied header alone. An uploaded "report.pdf" that is not
    really a PDF must not reach the parser labelled as one."""
    kind = filetype.guess(data)
    if kind is not None:
        return str(kind.mime)
    # filetype only recognises binary signatures; text formats have none. Confirming
    # the bytes actually decode as text is the check that replaces magic bytes here —
    # a binary payload filetype didn't recognise must not fall through to "it's text".
    try:
        sample = data[:4096].decode("utf-8")
    except UnicodeDecodeError:
        return None
    lowered = sample.lower()
    if "<html" in lowered or "<!doctype html" in lowered:
        return "text/html"
    if declared in _TEXT_CONTENT_TYPES:
        return declared
    return "text/plain"


def _expiry(settings: Settings) -> datetime:
    return datetime.now(UTC) + timedelta(hours=settings.documents_ttl_hours)


def _title_from_url(url: str) -> str:
    path = urlsplit(url).path.rstrip("/")
    if path and "/" in path:
        return path.rsplit("/", 1)[-1]
    return path or url
