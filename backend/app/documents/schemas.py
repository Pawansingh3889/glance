"""Request and response schemas for the document-chat session path."""

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.documents.enums import DocumentSourceType, DocumentStatus
from app.runs.enums import MessageRole


class FetchUrlRequest(BaseModel):
    url: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class ChatMessageRequest(BaseModel):
    # strip_whitespace makes "   " fail min_length: a blank message must 422 here, not
    # reach the model and burn a turn on nothing — same reasoning as RunMessageRequest.
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]


class CitationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    quote: str
    page: int | None
    section: str | None


class DocumentMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    content: str
    citations: list[CitationRead]
    created_at: datetime


class DocumentSummary(BaseModel):
    """The list view — no parsed content, so listing stays cheap."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source_type: DocumentSourceType
    status: DocumentStatus
    created_at: datetime
    expires_at: datetime


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source_type: DocumentSourceType
    source_url: str | None
    content_type: str
    status: DocumentStatus
    extraction_quality: float | None
    parsed_content: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    expires_at: datetime
    messages: list[DocumentMessageRead]
