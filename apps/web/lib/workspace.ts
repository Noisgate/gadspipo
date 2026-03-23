import {
  buildSearchCampaignDraftPreview,
  campaignObjectiveOptions,
  defaultDriveIntake,
  defaultWorkspaceIntegrationCards,
  type CampaignBriefPreview,
  type ReadinessCheck,
  type CampaignObjective,
  type SearchCampaignDraftPreview,
  type WorkspaceDriveIntake,
  type WorkspaceIntegrationCard,
} from "@adsmcp/domain";

export type WorkspaceSnapshot = {
  ownerLabel: string;
  progress: number;
  nextAction: string;
  integrations: WorkspaceIntegrationCard[];
  driveIntake: WorkspaceDriveIntake;
  readinessScore: number;
  readinessChecks: ReadinessCheck[];
  briefPreview: CampaignBriefPreview;
  searchCampaignDraft: SearchCampaignDraftPreview;
};

type WorkspaceDriveIntakeInput = Partial<
  Omit<WorkspaceDriveIntake, "objective">
> & {
  objective?: string;
};

function normalizeGoogleAdsCustomerId(input: string) {
  const trimmed = input.trim();

  if (!trimmed) {
    return "";
  }

  const digitsOnly = trimmed.replace(/\D/g, "");

  if (digitsOnly.length === 10) {
    return digitsOnly;
  }

  return trimmed;
}

function parseGoogleDriveFolderId(input: string): string | null {
  const trimmed = input.trim();

  if (!trimmed) {
    return null;
  }

  const folderMatch = trimmed.match(/\/folders\/([a-zA-Z0-9_-]+)/);

  if (folderMatch?.[1]) {
    return folderMatch[1];
  }

  if (/^[a-zA-Z0-9_-]{10,}$/.test(trimmed)) {
    return trimmed;
  }

  return null;
}

function normalizeObjective(value: string): CampaignObjective {
  return campaignObjectiveOptions.includes(value as CampaignObjective)
    ? (value as CampaignObjective)
    : defaultDriveIntake.objective;
}

export function buildWorkspaceDriveIntake(
  input?: WorkspaceDriveIntakeInput,
): WorkspaceDriveIntake {
  const folderInput = input?.folderInput?.trim() ?? "";

  return {
    googleAdsCustomerId: normalizeGoogleAdsCustomerId(
      input?.googleAdsCustomerId ?? "",
    ),
    folderInput,
    folderId: parseGoogleDriveFolderId(folderInput),
    objective: normalizeObjective(input?.objective ?? defaultDriveIntake.objective),
    offerSummary: input?.offerSummary?.trim() ?? "",
    landingPageUrl: input?.landingPageUrl?.trim() ?? "",
    notes: input?.notes?.trim() ?? "",
  };
}

function buildReadinessChecks(
  driveIntake: WorkspaceDriveIntake,
): ReadinessCheck[] {
  const hasValidGoogleAdsCustomerId = /^\d{10}$/.test(
    driveIntake.googleAdsCustomerId,
  );

  return [
    {
      label: "Conta do Google Ads",
      status: hasValidGoogleAdsCustomerId
        ? "ready"
        : driveIntake.googleAdsCustomerId
          ? "warning"
          : "missing",
      detail: hasValidGoogleAdsCustomerId
        ? `Conta alvo definida como ${driveIntake.googleAdsCustomerId}.`
        : driveIntake.googleAdsCustomerId
          ? "O customer id foi informado, mas ainda nao esta no formato esperado de 10 digitos sem depender de contexto adicional."
          : "Informe o customer id da conta que vai receber a primeira campanha.",
    },
    {
      label: "Pasta do Google Drive",
      status: driveIntake.folderId ? "ready" : "missing",
      detail: driveIntake.folderId
        ? "A pasta foi identificada e já pode servir como origem da campanha quando a integração real entrar."
        : "Informe um link ou ID de pasta válido para iniciar a ingestão.",
    },
    {
      label: "Objetivo da campanha",
      status: driveIntake.objective ? "ready" : "missing",
      detail: driveIntake.objective
        ? `Objetivo definido como ${driveIntake.objective}.`
        : "Defina o resultado principal antes de gerar drafts.",
    },
    {
      label: "Oferta principal",
      status: driveIntake.offerSummary ? "ready" : "missing",
      detail: driveIntake.offerSummary
        ? "A proposta comercial já foi resumida e pode orientar a copy inicial."
        : "Resuma a oferta principal para dar direção ao draft.",
    },
    {
      label: "Landing page",
      status: driveIntake.landingPageUrl ? "ready" : "warning",
      detail: driveIntake.landingPageUrl
        ? "Há uma URL principal para alinhar promessa e destino da campanha."
        : "Sem landing page definida, o readiness continua parcial e as recomendações perdem precisão.",
    },
    {
      label: "Notas e restrições",
      status: driveIntake.notes ? "ready" : "warning",
      detail: driveIntake.notes
        ? "Existem sinais adicionais para tom de voz, restrições ou diferenciais."
        : "Adicione observações para enriquecer a leitura do contexto.",
    },
  ];
}

