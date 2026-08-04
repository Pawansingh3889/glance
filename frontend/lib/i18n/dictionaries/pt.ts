import type { Dictionary } from "./en";

/** Portuguese (European). See TRANSLATIONS.md — not reviewed by a native speaker. */
export const pt: Dictionary = {
  nav: {
    build: "Criar",
    respond: "Responder",
    ask: "Perguntar",
    signOut: "Terminar sessão",
    signIn: "Iniciar sessão",
    home: "Início",
    language: "Idioma",
  },
  landing: {
    eyebrow: "Conversacional · Multilingue · Integrável",
    heroTitle: "Pergunte como uma pessoa, não como um formulário.",
    heroBody:
      "Descreva o questionário que quer e o Glance redige-o. As pessoas respondem numa conversa, em qualquer dispositivo e na sua língua.",
    respondCta: "Responder a um questionário",
    askCta: "Fazer uma pergunta",
    staffTitle: "Para todos os que respondem",
    staffBody: "Não é preciso conta. Diga o seu nome e avance.",
    managerTitle: "Para autores de questionários",
    managerBody:
      "Inicie sessão com a conta Microsoft da empresa para criar questionários e ver resultados.",
    managerCta: "Iniciar sessão com a Microsoft",
    footerNote: "Serviço de questionários de demonstração.",
  },
  guest: {
    title: "O seu nome",
    body: "Para que as respostas tenham um nome. Sem conta, sem palavra-passe.",
    nameLabel: "Nome",
    namePlaceholder: "ex. Marta K",
    emailLabel: "E-mail",
    emailOptional: "Opcional",
    emailHelp: "Apenas para que alguém o possa contactar sobre isto. Pode deixar em branco.",
    submit: "Continuar",
    submitting: "Um momento…",
    nameRequired: "Indique um nome.",
    back: "Voltar ao início",
  },
  sso: {
    title: "Iniciar sessão",
    body: "Os autores de questionários entram com a conta Microsoft da empresa.",
    button: "Iniciar sessão com a Microsoft",
    unavailable:
      "O início de sessão da empresa ainda não está configurado. Peça ao administrador para definir AUTH_PROVIDER=oidc.",
    notYou: "Não é autor? Não precisa de iniciar sessão para responder a um questionário.",
  },
  ask: {
    title: "Perguntar sobre a fábrica",
    lede: "Segurança alimentar, HACCP, manuseamento de pescado, cadeia de frio, higiene e segurança no trabalho.",
    disclaimer:
      "As respostas são orientações gerais do setor. O plano HACCP da sua unidade e o responsável de segurança têm precedência.",
    placeholder: "ex. Quanto tempo pode o peixe ficar fora numa paragem de linha?",
    send: "Perguntar",
    thinking: "A pensar…",
    pending: "A procurar a resposta — pode demorar até um minuto.",
    hint: "Enter envia · Shift + Enter nova linha",
    tryTitle: "Experimente uma destas",
    offTopic: "Fora do tema",
    examples: [
      "A que temperatura deve ser mantido o peixe refrigerado?",
      "Com que frequência deve ser verificado o detetor de metais?",
      "Quando tem de ser comunicado um quase-acidente?",
      "O que é um ponto crítico de controlo, em palavras simples?",
    ],
  },
  topics: {
    haccp: "HACCP",
    fish_handling: "Manuseamento de pescado",
    cold_chain: "Cadeia de frio",
    hygiene: "Higiene",
    allergens: "Alergénios",
    health_and_safety: "Segurança no trabalho",
    audits: "Auditorias",
    out_of_scope: "Fora do tema",
  },
  common: {
    loading: "A carregar…",
    somethingWrong: "Algo correu mal.",
  },
};
