/** English — the source dictionary.
 *
 *  Every other locale is typed against `Dictionary`, so adding a key here and forgetting
 *  it elsewhere is a compile error rather than a blank space on a Bulgarian tablet.
 */
export const en = {
  nav: {
    build: "Build",
    respond: "Respond",
    ask: "Ask",
    signOut: "Sign out",
    signIn: "Sign in",
    home: "Home",
    language: "Language",
  },
  landing: {
    eyebrow: "Conversational · Multilingual · Embeddable",
    heroTitle: "Ask like a person, not a form.",
    heroBody:
      "Describe the survey you want and Glance drafts it. People answer in a conversation, on any device, in their own language.",
    respondCta: "Answer a survey",
    askCta: "Ask a question",
    staffTitle: "For everyone answering",
    staffBody: "No account needed. Give your name and go.",
    managerTitle: "For survey authors",
    managerBody: "Sign in with your company Microsoft account to build surveys and read results.",
    managerCta: "Sign in with Microsoft",
    footerNote: "A demonstration survey service.",
  },
  guest: {
    title: "Your name",
    body: "So the answers have a name on them. No account, no password.",
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
    body: "Survey authors sign in with their company Microsoft account.",
    button: "Sign in with Microsoft",
    unavailable:
      "Company sign-in is not configured on this deployment yet. Ask your administrator to set AUTH_PROVIDER=oidc.",
    notYou: "Not an author? You do not need to sign in to answer a survey.",
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
};

export type Dictionary = typeof en;
