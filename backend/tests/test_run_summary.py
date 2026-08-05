"""The AI summary of a completed run.

The summary is creator-facing and acted on, so the tests that matter are the gates
between the model and the stored column — not that a happy path returns a string.
"""

import pytest

from app.conduct.engine import ConductEngine
from app.errors import ConflictError, NotFoundError
from app.llm.base import LLMError, ToolTurn
from app.runs.summary import RunSummaryService
from tests.fakes import FakeLLM, move_on, record

_QUOTE = "we still count stock on paper every Friday"


def _summary(**overrides) -> ToolTurn:
    payload = {
        "headline": "Two years in and still counting stock on paper.",
        "key_facts": ["Works as a line lead", "Weekly stock counts are manual"],
        "notable_quotes": [{"question": "What's your role?", "quote": _QUOTE}],
    }
    payload.update(overrides)
    return ToolTurn(text="", tool_name="summarise_run", tool_input=payload)


def _faithful() -> ToolTurn:
    return ToolTurn(text="", tool_name="report_verdict", tool_input={"faithful": True})


def _unfaithful(*problems: str) -> ToolTurn:
    return ToolTurn(
        text="",
        tool_name="report_verdict",
        tool_input={"faithful": False, "problems": list(problems)},
    )


async def _completed(session, participant, published):
    """A finished two-question run whose first answer contains the quotable sentence."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, participant)
    engine = ConductEngine(session, llm=FakeLLM(record(_QUOTE), move_on()))
    run = await engine.handle_message(run.id, _QUOTE, participant)
    engine = ConductEngine(session, llm=FakeLLM(record(4), move_on()))
    return await engine.handle_message(run.id, "4", participant)


async def test_summarises_a_completed_run_and_stores_it(session, creator, participant, published):
    run = await _completed(session, participant, published)
    llm = FakeLLM(_summary(), _faithful())

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)

    assert content.headline.startswith("Two years in")
    assert content.key_facts == ["Works as a line lead", "Weekly stock counts are manual"]
    assert [q.quote for q in content.notable_quotes] == [_QUOTE]
    await session.refresh(run)
    assert run.summary["headline"] == content.headline
    assert run.summary["prompt_version"] == "summarise_run_v1"
    assert run.summary["verify_prompt_version"] == "verify_summary_v1"
    assert run.summary["generated_at"]


async def test_a_stored_summary_is_not_regenerated(session, creator, participant, published):
    """Generation costs model calls, so the column is the cache — one pass, then none."""
    run = await _completed(session, participant, published)
    llm = FakeLLM(_summary(), _faithful())
    service = RunSummaryService(session, llm=llm)

    first = await service.summarise(published.id, run.id, creator)
    second = await service.summarise(published.id, run.id, creator)

    assert llm.calls == 2  # one draft, one verdict, and nothing for the second read
    assert first == second


async def test_refresh_regenerates_over_a_stored_summary(session, creator, participant, published):
    run = await _completed(session, participant, published)
    llm = FakeLLM(
        _summary(),
        _faithful(),
        _summary(headline="A second look at the same run."),
        _faithful(),
    )
    service = RunSummaryService(session, llm=llm)

    await service.summarise(published.id, run.id, creator)
    again = await service.summarise(published.id, run.id, creator, refresh=True)

    assert llm.calls == 4
    assert again.headline == "A second look at the same run."


async def test_an_unfinished_run_is_refused(session, creator, participant, published):
    """Summarising a half-answered run would describe a response the participant is still
    giving, and would cache that description as if it were final."""
    run = await ConductEngine(session, llm=FakeLLM()).start_run(published.id, participant)
    llm = FakeLLM(_summary())

    with pytest.raises(ConflictError, match="completed"):
        await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)
    assert llm.calls == 0  # refused before spending a model call


async def test_an_invented_quote_is_dropped_but_the_summary_survives(
    session, creator, participant, published
):
    """A quote the participant never said is indistinguishable from a real one once it is
    rendered beside their answers. The rest of the summary is usually sound, so drop the
    quote rather than lose the whole thing."""
    run = await _completed(session, participant, published)
    llm = FakeLLM(
        _summary(
            notable_quotes=[
                {"question": "What's your role?", "quote": _QUOTE},
                {"question": "Rate your onboarding", "quote": "the training was a shambles"},
            ]
        ),
        _faithful(),
    )

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)

    assert [q.quote for q in content.notable_quotes] == [_QUOTE]


async def test_a_quote_reflowed_by_the_model_is_kept(session, creator, participant, published):
    """Models re-wrap long quotes across lines and normalise spacing. That is not
    invention, and matching on raw bytes would throw away every genuine long quote."""
    run = await _completed(session, participant, published)
    reflowed = _QUOTE.replace(" ", "\n  ").upper()
    llm = FakeLLM(_summary(notable_quotes=[{"question": "Q", "quote": reflowed}]), _faithful())

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)

    assert len(content.notable_quotes) == 1


async def test_stringified_lists_from_a_weak_model_are_decoded(
    session, creator, participant, published
):
    """Backup models emit the right list wrapped in a string; that is a serialization
    artifact, not a content problem."""
    run = await _completed(session, participant, published)
    llm = FakeLLM(
        _summary(key_facts='["Works as a line lead", "Counts stock by hand"]'), _faithful()
    )

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)

    assert content.key_facts == ["Works as a line lead", "Counts stock by hand"]


async def test_an_invalid_summary_is_retried_once_then_fails_loudly(
    session, creator, participant, published
):
    run = await _completed(session, participant, published)
    recovers = FakeLLM(_summary(headline="   "), _summary(), _faithful())

    content = await RunSummaryService(session, llm=recovers).summarise(
        published.id, run.id, creator
    )
    assert recovers.calls == 3
    assert content.headline.startswith("Two years in")
    assert "rejected" in recovers.messages_seen[1][-1]["content"]

    stubborn = FakeLLM(_summary(headline=""))
    with pytest.raises(LLMError, match="after one retry"):
        await RunSummaryService(session, llm=stubborn).summarise(
            published.id, run.id, creator, refresh=True
        )


async def test_another_creator_cannot_summarise_someone_elses_run(
    session, creator, other_creator, participant, published
):
    run = await _completed(session, participant, published)
    llm = FakeLLM(_summary())

    with pytest.raises(NotFoundError):
        await RunSummaryService(session, llm=llm).summarise(published.id, run.id, other_creator)
    assert llm.calls == 0


async def test_the_checker_reads_fresh_context(session, creator, participant, published):
    """The checker's turn carries the answers and the candidate, and nothing of how the
    draft was made — not the writer's briefing, not the drafting conversation."""
    run = await _completed(session, participant, published)
    llm = FakeLLM(_summary(), _faithful())

    await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)

    assert llm.offered == [["summarise_run"], ["report_verdict"]]
    (brief,) = llm.messages_seen[1]  # a single user message — no drafting history
    assert _QUOTE in brief["content"]
    assert "Two years in" in brief["content"]
    assert "Summarise it" not in brief["content"]
    assert "You had no part in writing it" in llm.briefings[1]


