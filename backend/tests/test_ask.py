"""The shop-floor question service.

Everything here runs against a scripted model: the point of the tests is the service's
own gate — that a malformed answer never reaches the caller, and that the in_scope flag
and the topic can never contradict each other.
"""

import pytest

from app.ask.schemas import LANGUAGE_NAMES, AnswerLanguage, AskAnswer, AskTopic
from app.ask.service import AskService
from app.llm.base import LLMError
from tests.fakes import FakeOneShotLLM

GOOD = {
    "answer": "Chilled fish should be held on ice as close to 0 °C as you can keep it.",
    "topic": "cold_chain",
    "in_scope": True,
    "caveat": "Your site's HACCP plan sets the critical limit that actually applies.",
}


async def test_a_valid_answer_comes_back_whole():
    llm = FakeOneShotLLM(GOOD)
    answer = await AskService(llm).ask("What temperature should chilled fish be held at?")

    assert isinstance(answer, AskAnswer)
    assert answer.topic is AskTopic.cold_chain
    assert answer.in_scope is True
    assert answer.caveat is not None


async def test_the_question_is_what_reaches_the_model():
    llm = FakeOneShotLLM(GOOD)
    await AskService(llm).ask("How often must I verify the metal detector?")

    assert llm.prompts == ["How often must I verify the metal detector?"]
    # The subject-matter briefing is a prompt file, not an inline literal.
    assert "HACCP" in llm.systems[0]


async def test_the_tool_schema_is_the_response_model():
    """The model is constrained to exactly the shape the endpoint returns, so there is no
    second schema that can drift out of step with it."""
    llm = FakeOneShotLLM(GOOD)
    await AskService(llm).ask("What is a critical control point?")

    assert set(llm.schemas[0]["properties"]) == set(AskAnswer.model_fields)


async def test_an_out_of_scope_answer_cannot_keep_a_subject_topic():
    """A model that declines the question but still tags it with a subject has
    half-followed its instruction; the flag is what the UI branches on, so the topic is
    made to agree rather than left contradicting it."""
    llm = FakeOneShotLLM({**GOOD, "in_scope": False, "topic": "cold_chain"})
    answer = await AskService(llm).ask("Who won the league?")

    assert answer.in_scope is False
    assert answer.topic is AskTopic.out_of_scope


async def test_an_out_of_scope_answer_already_tagged_is_left_alone():
    llm = FakeOneShotLLM({**GOOD, "in_scope": False, "topic": "out_of_scope"})
    answer = await AskService(llm).ask("Who won the league?")

    assert answer.topic is AskTopic.out_of_scope


@pytest.mark.parametrize(
    "payload",
    [
        {"topic": "haccp", "in_scope": True},  # no answer at all
        {"answer": "", "topic": "haccp", "in_scope": True},  # empty answer
        {"answer": "Fine.", "topic": "astrology", "in_scope": True},  # topic off the enum
        {"answer": "Fine.", "topic": "haccp"},  # no in_scope flag
    ],
)
async def test_a_malformed_answer_fails_loudly(payload):
    """No partial credit: an answer that does not validate is an LLM failure, not
    something to patch up and serve."""
    llm = FakeOneShotLLM(payload)
    with pytest.raises(LLMError):
        await AskService(llm).ask("What is a critical control point?")


async def test_a_provider_failure_propagates():
    llm = FakeOneShotLLM(LLMError("every tier failed"))
    with pytest.raises(LLMError):
        await AskService(llm).ask("What is a critical control point?")


async def test_a_null_caveat_is_allowed():
    llm = FakeOneShotLLM({**GOOD, "caveat": None})
    answer = await AskService(llm).ask("What is a critical control point?")

    assert answer.caveat is None


# ------------------------------------------------------------------ language


async def test_english_is_the_default():
    llm = FakeOneShotLLM(GOOD)
    await AskService(llm).ask("What is a critical control point?")

    assert "English" in llm.systems[0]


@pytest.mark.parametrize(
    "language,expected",
    [
        (AnswerLanguage.pl, "Polish"),
        (AnswerLanguage.lt, "Lithuanian"),
        (AnswerLanguage.ro, "Romanian"),
        (AnswerLanguage.bg, "Bulgarian"),
    ],
)
async def test_the_requested_language_reaches_the_prompt(language, expected):
    llm = FakeOneShotLLM(GOOD)
    await AskService(llm).ask("Jaka jest temperatura?", language)

    assert expected in llm.systems[0]


async def test_no_placeholder_survives_into_the_prompt():
    """An unfilled {{LANGUAGE}} would still produce a fluent answer — in the wrong
    language — which is exactly the kind of failure that hides."""
    llm = FakeOneShotLLM(GOOD)
    await AskService(llm).ask("What is a CCP?", AnswerLanguage.es)

    assert "{{" not in llm.systems[0]


async def test_every_language_has_a_name():
    """A missing entry would raise KeyError at request time rather than at import."""
    assert set(LANGUAGE_NAMES) == set(AnswerLanguage)
