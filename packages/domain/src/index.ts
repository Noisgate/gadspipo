export const campaignObjectiveOptions = [
  "leads",
  "vendas",
  "agendamentos",
  "trafego qualificado",
] as const;

export type CampaignObjective = (typeof campaignObjectiveOptions)[number];

export const draftLifecycleStates = [
  "draft",
  "ready_for_review",
  "approved",
  "published",
  "recommendation_pending",
  "recommendation_approved",
  "applied",
  "rejected",
  "failed",
] as const;

export type DraftLifecycleState = (typeof draftLifecycleStates)[number];

export type MvpFeature = {
  id: string;
  name: string;
  outcome: string;
};

export const mvpFeatureSequence: MvpFeature[] = [
  {
    id: "MVP-01",
    name: "Workspace Onboarding",
    outcome: "Conectar Google Ads e Google Drive com clareza para o dono do negócio.",
  },
  {
    id: "MVP-02",
    name: "Drive Context Ingestion",
    outcome: "Ler a pasta da campanha, estruturar contexto e medir readiness.",
  },
  {
    id: "MVP-03",
    name: "Search Campaign Draft Builder",
    outcome: "Gerar drafts Search explicáveis a partir do briefing aprovado.",
  },
  {
    id: "MVP-04",
    name: "Approval, Publishing, and Audit",
    outcome: "Publicar apenas com aprovação e manter rastreabilidade completa.",
  },
  {
    id: "MVP-05",
    name: "Optimization Recommendations Center",
    outcome: "Sugerir melhorias contínuas sem tirar o controle do usuário.",
  },
];

export type Guardrails = {
  maxDailyBudget: number;
  allowedCountries: string[];
  blockedTerms: string[];
  searchOnly: boolean;
};

export const defaultGuardrails: Guardrails = {
  maxDailyBudget: 500,
  allowedCountries: ["BR"],
  blockedTerms: [],
  searchOnly: true,
};

export type WorkspaceIntegrationStatus = {
  googleAdsConnected: boolean;
  googleDriveConnected: boolean;
  readinessScore: number | null;
};

export type IntegrationCardStatus = "connected" | "disconnected" | "attention";

export type WorkspaceIntegrationCard = {
  key: "googleAds" | "googleDrive";
  name: string;
  summary: string;
  status: IntegrationCardStatus;
  nextStep: string;
};

export type ReadinessCheckStatus = "ready" | "missing" | "warning";

export type ReadinessCheck = {
  label: string;
  status: ReadinessCheckStatus;
  detail: string;
};

export type WorkspaceDriveIntake = {
  googleAdsCustomerId: string;
  folderInput: string;
  folderId: string | null;
  objective: CampaignObjective;
  offerSummary: string;
  landingPageUrl: string;
  notes: string;
};

export type CampaignBriefPreview = {
  sourceSummary: string;
  campaignAngle: string;
  targetOutcome: string;
  missingSignals: string[];
  nextBestActions: string[];
};

export type SearchCampaignDraftStatus = "ready" | "needs_context";

export type SearchAdGroupDraft = {
  name: string;
  focus: string;
  keywords: string[];
  headlines: string[];
  descriptions: string[];
  rationale: string;
};

export type SearchCampaignDraftPreview = {
  status: SearchCampaignDraftStatus;
  statusDetail: string;
  campaignName: string;
  objective: CampaignObjective;
  budgetGuidance: string;
  adGroups: SearchAdGroupDraft[];
  negativeKeywords: string[];
  extensions: string[];
  rationale: string[];
  blockers: string[];
};

export const defaultWorkspaceIntegrationCards: WorkspaceIntegrationCard[] = [
  {
    key: "googleAds",
    name: "Google Ads",
    summary:
      "Conta ainda nao preparada. Sem customer id, developer token e OAuth, o produto nao consegue criar ou publicar campanhas.",
    status: "disconnected",
    nextStep:
      "Registrar a conta alvo e configurar Google Ads API para liberar drafts e publicacao.",
  },
  {
    key: "googleDrive",
    name: "Google Drive",
    summary: "Pasta de campanha ainda não conectada. O contexto do negócio continua indisponível para ingestão.",
    status: "disconnected",
    nextStep: "Conectar Google Drive para importar briefing, oferta e landing pages.",
  },
];

export const defaultDriveIntake: WorkspaceDriveIntake = {
  googleAdsCustomerId: "",
  folderInput: "",
  folderId: null,
  objective: "leads",
  offerSummary: "",
  landingPageUrl: "",
  notes: "",
};

const ptBrStopwords = new Set([
  "a",
  "ao",
  "aos",
  "as",
  "com",
  "como",
  "da",
  "das",
  "de",
  "do",
  "dos",
  "e",
  "em",
  "na",
  "nas",
  "no",
  "nos",
  "o",
  "os",
  "ou",
  "para",
  "por",
  "se",
  "sem",
  "um",
  "uma",
]);

const objectiveBudgetGuidance: Record<CampaignObjective, string> = {
  leads: "Comecar com grupos enxutos, foco em termos de alta intencao e lances conservadores por conversao.",
  vendas: "Priorizar intencao comercial, landing page orientada a compra e monitorar termos de preco desde o primeiro dia.",
  agendamentos: "Concentrar verba em termos de contato imediato e reforcar CTAs de agenda nos anuncios e extensoes.",
  "trafego qualificado":
    "Abrir cobertura com termos relevantes, mas preservar filtros de qualidade para evitar clique curioso demais.",
};

