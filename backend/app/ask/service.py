"""Answering shop-floor questions about the factory.

Read-only and stateless: nothing here touches the database. The model is constrained to
a tool schema and its reply is validated before it leaves the service, so a malformed
answer fails loudly with a 503 rather than reaching the floor as prose.
"""

import logging
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from app.ask.schemas import LANGUAGE_NAMES, AnswerLanguage, AskAnswer, AskTopic
from app.llm.base import LLMError, LLMProtocol
from app.llm.factory import get_llm
from app.llm.prompts import load_prompt

logger = logging.getLogger("app.ask.service")

_TOOL_NAME = "answer_question"
_TOOL_DESCRIPTION = (
    "Answer a factory worker's question about food safety, fish handling or health and "
    "safety, or decline it as out of scope."
)
_TOOL_SCHEMA: dict[str, Any] = AskAnswer.model_json_schema()


class AskService:
    def __init__(self, llm: LLMProtocol | None = None) -> None:
        self.llm: LLMProtocol = llm or get_llm()

    async def ask(self, question: str, language: AnswerLanguage = AnswerLanguage.en) -> AskAnswer:
        system = load_prompt("ask_fish_factory_v2", LANGUAGE=LANGUAGE_NAMES[language])
        raw = await self.llm.tool_call(
            system=system,
            prompt=question,
            tool_name=_TOOL_NAME,
            tool_description=_TOOL_DESCRIPTION,
            input_schema=_TOOL_SCHEMA,
            max_tokens=1024,
        )
        try:
            answer = AskAnswer.model_validate(raw)
        except PydanticValidationError as exc:
            # Keep the payload: the validation error says what was wrong with the shape
            # but not what the model actually sent.
            logger.error("ask answer rejected: raw=%r error=%s", raw, exc)
            raise LLMError(f"Model returned an invalid answer: {exc}") from exc

        # A model that flags a question out of scope but still labels it with a subject
        # has half-followed the instruction. The flag is the decision the UI acts on, so
        # make the topic agree with it rather than leaving the two contradicting.
        if not answer.in_scope and answer.topic is not AskTopic.out_of_scope:
            answer = answer.model_copy(update={"topic": AskTopic.out_of_scope})
        return answer
