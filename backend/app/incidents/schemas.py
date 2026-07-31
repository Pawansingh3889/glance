"""Request and response bodies for the health-and-safety incident form."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.templates.enums import AnswerType


class IncidentQuestion(BaseModel):
    """One field, as the published version defines it. The form is rendered from this
    rather than from a hardcoded list, so re-publishing the template changes the form."""

    id: UUID
    position: int
    text: str
    answer_type: AnswerType
    options: list[str]
    allow_other: bool
    required: bool


class IncidentForm(BaseModel):
    template_id: UUID
    version_id: UUID
    title: str
    description: str | None
    questions: list[IncidentQuestion]


class IncidentAnswerIn(BaseModel):
    question_id: UUID
    # Deliberately untyped here: what counts as valid depends on the question's answer
    # type, which only the published version knows. The service validates it through the
    # same gate the conduct engine uses, so a typed union here would be a second,
    # divergent source of truth.
    value: Any


class IncidentSubmission(BaseModel):
    answers: list[IncidentAnswerIn] = Field(min_length=1)


class IncidentReceipt(BaseModel):
    """What the reporter is shown after filing. The reference is the run id's first
    block, which is short enough to read down a radio and still unique on site."""

    run_id: UUID
    reference: str
    submitted_at: datetime
