import type { Dictionary } from "./en";

/** Lithuanian. See TRANSLATIONS.md — not reviewed by a native speaker. */
export const lt: Dictionary = {
  nav: {
    build: "Kurti",
    respond: "Atsakyti",
    ask: "Klausti",
    signOut: "Atsijungti",
    signIn: "Prisijungti",
    home: "Pradžia",
    language: "Kalba",
  },
  landing: {
    eyebrow: "Pokalbio forma · Daugiakalbė · Įterpiama",
    heroTitle: "Klauskite kaip žmogus, o ne kaip anketa.",
    heroBody:
      "Aprašykite norimą apklausą ir Glance ją parengs. Žmonės atsako pokalbiu, bet kuriuo įrenginiu ir savo kalba.",
    respondCta: "Atsakyti į apklausą",
    askCta: "Užduoti klausimą",
    staffTitle: "Visiems atsakantiems",
    staffBody: "Paskyros nereikia. Įrašykite vardą ir pirmyn.",
    managerTitle: "Apklausų autoriams",
    managerBody:
      "Prisijunkite įmonės Microsoft paskyra, kad kurtumėte apklausas ir matytumėte rezultatus.",
    managerCta: "Prisijungti su Microsoft",
    footerNote: "Demonstracinė apklausų paslauga.",
  },
  guest: {
    title: "Jūsų vardas",
    body: "Kad atsakymuose būtų vardas. Be paskyros, be slaptažodžio.",
    nameLabel: "Vardas",
    namePlaceholder: "pvz. Marta K",
    emailLabel: "El. paštas",
    emailOptional: "Neprivaloma",
    emailHelp: "Tik tam, kad su jumis būtų galima susisiekti. Galite palikti tuščią.",
    submit: "Tęsti",
    submitting: "Palaukite…",
    nameRequired: "Įrašykite vardą.",
    back: "Grįžti į pradžią",
  },
  sso: {
    title: "Prisijungimas",
    body: "Apklausų autoriai jungiasi įmonės Microsoft paskyra.",
    button: "Prisijungti su Microsoft",
    unavailable:
      "Įmonės prisijungimas dar nesukonfigūruotas. Paprašykite administratoriaus nustatyti AUTH_PROVIDER=oidc.",
    notYou: "Ne autorius? Norint atsakyti į apklausą, prisijungti nereikia.",
  },
  ask: {
    title: "Klauskite apie įmonę",
    lede: "Maisto sauga, HACCP, žuvies tvarkymas, šaltoji grandinė, higiena ir darbų sauga.",
    disclaimer:
      "Atsakymai yra bendrosios gairės. Jūsų įmonės HACCP planas ir saugos vadovas yra svarbesni.",
    placeholder: "pvz. Kiek laiko žuvis gali gulėti sustojus linijai?",
    send: "Klausti",
    thinking: "Galvoju…",
    pending: "Ieškau atsakymo — tai gali užtrukti iki minutės.",
    hint: "Enter siunčia · Shift + Enter nauja eilutė",
    tryTitle: "Išbandykite vieną iš šių",
    offTopic: "Ne tema",
    examples: [
      "Kokioje temperatūroje laikyti atšaldytą žuvį?",
      "Kaip dažnai tikrinti metalo detektorių?",
      "Kada būtina pranešti apie vos neįvykusį incidentą?",
      "Kas yra svarbusis valdymo taškas paprastais žodžiais?",
    ],
  },
  topics: {
    haccp: "HACCP",
    fish_handling: "Žuvies tvarkymas",
    cold_chain: "Šaltoji grandinė",
    hygiene: "Higiena",
    allergens: "Alergenai",
    health_and_safety: "Darbų sauga",
    audits: "Auditai",
    out_of_scope: "Ne tema",
  },
  common: {
    loading: "Kraunama…",
    somethingWrong: "Kažkas nepavyko.",
  },
};
