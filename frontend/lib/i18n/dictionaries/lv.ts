import type { Dictionary } from "./en";

/** Latvian. See TRANSLATIONS.md — not reviewed by a native speaker. */
export const lv: Dictionary = {
  nav: {
    build: "Veidot",
    respond: "Atbildēt",
    ask: "Jautāt",
    signOut: "Iziet",
    signIn: "Pieteikties",
    home: "Sākums",
    language: "Valoda",
  },
  landing: {
    eyebrow: "Sarunveida · Daudzvalodu · Iegulstama",
    heroTitle: "Jautājiet kā cilvēks, nevis kā veidlapa.",
    heroBody:
      "Aprakstiet vēlamo aptauju, un Glance to sagatavos. Cilvēki atbild sarunā, jebkurā ierīcē un savā valodā.",
    respondCta: "Aizpildīt aptauju",
    askCta: "Uzdot jautājumu",
    staffTitle: "Visiem, kas atbild",
    staffBody: "Konts nav vajadzīgs. Ierakstiet vārdu un turpiniet.",
    managerTitle: "Aptauju autoriem",
    managerBody:
      "Piesakieties ar uzņēmuma Microsoft kontu, lai veidotu aptaujas un skatītu rezultātus.",
    managerCta: "Pieteikties ar Microsoft",
    footerNote: "Demonstrācijas aptauju pakalpojums.",
  },
  guest: {
    title: "Jūsu vārds",
    body: "Lai atbildēm būtu vārds. Bez konta, bez paroles.",
    nameLabel: "Vārds",
    namePlaceholder: "piem. Marta K",
    emailLabel: "E-pasts",
    emailOptional: "Nav obligāti",
    emailHelp: "Tikai tāpēc, lai kāds varētu ar jums sazināties. Varat atstāt tukšu.",
    submit: "Turpināt",
    submitting: "Brīdi…",
    nameRequired: "Lūdzu, ierakstiet vārdu.",
    back: "Atpakaļ uz sākumu",
  },
  sso: {
    title: "Pieteikšanās",
    body: "Aptauju autori piesakās ar uzņēmuma Microsoft kontu.",
    button: "Pieteikties ar Microsoft",
    unavailable:
      "Uzņēmuma pieteikšanās vēl nav konfigurēta. Palūdziet administratoram iestatīt AUTH_PROVIDER=oidc.",
    notYou: "Neesat autors? Lai atbildētu uz aptauju, pieteikties nav nepieciešams.",
  },
  ask: {
    title: "Jautājiet par ražotni",
    lede: "Pārtikas nekaitīgums, HACCP, zivju apstrāde, aukstuma ķēde, higiēna un darba aizsardzība.",
    disclaimer:
      "Atbildes ir vispārīgas nozares vadlīnijas. Jūsu ražotnes HACCP plāns un darba aizsardzības vadītājs ir noteicošie.",
    placeholder: "piem. Cik ilgi zivs var stāvēt, ja līnija ir apstājusies?",
    send: "Jautāt",
    thinking: "Domāju…",
    pending: "Meklēju atbildi — tas var aizņemt līdz minūtei.",
    hint: "Enter nosūta · Shift + Enter jauna rinda",
    tryTitle: "Izmēģiniet vienu no šiem",
    offTopic: "Ārpus tēmas",
    examples: [
      "Kādā temperatūrā jāuzglabā atdzesēta zivs?",
      "Cik bieži jāpārbauda metāla detektors?",
      "Kad jāziņo par gandrīz notikušu nelaimi?",
      "Kas ir kritiskais kontroles punkts vienkāršiem vārdiem?",
    ],
  },
  topics: {
    haccp: "HACCP",
    fish_handling: "Zivju apstrāde",
    cold_chain: "Aukstuma ķēde",
    hygiene: "Higiēna",
    allergens: "Alergēni",
    health_and_safety: "Darba aizsardzība",
    audits: "Auditi",
    out_of_scope: "Ārpus tēmas",
  },
  common: {
    loading: "Ielādē…",
    somethingWrong: "Kaut kas nogāja greizi.",
  },
};
