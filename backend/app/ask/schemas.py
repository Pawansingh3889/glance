"""Request and response bodies for the shop-floor question service."""

from enum import StrEnum

from pydantic import BaseModel, Field


class AskTopic(StrEnum):
    """The subject areas the assistant covers. ``out_of_scope`` is not a subject — it is
    what the model returns when the question is not about the factory at all."""

    haccp = "haccp"
    fish_handling = "fish_handling"
    cold_chain = "cold_chain"
    hygiene = "hygiene"
    allergens = "allergens"
    health_and_safety = "health_and_safety"
    audits = "audits"
    out_of_scope = "out_of_scope"


class AnswerLanguage(StrEnum):
    """The languages the floor is answered in.

    Chosen for UK fish and food processing, where a large part of the workforce does not
    read English comfortably. The value is the ISO 639-1 code the frontend already uses
    for its own strings, so one setting drives both.
    """

    en = "en"
    pl = "pl"
    lt = "lt"
    ro = "ro"
    pt = "pt"
    es = "es"
    lv = "lv"
    bg = "bg"


# What to call each language *in the prompt*. Naming it in its own language as well as in
# English measurably reduces the chance a model answers in the wrong one.
LANGUAGE_NAMES: dict[AnswerLanguage, str] = {
    AnswerLanguage.en: "English",
    AnswerLanguage.pl: "Polish (polski)",
    AnswerLanguage.lt: "Lithuanian (lietuvių)",
    AnswerLanguage.ro: "Romanian (română)",
    AnswerLanguage.pt: "Portuguese (português)",
    AnswerLanguage.es: "Spanish (español)",
    AnswerLanguage.lv: "Latvian (latviešu)",
    AnswerLanguage.bg: "Bulgarian (български)",
}


class AskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=600,
        description="A question about food safety, fish handling or health and safety.",
    )
    language: AnswerLanguage = Field(
        default=AnswerLanguage.en,
        description="Language to answer in. Defaults to English when the caller says nothing.",
    )


class AskAnswer(BaseModel):
    """The model's structured reply. This is the tool schema the LLM is constrained to,
    and — unchanged — the response body, so there is no second shape to keep in step."""

    answer: str = Field(
        min_length=1,
        description="The answer, written for someone on the line. Two or three short "
        "paragraphs at most.",
    )
    topic: AskTopic = Field(description="Which subject area the question falls under.")
    in_scope: bool = Field(
        description="False when the question is not about food safety, fish processing "
        "or factory health and safety."
    )
    caveat: str | None = Field(
        default=None,
        description="One sentence on what the answer depends on — jurisdiction, species, "
        "or the site's own HACCP plan. Null when nothing material qualifies it.",
    )
