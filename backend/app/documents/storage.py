"""Where uploaded/fetched document bytes live.

A small seam (``Storage``) rather than calls to the filesystem scattered through the
service — swapping in a real object-store backend later is a new class behind the same
protocol, the same shape as ``OIDCTokenVerifier`` in app/auth/tokens.py, not a rewrite.
"""

from pathlib import Path
from typing import Protocol
from uuid import uuid4


class Storage(Protocol):
    def new_key(self) -> str: ...
    def save(self, key: str, data: bytes) -> None: ...
    def read(self, key: str) -> bytes: ...
    def delete(self, key: str) -> None: ...


class LocalFileStorage:
    """Files on disk under one root directory, keyed by a generated name.

    The key is always a fresh UUID hex string, never the caller's filename — an
    uploaded ``../../etc/passwd`` must not become a path, and two uploads sharing a
    filename must not collide.
    """

    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def new_key(self) -> str:
        return uuid4().hex

    def save(self, key: str, data: bytes) -> None:
        (self.root / key).write_bytes(data)

    def read(self, key: str) -> bytes:
        return (self.root / key).read_bytes()

    def delete(self, key: str) -> None:
        (self.root / key).unlink(missing_ok=True)