function calculateReadinessScore(checks: ReadinessCheck[]) {
  const scoreMap = {
    ready: 1,
    warning: 0.5,
    missing: 0,
  } as const;

  const total = checks.reduce((acc, item) => acc + scoreMap[item.status], 0);

  return Math.round((total / checks.length) * 100);
}

function buildBriefPreview(
  driveIntake: WorkspaceDriveIntake,
  checks: ReadinessCheck[],
): CampaignBriefPreview {
  const missingSignals = checks
    .filter((item) => item.status !== "ready")
    .map((item) => item.label);

  return {
    sourceSummary: driveIntake.folderId
      ? `Pasta selecionada: ${driveIntake.folderId}`
      : "Nenhuma pasta pronta para ingestão ainda.",
    campaignAngle: driveIntake.offerSummary
      ? driveIntake.offerSummary
      : "Oferta principal ainda não resumida.",
    targetOutcome: `Foco atual: ${driveIntake.objective}.`,
    missingSignals,
    nextBestActions: [
      /^\d{10}$/.test(driveIntake.googleAdsCustomerId)
        ? "Validar se o customer id informado corresponde exatamente a conta que recebera a primeira campanha."
        : "Registrar o customer id do Google Ads para definir a conta alvo da campanha.",
      driveIntake.folderId
        ? "Conectar Google Drive real para ler os arquivos automaticamente."
        : "Adicionar um link ou ID de pasta válido.",
      driveIntake.offerSummary
        ? "Refinar brand rules e diferenciais antes do draft."
        : "Resumir a oferta principal em uma frase objetiva.",
      driveIntake.landingPageUrl
        ? "Validar consistência entre oferta e landing page."
        : "Adicionar a landing page principal para melhorar a aderência da campanha.",
    ],
  };
}

function buildIntegrationCards(
  driveIntake: WorkspaceDriveIntake,
): WorkspaceIntegrationCard[] {
  return defaultWorkspaceIntegrationCards.map((card) => {
    if (card.key === "googleAds" && /^\d{10}$/.test(driveIntake.googleAdsCustomerId)) {
      return {
        ...card,
        summary: `A conta alvo ${driveIntake.googleAdsCustomerId} ja foi registrada no workspace, mas a autenticacao real da API ainda depende das credenciais do Google Ads.`,
        status: "attention",
        nextStep:
          "Configurar developer token, OAuth e refresh token para liberar leitura e publicacao reais.",
      };
    }

    if (card.key === "googleDrive" && driveIntake.folderId) {
      return {
        ...card,
        summary:
          "Uma pasta de campanha já foi registrada no workspace, mas a leitura automática ainda depende da conexão real do Drive.",
        status: "attention",
        nextStep: "Conectar Google Drive OAuth e iniciar ingestão automática da pasta.",
      };
    }

    return card;
  });
}

export function getWorkspaceSnapshot(
  ownerEmail?: string | null,
  driveIntakeInput?: WorkspaceDriveIntakeInput,
): WorkspaceSnapshot {
  const ownerLabel = ownerEmail?.split("@")[0] ?? "dono do negocio";
  const driveIntake = buildWorkspaceDriveIntake(driveIntakeInput);
  const hasValidGoogleAdsCustomerId = /^\d{10}$/.test(
    driveIntake.googleAdsCustomerId,
  );
  const integrations = buildIntegrationCards(driveIntake);
  const readinessChecks = buildReadinessChecks(driveIntake);
  const readinessScore = calculateReadinessScore(readinessChecks);
  const completedMilestones = [
    Boolean(ownerEmail),
    hasValidGoogleAdsCustomerId,
    Boolean(driveIntake.folderId),
    Boolean(driveIntake.offerSummary),
    Boolean(driveIntake.landingPageUrl),
  ].filter(Boolean).length;
  const progress = Math.round((completedMilestones / 5) * 100);
  const briefPreview = buildBriefPreview(driveIntake, readinessChecks);
  const searchCampaignDraft = buildSearchCampaignDraftPreview({
    ownerLabel,
    driveIntake,
    readinessChecks,
    briefPreview,
  });

  return {
    ownerLabel,
    progress,
    nextAction: !hasValidGoogleAdsCustomerId
      ? "Registrar o customer id do Google Ads para definir a conta alvo da primeira campanha."
      : !driveIntake.folderId
      ? "Informar uma pasta válida do Google Drive para destravar a ingestão."
      : !driveIntake.offerSummary
        ? "Resumir a oferta principal antes de gerar o primeiro brief utilizável."
        : !driveIntake.landingPageUrl
          ? "Adicionar a landing page principal para aumentar a qualidade do readiness."
          : "Conectar Google Ads API e Google Drive reais para sair do modo preview e seguir para o draft.",
    integrations,
    driveIntake,
    readinessScore,
    readinessChecks,
    briefPreview,
    searchCampaignDraft,
  };
}
