import type { Dictionary } from "./en";

/** Spanish. See TRANSLATIONS.md — not reviewed by a native speaker. */
export const es: Dictionary = {
  nav: {
    build: "Crear",
    respond: "Responder",
    ask: "Preguntar",
    signOut: "Cerrar sesión",
    signIn: "Iniciar sesión",
    home: "Inicio",
    language: "Idioma",
  },
  landing: {
    eyebrow: "Conversacional · Multilingüe · Integrable",
    heroTitle: "Pregunta como una persona, no como un formulario.",
    heroBody:
      "Describe la encuesta que quieres y Glance la redacta. La gente responde conversando, en cualquier dispositivo y en su idioma.",
    respondCta: "Responder una encuesta",
    askCta: "Hacer una pregunta",
    staffTitle: "Para todos los que responden",
    staffBody: "No hace falta cuenta. Pon tu nombre y adelante.",
    managerTitle: "Para autores de encuestas",
    managerBody:
      "Inicia sesión con la cuenta Microsoft de la empresa para crear encuestas y ver resultados.",
    managerCta: "Iniciar sesión con Microsoft",
    footerNote: "Servicio de encuestas de demostración.",
  },
  guest: {
    title: "Tu nombre",
    body: "Para que las respuestas lleven un nombre. Sin cuenta, sin contraseña.",
    nameLabel: "Nombre",
    namePlaceholder: "p. ej. Marta K",
    emailLabel: "Correo electrónico",
    emailOptional: "Opcional",
    emailHelp: "Solo para que alguien pueda contactarte sobre esto. Puedes dejarlo en blanco.",
    submit: "Continuar",
    submitting: "Un momento…",
    nameRequired: "Introduce un nombre.",
    back: "Volver al inicio",
  },
  sso: {
    title: "Iniciar sesión",
    body: "Los autores de encuestas entran con la cuenta Microsoft de la empresa.",
    button: "Iniciar sesión con Microsoft",
    unavailable:
      "El inicio de sesión corporativo aún no está configurado. Pide al administrador que establezca AUTH_PROVIDER=oidc.",
    notYou: "¿No eres autor? No necesitas iniciar sesión para responder una encuesta.",
  },
  ask: {
    title: "Pregunta sobre la planta",
    lede: "Seguridad alimentaria, APPCC, manipulación de pescado, cadena de frío, higiene y prevención.",
    disclaimer:
      "Las respuestas son orientación general del sector. El plan APPCC de tu planta y tu responsable de seguridad tienen prioridad.",
    placeholder: "p. ej. ¿Cuánto puede estar el pescado fuera en una parada de línea?",
    send: "Preguntar",
    thinking: "Pensando…",
    pending: "Buscando la respuesta — puede tardar hasta un minuto.",
    hint: "Enter envía · Mayús + Enter nueva línea",
    tryTitle: "Prueba una de estas",
    offTopic: "Fuera de tema",
    examples: [
      "¿A qué temperatura debe conservarse el pescado refrigerado?",
      "¿Con qué frecuencia hay que verificar el detector de metales?",
      "¿Cuándo hay que notificar un incidente sin daños?",
      "¿Qué es un punto de control crítico, en palabras sencillas?",
    ],
  },
  topics: {
    haccp: "APPCC",
    fish_handling: "Manipulación de pescado",
    cold_chain: "Cadena de frío",
    hygiene: "Higiene",
    allergens: "Alérgenos",
    health_and_safety: "Prevención de riesgos",
    audits: "Auditorías",
    out_of_scope: "Fuera de tema",
  },
  common: {
    loading: "Cargando…",
    somethingWrong: "Algo ha ido mal.",
  },
};
