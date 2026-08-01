"""Document and document-message queries."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.documents.models import Document, DocumentMessage


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, document: Document) -> None:
        self.session.add(document)

    def add_message(self, message: DocumentMessage) -> None:
        self.session.add(message)

    async def get(self, document_id: UUID) -> Document | None:
        stmt = (
            select(Document)
            .where(Document.id == document_id)
            .options(selectinload(Document.messages))
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_owner(self, owner_id: UUID) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def expired_before(self, cutoff: datetime) -> list[Document]:
        """Powers the TTL sweep in cleanup.py — never read from a request path."""
        stmt = select(Document).where(Document.expires_at < cutoff)
        return list((await self.session.execute(stmt)).scalars().all())

    async def delete(self, document: Document) -> None:
        await self.session.delete(document)
