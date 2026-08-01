"""Document routes. Thin: resolve the caller, call one service method, shape output.

Uses ``get_current_user`` directly, not ``require_creator``/``require_participant`` —
discussing a document is a general capability orthogonal to survey roles, available to
any signed-in account, scoped to what that account itself uploaded or fetched.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED

from app.auth.dependencies import get_current_user
from app.db.session import get_session
from app.documents.schemas import (
    ChatMessageRequest,
    DocumentRead,
    DocumentSummary,
    FetchUrlRequest,
)
from app.documents.service import DocumentService
from app.users.models import User

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("", response_model=DocumentRead, status_code=HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    document = await DocumentService(session).upload(file, user)
    return DocumentRead.model_validate(document)


@router.post("/fetch", response_model=DocumentRead, status_code=HTTP_201_CREATED)
async def fetch_document(
    data: FetchUrlRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    document = await DocumentService(session).fetch_from_url(data.url, user)
    return DocumentRead.model_validate(document)


# Declared before /{document_id} so the literal path is never parsed as a document id.
@router.get("", response_model=list[DocumentSummary])
async def list_documents(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[DocumentSummary]:
    documents = await DocumentService(session).list_for_owner(user)
    return [DocumentSummary.model_validate(d) for d in documents]


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    document = await DocumentService(session).get(document_id, user)
    return DocumentRead.model_validate(document)


@router.post("/{document_id}/messages", response_model=DocumentRead)
async def post_message(
    document_id: UUID,
    data: ChatMessageRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DocumentRead:
    document = await DocumentService(session).send_message(document_id, data.content, user)
    return DocumentRead.model_validate(document)