const objectiveIntentSuffixes: Record<CampaignObjective, string[]> = {
  leads: ["orcamento", "contato", "empresa"],
  vendas: ["preco", "comprar", "oferta"],
  agendamentos: ["agendar", "consulta", "marcar"],
  "trafego qualificado": ["site", "solucao", "servico"],
};

const objectiveHeadlineCtas: Record<CampaignObjective, string[]> = {
  leads: ["Solicite um contato", "Fale com especialista", "Receba um orcamento"],
  vendas: ["Veja a oferta", "Compre com clareza", "Conheca as condicoes"],
  agendamentos: ["Agende seu horario", "Marque uma conversa", "Atendimento rapido"],
  "trafego qualificado": [
    "Conheca a solucao",
    "Veja como funciona",
    "Descubra a proposta",
  ],
};

function uniqueItems(items: string[]) {
  return [...new Set(items.filter(Boolean))];
}

function titleCase(value: string) {
  return value
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function normalizeWords(input: string) {
  return input
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((word) => word.length >= 3 && !ptBrStopwords.has(word));
}

function buildPhraseSeeds(offerSummary: string, ownerLabel: string) {
  const tokens = uniqueItems(normalizeWords(offerSummary));
  const labelSeed =
    ownerLabel && ownerLabel !== "dono do negocio"
      ? ownerLabel.replace(/[-_]/g, " ").toLowerCase()
      : "";

  const seeds = [
    tokens.slice(0, 2).join(" "),
    tokens.slice(2, 4).join(" "),
    tokens[0] ?? "",
    labelSeed,
  ];

  return uniqueItems(seeds).filter((seed) => seed.length >= 3).slice(0, 3);
}

function buildSearchKeywords(seed: string, objective: CampaignObjective) {
  const suffixes = objectiveIntentSuffixes[objective];

  return uniqueItems([
    seed,
    `${seed} ${suffixes[0]}`,
    `${seed} ${suffixes[1]}`,
    `${seed} ${suffixes[2]}`,
  ]).slice(0, 4);
}

function buildSearchAdGroup(
  seed: string,
  objective: CampaignObjective,
  offerSummary: string,
) {
  const ctas = objectiveHeadlineCtas[objective];
  const conciseOffer = offerSummary.trim() || "Sua oferta principal";
  const label = titleCase(seed);

  return {
    name: label,
    focus: `Grupo orientado ao tema "${label}" para capturar buscas relacionadas a ${conciseOffer.toLowerCase()}.`,
    keywords: buildSearchKeywords(seed, objective),
    headlines: uniqueItems([
      label,
      conciseOffer.slice(0, 30),
      ctas[0],
      ctas[1],
    ]).slice(0, 3),
    descriptions: uniqueItems([
      `${conciseOffer}. ${ctas[0]}.`,
      `Mensagem alinhada ao objetivo de ${objective} com foco em clareza e proxima acao.`,
    ]).slice(0, 2),
    rationale: `Este grupo conecta o tema "${label}" ao objetivo de ${objective}, mantendo intencao alta e copy direta.`,
  };
}

export function buildSearchCampaignDraftPreview(input: {
  ownerLabel: string;
  driveIntake: WorkspaceDriveIntake;
  readinessChecks: ReadinessCheck[];
  briefPreview: CampaignBriefPreview;
}): SearchCampaignDraftPreview {
  const blockers = input.readinessChecks
    .filter((item) => item.status === "missing")
    .map((item) => item.label);
  const seeds = buildPhraseSeeds(input.driveIntake.offerSummary, input.ownerLabel);
  const adGroupSeeds = seeds.length > 0 ? seeds : ["oferta principal", "solucao", "marca"];
  const ownerToken =
    input.ownerLabel && input.ownerLabel !== "dono do negocio"
      ? titleCase(input.ownerLabel.replace(/[-_]/g, " "))
      : "Workspace";
  const status: SearchCampaignDraftStatus =
    blockers.includes("Oferta principal") || blockers.includes("Pasta do Google Drive")
      ? "needs_context"
      : "ready";

  return {
    status,
    statusDetail:
      status === "ready"
        ? "O contexto atual ja permite montar um draft Search inicial para revisao humana."
        : "Ainda faltam sinais criticos antes de confiar em um draft para aprovacao.",
    campaignName: `Search | ${titleCase(input.driveIntake.objective)} | ${ownerToken}`,
    objective: input.driveIntake.objective,
    budgetGuidance: objectiveBudgetGuidance[input.driveIntake.objective],
    adGroups: adGroupSeeds.map((seed) =>
      buildSearchAdGroup(seed, input.driveIntake.objective, input.driveIntake.offerSummary),
    ),
    negativeKeywords: uniqueItems([
      "gratis",
      "download",
      "vaga",
      "reclamacao",
      input.driveIntake.objective === "vendas" ? "manual" : "",
    ]).slice(0, 5),
    extensions: uniqueItems([
      "Sitelink: Conheca a oferta",
      "Sitelink: Como funciona",
      "Callout: Atendimento consultivo",
      "Snippet: Beneficios e diferenciais",
    ]),
    rationale: [
      `O draft parte do angulo principal identificado: ${input.briefPreview.campaignAngle}`,
      `O objetivo ativo e ${input.driveIntake.objective}, entao a copy prioriza uma CTA coerente com esse desfecho.`,
      `Os grupos foram mantidos enxutos para facilitar revisao, aprovacao e aprendizado inicial da conta.`,
    ],
    blockers,
  };
}
