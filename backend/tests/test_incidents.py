"""Filing a health-and-safety incident report.

A report is a completed run against the published incident template, written directly
rather than driven through the conduct engine. These tests hold that path to the same
rules the conversational one obeys: nothing invalid is stored, required questions are
required, and the result is a run the existing results paths can read.
"""

from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.errors import NotFoundError, ValidationError
from app.incidents.schemas import IncidentAnswerIn
from app.incidents.service import INCIDENT_TEMPLATE_ID, IncidentService
from app.runs.enums import AnswerKind, RunStatus
from app.runs.models import SurveyRun
from app.sample_data.loader import load_sample_data
from app.seed import SEED_USERS
from app.users.models import User

# Keyed by the question's position in the published form, so a reworded question does not
# break every test here — only a reordered or retyped one, which should break them.
FILLED = {
    0: "2026-07-29",
    1: "Filleting",
    2: "Near miss",
    3: "First aid only",
    4: "A tote slid off the wet bench and landed next to an operative's foot.",
    5: ["Cut-resistant gloves", "Wellingtons / non-slip footwear"],
    6: True,
    7: "Bench cleared and the floor squeegeed; line leader told straight away.",
    8: "A lip on the bench edge would stop totes sliding when it is wet.",
}


@pytest_asyncio.fixture
async def reporter(session) -> User:
    for uid, email, name, role in SEED_USERS:
        session.add(User(id=uid, email=email, display_name=name, role=role))
    await session.flush()
    await load_sample_data(session)
    return await session.get(User, UUID("00000000-0000-0000-0000-0000000000a1"))


async def _submission(
    svc: IncidentService, overrides: dict[int, object] | None = None, drop: set[int] | None = None
) -> list[IncidentAnswerIn]:
    form = await svc.form()
    values = {**FILLED, **(overrides or {})}
    return [
        IncidentAnswerIn(question_id=q.id, value=values[q.position])
        for q in form.questions
        if q.position in values and q.position not in (drop or set())
    ]


async def test_the_form_comes_from_the_published_version(session, reporter):
    form = await IncidentService(session).form()

    assert form.template_id == INCIDENT_TEMPLATE_ID
    assert [q.position for q in form.questions] == list(range(9))
    assert form.questions[0].answer_type == "date"
    assert form.questions[6].answer_type == "yes_no"
    # The select options are the template's, not a hardcoded list in the frontend.
    assert "Filleting" in form.questions[1].options


async def test_a_filed_report_is_a_completed_run(session, reporter):
    svc = IncidentService(session)
    receipt = await svc.submit(await _submission(svc), reporter)

    run = await session.get(SurveyRun, receipt.run_id)
    assert run is not None
    assert run.status is RunStatus.completed
    assert run.completed_at is not None
    assert len(run.answers) == 9
    assert {a.kind for a in run.answers} == {AnswerKind.scripted}


async def test_answers_are_stored_in_the_engines_own_shape(session, reporter):
    """A form answer and a conversational one must be indistinguishable downstream —
    the results and export paths read one shape, not two."""
    svc = IncidentService(session)
    receipt = await svc.submit(await _submission(svc), reporter)

    run = await session.get(SurveyRun, receipt.run_id)
    by_text = {a.question_text: a.value for a in run.answers}
    assert by_text["When did it happen?"] == {"date": "2026-07-29"}
    assert by_text["Which area or line was it in?"] == {"option": "Filleting"}
    assert by_text["Was anyone hurt?"] == {"yes_no": True}
    assert by_text["What PPE was being worn at the time?"] == {
        "options": ["Cut-resistant gloves", "Wellingtons / non-slip footwear"]
    }


async def test_the_receipt_reference_is_readable(session, reporter):
    svc = IncidentService(session)
    receipt = await svc.submit(await _submission(svc), reporter)

    assert receipt.reference == str(receipt.run_id).split("-", 1)[0].upper()
    assert len(receipt.reference) == 8


async def test_a_missing_required_answer_is_refused(session, reporter):
    svc = IncidentService(session)
    with pytest.raises(ValidationError, match="required"):
        await svc.submit(await _submission(svc, drop={4}), reporter)


async def test_an_optional_answer_may_be_left_out(session, reporter):
    """Position 8 ("what would stop this happening again") is the only optional field."""
    svc = IncidentService(session)
    receipt = await svc.submit(await _submission(svc, drop={8}), reporter)

    run = await session.get(SurveyRun, receipt.run_id)
    assert len(run.answers) == 8
    # Left out entirely rather than stored as an empty answer.
    assert all("stop this happening" not in a.question_text for a in run.answers)


@pytest.mark.parametrize(
    "position,bad",
    [
        (0, "29/07/2026"),  # date in the wrong format
        (2, "Something else entirely"),  # not an option, and this one forbids write-ins
        (6, "probably"),  # not a boolean
        (5, "Cut-resistant gloves"),  # multi_select given a bare string
        (4, "   "),  # required text that is only whitespace
    ],
)
async def test_a_value_that_fails_the_answer_gate_is_refused(session, reporter, position, bad):
    svc = IncidentService(session)
    with pytest.raises(ValidationError):
        await svc.submit(await _submission(svc, overrides={position: bad}), reporter)


async def test_the_area_question_accepts_a_write_in(session, reporter):
    """Area is the one select with allow_other set: a site will always have a corner the
    fixed list does not name, and forcing it into "Packing" would lose where it happened.
    The controlled lists — event kind, severity — stay closed so they aggregate."""
    svc = IncidentService(session)
    receipt = await svc.submit(await _submission(svc, overrides={1: "Bridge deck"}), reporter)

    run = await session.get(SurveyRun, receipt.run_id)
    by_text = {a.question_text: a.value for a in run.answers}
    assert by_text["Which area or line was it in?"] == {"other": "Bridge deck"}


async def test_nothing_is_written_when_a_value_is_refused(session, reporter):
    """The whole report is one transaction: a bad field must not leave a half-filed run."""
    svc = IncidentService(session)
    before = len((await session.execute(select(SurveyRun))).all())
    with pytest.raises(ValidationError):
        await svc.submit(await _submission(svc, overrides={6: "probably"}), reporter)
    after = len((await session.execute(select(SurveyRun))).all())
    assert after == before


async def test_an_unknown_question_id_is_refused(session, reporter):
    svc = IncidentService(session)
    answers = await _submission(svc)
    answers.append(IncidentAnswerIn(question_id=uuid4(), value="smuggled in"))

    with pytest.raises(ValidationError, match="Unknown question"):
        await svc.submit(answers, reporter)


async def test_an_unseeded_database_says_so(session):
    """No fallbacks: without the template there is no form, and the caller is told why
    rather than handed an empty one."""
    with pytest.raises(NotFoundError, match="not published"):
        await IncidentService(session).form()
