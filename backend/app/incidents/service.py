"""Filing a health-and-safety incident report.

A report is a completed run against the published incident template, so everything the
results and export paths already do — per-question aggregation, CSV, the run detail
view — works on incidents with no special case.

What it deliberately does *not* do is go through the conduct engine. That engine spends
one LLM call per message to decide what to ask next, which is right for a conversation
and wrong for a form the reporter has already filled in: a nine-field report would cost
nine model calls and minutes of waiting to arrive at answers the reporter had typed
before the first call was made. The fields are still validated through the engine's own
``validate_answer`` gate, so a form answer and a conversational one are held to
identical rules and land in identical shapes.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.conduct.validation import AnswerValidationError, validate_answer
from app.errors import NotFoundError, ValidationError
from app.incidents.repository import IncidentRepository
from app.incidents.schemas import (
    IncidentAnswerIn,
    IncidentForm,
    IncidentQuestion,
    IncidentReceipt,
)
from app.runs.enums import AnswerKind, RunStatus
from app.runs.models import Answer, SurveyRun
from app.users.models import User

logger = logging.getLogger("app.incidents.service")

# The seeded "Health and Safety Incident Report" template. A fixed id rather than a
# title lookup: titles are editable in the builder, and an incident form that silently
# stops resolving because someone renamed a template is exactly the failure this
# codebase's no-fallbacks rule exists to prevent.
INCIDENT_TEMPLATE_ID = UUID("a8439cef-cc17-5c28-b1cc-6c0cd0948cf3")


class IncidentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = IncidentRepository(session)

    async def _definition(self) -> tuple[UUID, dict[str, Any]]:
        version = await self.repo.latest_version(INCIDENT_TEMPLATE_ID)
        if version is None:
            raise NotFoundError(
                "The health and safety incident template is not published on this "
                "database. Seed the sample data to install it."
            )
        return version.id, dict(version.definition)

    async def form(self) -> IncidentForm:
        version_id, definition = await self._definition()
        questions = sorted(definition["questions"], key=lambda q: q["position"])
        return IncidentForm(
            template_id=INCIDENT_TEMPLATE_ID,
            version_id=version_id,
            title=definition["title"],
            description=definition.get("description"),
            questions=[
                IncidentQuestion(
                    id=UUID(q["id"]),
                    position=q["position"],
                    text=q["text"],
                    answer_type=q["answer_type"],
                    options=q["options"],
                    allow_other=q["allow_other"],
                    required=q["required"],
                )
                for q in questions
            ],
        )

    async def submit(self, submitted: list[IncidentAnswerIn], reporter: User) -> IncidentReceipt:
        version_id, definition = await self._definition()
        by_id = {q["id"]: q for q in definition["questions"]}

        supplied = {str(a.question_id): a.value for a in submitted}
        unknown = sorted(set(supplied) - set(by_id))
        if unknown:
            raise ValidationError(f"Unknown question ids for this form: {unknown}")

        missing = sorted(
            q["text"] for qid, q in by_id.items() if q["required"] and qid not in supplied
        )
        if missing:
            raise ValidationError(f"These questions are required: {missing}")

        now = datetime.now(UTC)
        run = SurveyRun(
            template_version_id=version_id,
            participant_id=reporter.id,
            status=RunStatus.completed,
            # Every question is accounted for, so the run is finished on arrival: there
            # is no current question for a form that was submitted whole.
            current_question_index=len(by_id),
            probes_asked={},
            started_at=now,
            completed_at=now,
        )

        for qid, question in sorted(by_id.items(), key=lambda kv: kv[1]["position"]):
            if qid not in supplied:
                continue  # optional and left blank: record nothing rather than a null
            try:
                value = validate_answer(question, supplied[qid])
            except AnswerValidationError as exc:
                raise ValidationError(f"{question['text']}: {exc}") from exc
            run.answers.append(
                Answer(
                    question_id=UUID(qid),
                    kind=AnswerKind.scripted,
                    question_text=question["text"],
                    value=value,
                    answered_by=reporter.id,
                    answered_at=now,
                )
            )

        self.repo.add(run)
        await self.session.commit()
        logger.info("incident filed run=%s answers=%d by=%s", run.id, len(run.answers), reporter.id)
        return IncidentReceipt(
            run_id=run.id,
            reference=str(run.id).split("-", 1)[0].upper(),
            submitted_at=now,
        )
