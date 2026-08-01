"""Controlled vocabularies for the document-chat session path."""

import enum


class DocumentSourceType(str, enum.Enum):
    upload = "upload"
    url = "url"


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    parsing = "parsing"
    ready = "ready"
    failed = "failed"
