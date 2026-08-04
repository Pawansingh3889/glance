# Translations

Eight languages: English, Polish, Lithuanian, Romanian, Portuguese, Spanish, Latvian,
Bulgarian. Chosen for UK fish and food processing, where a large share of line staff do
not read English comfortably.

## Status: **not reviewed by native speakers**

Every non-English dictionary in `dictionaries/` was produced by an LLM and has had no
human review. That is fine for a demonstration and not fine for a live site.

The safety-critical part of this warning used to be the incident form — its severity
options distinguished "first aid only" from "lost-time injury" from "potentially RIDDOR
reportable", a distinction carrying a legal reporting duty in the UK, where a
plausible-but-wrong translation reads perfectly and is worse than none. That form was
removed from the front end, so the risk with it. What remains worth a native speaker's
eye before real use:

- `ask.disclaimer` — it defers to the site's HACCP plan and safety lead, so a weak
  translation undersells a deliberate limit on the assistant's authority.
- `ask.lede` and `topics.*` — domain vocabulary a food-manufacturing reader will judge.

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
- **Assistant answers** are not translated here at all: the model is asked to answer in
  the chosen language directly, via `ask_fish_factory_v2.md`.
