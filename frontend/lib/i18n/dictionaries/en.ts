/** English — the source dictionary.
 *
 *  Every other locale is typed against `Dictionary`, so adding a key here and forgetting
 *  it elsewhere is a compile error rather than a blank space on a Bulgarian tablet.
 *
 *  `questions` maps the seeded incident template's question ids to translations. Those
 *  ids are fixed in backend/app/sample_data/surveys.json; the form falls back to the
 *  wording the API returned when an id has no entry, which is what happens if someone
 *  republishes the template with new questions.
 */
export const en = {
  nav: {
    build: "Build",
    respond: "Respond",
    report: "Report",
    ask: "Ask",
    signOut: "Sign out",
    signIn: "Sign in",
    home: "Home",
    language: "Language",
  },
  landing: {
    eyebrow: "Food safety · HACCP · Health & safety",
    heroTitle: "Ask the factory floor what the audit will find.",
    heroBody:
      "Conversational food safety and health-and-safety checks for fish processing sites — so problems surface from the people on the line, not from an auditor.",
    reportCta: "Report an incident",
    askCta: "Ask a question",
    staffTitle: "For everyone on shift",
    staffBody: "No account needed. Give your name and go.",
    managerTitle: "For safety and technical leads",
    managerBody: "Sign in with your company Microsoft account to build surveys and read results.",
    managerCta: "Sign in with Microsoft",
    footerNote:
      "A demonstration survey service. Standards named here — HACCP, BRCGS — belong to their respective owners.",
  },
  guest: {
    title: "Your name",
    body: "So the report has a name on it. No account, no password.",
    nameLabel: "Name",
    namePlaceholder: "e.g. Marta K",
    emailLabel: "Email",
    emailOptional: "Optional",
    emailHelp: "Only so someone can come back to you about this. Leave it blank if you prefer.",
    submit: "Continue",
    submitting: "Just a moment…",
    nameRequired: "Please give a name.",
    back: "Back to home",
  },
  sso: {
    title: "Sign in",
    body: "Survey authors and safety leads sign in with their company Microsoft account.",
    button: "Sign in with Microsoft",
    unavailable:
      "Company sign-in is not configured on this deployment yet. Ask your administrator to set AUTH_PROVIDER=oidc.",
    notYou: "Not an author? You do not need to sign in to report an incident or answer a survey.",
  },
  report: {
    title: "Report an incident",
    lede: "An injury, a near miss, or something unsafe you have seen.",
    urgent: "If someone is hurt right now, get the first aider before you fill this in.",
    optional: "Optional",
    submit: "File this report",
    submitting: "Filing…",
    remaining_one: "{n} question still to answer",
    remaining_other: "{n} questions still to answer",
    filedTitle: "Report filed",
    filedRef: "Reference",
    filedNote: "Quote this reference if someone asks about it. Your safety lead can see it now.",
    another: "File another",
    askInstead: "Ask a question instead",
    writeIn: "Where was it?",
    yes: "Yes",
    no: "No",
    freeText: "In your own words…",
  },
  ask: {
    title: "Ask about the factory",
    lede: "Food safety, HACCP, fish handling, cold chain, hygiene and health and safety.",
    disclaimer:
      "Answers are general industry guidance. Your site's HACCP plan and your safety lead come first.",
    placeholder: "e.g. How long can fish sit out during a line stoppage?",
    send: "Ask",
    thinking: "Thinking…",
    pending: "Working it out — this can take up to a minute.",
    hint: "Enter to send · Shift + Enter for a new line",
    tryTitle: "Try one of these",
    offTopic: "Off topic",
    reportPrompt: "Something happened on shift?",
    reportLink: "File an incident report",
    reportPromptEnd: "rather than only asking here.",
    examples: [
      "What temperature should chilled fish be held at?",
      "How often should the metal detector be verified?",
      "When does a near miss have to be reported?",
      "What is a critical control point, in plain English?",
    ],
  },
  topics: {
    haccp: "HACCP",
    fish_handling: "Fish handling",
    cold_chain: "Cold chain",
    hygiene: "Hygiene",
    allergens: "Allergens",
    health_and_safety: "Health & safety",
    audits: "Audits",
    out_of_scope: "Off topic",
  },
  common: {
    loading: "Loading…",
    somethingWrong: "Something went wrong.",
  },
  /** Incident question ids → wording. Empty here on purpose: the API already returns
   *  English, so there is nothing to override. The other locales fill these. */
  questions: {} as Record<string, string>,
  /** Incident select options → wording, keyed by the English option text the API
   *  returns, because options carry no ids of their own. Empty here for the same reason. */
  options: {} as Record<string, string>,
};

export type Dictionary = typeof en;
