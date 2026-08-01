"""Document and document-chat-message models.

A document is scoped to its uploading owner and TTL-expires — it never joins any
controlled knowledge base. See app/documents/service.py for the pipeline that creates
these rows, app/documents/cleanup.py for the TTL sweep.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.documents.enums import DocumentSourceType, DocumentStatus
from app.runs.enums import MessageRole


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(300))
    source_type: Mapped[DocumentSourceType] = mapped_column(
        SAEnum(DocumentSourceType, name="document_source_type")
    )
    source_url: Mapped[str | None] = mapped_column(Text, default=None)
    storage_key: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(127))
    size_bytes: Mapped[int] = mapped_column(Integer)
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus, name="document_status"), default=DocumentStatus.pending
    )
    # Docling's per-element confidence where available, else a coarse heuristic — never
    # invented. See app/documents/parsing.py.
    extraction_quality: Mapped[float | None] = mapped_column(Float, default=None)
    # Structured extraction: sections, tables, page map. None until parsing finishes.
    parsed_content: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # TTL: the session store's expiry. Cleanup deletes the row and its storage object
    # once past this, never before — see app/documents/cleanup.py.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list["DocumentMessage"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentMessage.created_at",
    )


class DocumentMessage(Base):
    __tablename__ = "document_messages"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole, name="message_role"))
    content: Mapped[str] = mapped_column(Text)
    # [{"quote": ..., "page": ..., "section": ...}, ...] — empty when the answer cites
    # nothing (e.g. a refusal).
    citations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    # Client-side for the same reason as RunMessage.created_at: a question and its
    # answer written within one transaction would otherwise tie under Postgres's
    # transaction-time now().
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=lambda: datetime.now(UTC)
    )

    document: Mapped["Document"] = relationship(back_populates="messages")
