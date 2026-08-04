import type { Dictionary } from "./en";

/** Polish. See TRANSLATIONS.md — not reviewed by a native speaker. */
export const pl: Dictionary = {
  nav: {
    build: "Twórz",
    respond: "Odpowiedz",
    ask: "Zapytaj",
    signOut: "Wyloguj",
    signIn: "Zaloguj",
    home: "Strona główna",
    language: "Język",
  },
  landing: {
    eyebrow: "Rozmowa · Wielojęzyczność · Osadzanie",
    heroTitle: "Pytaj jak człowiek, nie jak formularz.",
    heroBody:
      "Opisz ankietę, której potrzebujesz, a Glance ją przygotuje. Ludzie odpowiadają w rozmowie, na dowolnym urządzeniu i we własnym języku.",
    respondCta: "Wypełnij ankietę",
    askCta: "Zadaj pytanie",
    staffTitle: "Dla wszystkich odpowiadających",
    staffBody: "Konto nie jest potrzebne. Podaj imię i zaczynaj.",
    managerTitle: "Dla autorów ankiet",
    managerBody:
      "Zaloguj się firmowym kontem Microsoft, aby tworzyć ankiety i przeglądać wyniki.",
    managerCta: "Zaloguj przez Microsoft",
    footerNote: "Demonstracyjna usługa ankiet.",
  },
  guest: {
    title: "Twoje imię",
    body: "Żeby odpowiedzi miały podpis. Bez konta, bez hasła.",
    nameLabel: "Imię i nazwisko",
    namePlaceholder: "np. Marta K",
    emailLabel: "E-mail",
    emailOptional: "Opcjonalnie",
    emailHelp: "Tylko po to, żeby ktoś mógł się z Tobą skontaktować. Możesz zostawić puste.",
    submit: "Dalej",
    submitting: "Chwileczkę…",
    nameRequired: "Podaj imię.",
    back: "Wróć na stronę główną",
  },
  sso: {
    title: "Logowanie",
    body: "Autorzy ankiet logują się firmowym kontem Microsoft.",
    button: "Zaloguj przez Microsoft",
    unavailable:
      "Logowanie firmowe nie jest jeszcze skonfigurowane. Poproś administratora o ustawienie AUTH_PROVIDER=oidc.",
    notYou: "Nie jesteś autorem? Nie musisz się logować, aby wypełnić ankietę.",
  },
  ask: {
    title: "Zapytaj o zakład",
    lede: "Bezpieczeństwo żywności, HACCP, obróbka ryb, łańcuch chłodniczy, higiena i BHP.",
    disclaimer:
      "Odpowiedzi to ogólne wytyczne branżowe. Plan HACCP zakładu i kierownik BHP mają pierwszeństwo.",
    placeholder: "np. Jak długo ryba może leżeć przy postoju linii?",
    send: "Zapytaj",
    thinking: "Myślę…",
    pending: "Szukam odpowiedzi — to może potrwać do minuty.",
    hint: "Enter wysyła · Shift + Enter nowa linia",
    tryTitle: "Wypróbuj jedno z tych",
    offTopic: "Poza tematem",
    examples: [
      "W jakiej temperaturze przechowywać schłodzone ryby?",
      "Jak często sprawdzać wykrywacz metali?",
      "Kiedy trzeba zgłosić zdarzenie potencjalnie wypadkowe?",
      "Czym jest krytyczny punkt kontroli, prostymi słowami?",
    ],
  },
  topics: {
    haccp: "HACCP",
    fish_handling: "Obróbka ryb",
    cold_chain: "Łańcuch chłodniczy",
    hygiene: "Higiena",
    allergens: "Alergeny",
    health_and_safety: "BHP",
    audits: "Audyty",
    out_of_scope: "Poza tematem",
  },
  common: {
    loading: "Ładowanie…",
    somethingWrong: "Coś poszło nie tak.",
  },
};
