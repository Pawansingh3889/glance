"""TTL sweep for expired session documents.

Run with ``python -m app.documents.cleanup``. Idempotent — deletes only rows already
past ``expires_at``, and each row's storage object along with it, so a document never
outlives the promise its TTL made in the UI. Not run automatically: there is no
scheduler in this codebase, so this is a cron entry for whoever operates a deployment,
the same manual-step role ``python -m app.seed`` plays in development.
"""

import asyncio
from datetime import UTC, datetime

from app.config import get_settings
from app.db.session import SessionFactory
from app.documents.repository import DocumentRepository
from app.documents.storage import LocalFileStorage, Storage


async def cleanup(storage: Storage | None = None) -> int:
    settings = get_settings()
    store = storage or LocalFileStorage(settings.documents_storage_path)
    async with SessionFactory() as session:
        repo = DocumentRepository(session)
        expired = await repo.expired_before(datetime.now(UTC))
        for document in expired:
            # Storage first: an orphaned file with no row is a rounding error the next
            # sweep can't even find; a row with no file is a broken document.
            store.delete(document.storage_key)
            await repo.delete(document)
        await session.commit()
    return len(expired)


if __name__ == "__main__":
    count = asyncio.run(cleanup())
    print(f"Deleted {count} expired document(s).")