async def test_an_unsupported_summary_is_redrafted_with_the_checkers_notes(
    session, creator, participant, published
):
    """An unfaithful verdict goes back to the writer through the same channel a schema
    rejection uses, and the redraft is checked again from scratch."""
    run = await _completed(session, participant, published)
    llm = FakeLLM(
        _summary(headline="Promoted to shift manager last spring."),
        _unfaithful("the headline reports a promotion the participant never mentioned"),
        _summary(),
        _faithful(),
    )

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)

    assert content.headline.startswith("Two years in")
    assert llm.calls == 4
    redraft_note = llm.messages_seen[2][-1]["content"]
    assert "rejected" in redraft_note
    assert "promotion" in redraft_note


async def test_a_summary_the_checker_refuses_twice_is_not_stored(
    session, creator, participant, published
):
    """After the one send-back the gate is a hard no: an unsupported summary rendered
    beside the answers is worse than the creator reading the answers themselves."""
    run = await _completed(session, participant, published)
    llm = FakeLLM(
        _summary(),
        _unfaithful("the second fact is not in the answers"),
        _summary(),
        _unfaithful("the second fact is not in the answers"),
    )

    with pytest.raises(LLMError, match="could not be verified"):
        await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)

    await session.refresh(run)
    assert run.summary is None


async def test_a_refusal_without_notes_is_an_invalid_verdict(
    session, creator, participant, published
):
    """'Fail, no reason given' cannot be sent back as notes, so it is rejected as a
    verdict rather than quietly treated as either answer."""
    run = await _completed(session, participant, published)
    llm = FakeLLM(_summary(), _unfaithful())

    with pytest.raises(LLMError, match="invalid verdict"):
        await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)


async def test_a_stringified_problems_list_is_decoded(session, creator, participant, published):
    """The same weak-model serialization slip the summary fields get absorbed for."""
    run = await _completed(session, participant, published)
    stringified = ToolTurn(
        text="",
        tool_name="report_verdict",
        tool_input={"faithful": False, "problems": '["the headline overreaches"]'},
    )
    llm = FakeLLM(_summary(), stringified, _summary(), _faithful())

    content = await RunSummaryService(session, llm=llm).summarise(published.id, run.id, creator)

    assert llm.calls == 4
    assert "overreaches" in llm.messages_seen[2][-1]["content"]
    assert content.headline.startswith("Two years in")
