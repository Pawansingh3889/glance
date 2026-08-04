import type { Dictionary } from "./en";

/** Romanian. See TRANSLATIONS.md — not reviewed by a native speaker. */
export const ro: Dictionary = {
  nav: {
    build: "Creează",
    respond: "Răspunde",
    ask: "Întreabă",
    signOut: "Deconectare",
    signIn: "Conectare",
    home: "Acasă",
    language: "Limbă",
  },
  landing: {
    eyebrow: "Conversațional · Multilingv · Integrabil",
    heroTitle: "Întreabă ca un om, nu ca un formular.",
    heroBody:
      "Descrie chestionarul dorit și Glance îl redactează. Oamenii răspund într-o conversație, pe orice dispozitiv și în limba lor.",
    respondCta: "Completează un chestionar",
    askCta: "Pune o întrebare",
    staffTitle: "Pentru toți cei care răspund",
    staffBody: "Nu ai nevoie de cont. Spune-ți numele și mergi mai departe.",
    managerTitle: "Pentru autorii de chestionare",
    managerBody:
      "Conectează-te cu contul Microsoft al companiei pentru a crea chestionare și a vedea rezultatele.",
    managerCta: "Conectare cu Microsoft",
    footerNote: "Serviciu demonstrativ de chestionare.",
  },
  guest: {
    title: "Numele tău",
    body: "Ca răspunsurile să aibă un nume. Fără cont, fără parolă.",
    nameLabel: "Nume",
    namePlaceholder: "ex. Marta K",
    emailLabel: "E-mail",
    emailOptional: "Opțional",
    emailHelp: "Doar ca cineva să te poată contacta în legătură cu asta. Poți lăsa gol.",
    submit: "Continuă",
    submitting: "Un moment…",
    nameRequired: "Te rugăm să introduci un nume.",
    back: "Înapoi la pagina principală",
  },
  sso: {
    title: "Conectare",
    body: "Autorii de chestionare se conectează cu contul Microsoft al companiei.",
    button: "Conectare cu Microsoft",
    unavailable:
      "Conectarea companiei nu este încă configurată. Cere administratorului să seteze AUTH_PROVIDER=oidc.",
    notYou: "Nu ești autor? Nu trebuie să te conectezi pentru a completa un chestionar.",
  },
  ask: {
    title: "Întreabă despre fabrică",
    lede: "Siguranța alimentelor, HACCP, manipularea peștelui, lanțul frigorific, igienă și SSM.",
    disclaimer:
      "Răspunsurile sunt îndrumări generale. Planul HACCP al fabricii și responsabilul SSM au prioritate.",
    placeholder: "ex. Cât poate sta peștele afară la o oprire de linie?",
    send: "Întreabă",
    thinking: "Mă gândesc…",
    pending: "Caut răspunsul — poate dura până la un minut.",
    hint: "Enter trimite · Shift + Enter rând nou",
    tryTitle: "Încearcă una dintre acestea",
    offTopic: "În afara subiectului",
    examples: [
      "La ce temperatură trebuie ținut peștele refrigerat?",
      "Cât de des trebuie verificat detectorul de metale?",
      "Când trebuie raportat un incident evitat la limită?",
      "Ce este un punct critic de control, pe înțelesul tuturor?",
    ],
  },
  topics: {
    haccp: "HACCP",
    fish_handling: "Manipularea peștelui",
    cold_chain: "Lanț frigorific",
    hygiene: "Igienă",
    allergens: "Alergeni",
    health_and_safety: "Sănătate și securitate",
    audits: "Audituri",
    out_of_scope: "În afara subiectului",
  },
  common: {
    loading: "Se încarcă…",
    somethingWrong: "Ceva nu a mers bine.",
  },
};
