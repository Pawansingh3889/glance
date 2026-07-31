# Translations

Eight languages: English, Polish, Lithuanian, Romanian, Portuguese, Spanish, Latvian,
Bulgarian. Chosen for UK fish and food processing, where a large share of line staff do
not read English comfortably.

## Status: **not reviewed by native speakers**

Every non-English dictionary in `dictionaries/` was produced by an LLM and has had no
human review. That is fine for a demonstration and **not fine for a live site**, for one
specific reason:

> The incident form is safety-critical. `report.urgent` tells someone to fetch the first
> aider before filling anything in. The severity options distinguish "first aid only"
> from "lost-time injury" from "potentially RIDDOR reportable" — a distinction that
> carries a legal reporting duty in the UK. A plausible-but-wrong translation of any of
> these reads perfectly and is worse than no translation at all, because nobody will
> notice it is wrong.

Before this is used on a real site, have a native speaker who knows food-manufacturing
vocabulary review, at minimum:

- `report.*` — the whole section, especially `urgent`
- `questions` and `options` — the form itself
- `ask.disclaimer` — it defers to the site's HACCP plan and safety lead

Terms of art (**HACCP**, **CCP**, **BRCGS**, **PPE**, **RIDDOR**) are left in English on
purpose. They appear that way on the site's own signage, labels and audit paperwork, so
translating them would break the link between the form and the documents it feeds.
The Spanish dictionary uses **APPCC** for HACCP, which is the form actually used in Spain.

## Adding a language

1. Add the code to `LOCALES` in `locales.ts` and a name to `LOCALE_NAMES` — in that
   language, not in English.
2. Add the same code to `AnswerLanguage` and `LANGUAGE_NAMES` in
   `backend/app/ask/schemas.py`, or the assistant will keep answering in English.
3. Copy `dictionaries/en.ts`, translate, and register it in `DICTIONARIES` in `index.tsx`.

`Dictionary` is derived from the English file, so a missing key is a TypeScript error
rather than a blank space on somebody's tablet. Extra keys are an error too.

## What is not translated

- **Survey content authors write.** A survey's questions are the author's words, stored
  in the published version; translating them would mean translating user data.
- **Incident questions after a republish.** `questions` is keyed by the seeded template's
  fixed UUIDs (see `incidentKeys.ts`). Republish the template with new questions and the
  form falls back to the API's English wording — visibly untranslated rather than wrong.
- **Assistant answers** are not translated here at all: the model is asked to answer in
  the chosen language directly, via `ask_fish_factory_v2.md`.
