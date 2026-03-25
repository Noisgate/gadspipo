import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import type { IntegrationCardStatus, ReadinessCheck } from "@adsmcp/domain";
import { exchangeGoogleAdsRefreshToken } from "./google-ads-oauth";

type GoogleAdsConfigMode = "env" | "yaml" | "missing";

type ParsedGoogleAdsYaml = {
  path: string;
  values: Partial<Record<string, string>>;
};

export type GoogleAdsConnectionDiagnostic = {
  status: IntegrationCardStatus;
  configMode: GoogleAdsConfigMode;
  isConfigured: boolean;
  targetCustomerId: string | null;
  loginCustomerId: string | null;
  credentialSourceLabel: string;
  summary: string;
  nextStep: string;
  checks: ReadinessCheck[];
  missingRequirements: string[];
  configPath: string | null;
};

type GoogleAdsResolvedConfig = {
  configMode: GoogleAdsConfigMode;
  configPath: string | null;
  developerToken: string;
  clientId: string;
  clientSecret: string;
  refreshToken: string;
  targetCustomerId: string | null;
  loginCustomerId: string | null;
};

type GoogleAdsApiErrorPayload = {
  error?: {
    code?: number;
    details?: Array<{
      errors?: Array<{
        errorCode?: Record<string, string>;
        message?: string;
      }>;
    }>;
    message?: string;
    status?: string;
  };
};

type GoogleAdsListAccessibleCustomersResponse = {
  resourceNames?: string[];
};

type GoogleAdsCustomerLookupResponse = {
  results?: Array<{
    customer?: {
      currencyCode?: string;
      descriptiveName?: string;
      id?: string;
      manager?: boolean;
      timeZone?: string;
    };
  }>;
};

export type GoogleAdsLiveConnectionCheck = {
  accessibleCustomerIds: string[];
  detail: string;
  requestId: string | null;
  status: "ready" | "warning" | "missing";
  summary: string;
  targetCustomer: {
    currencyCode: string | null;
    customerId: string;
    descriptiveName: string | null;
    isManager: boolean | null;
    timeZone: string | null;
  } | null;
};

const REQUIRED_YAML_KEYS = [
  "developer_token",
  "client_id",
  "client_secret",
  "refresh_token",
] as const;
const GOOGLE_ADS_API_BASE_URL = "https://googleads.googleapis.com/v22";

function normalizeGoogleAdsCustomerId(value?: string | null) {
  const trimmed = value?.trim() ?? "";

  if (!trimmed) {
    return "";
  }

  const digitsOnly = trimmed.replace(/\D/g, "");

  if (digitsOnly.length === 10) {
    return digitsOnly;
  }

  return trimmed;
}

function parseGoogleAdsYaml(rawValue: string): Partial<Record<string, string>> {
  return rawValue.split("\n").reduce<Partial<Record<string, string>>>(
    (acc, line) => {
      const trimmed = line.trim();

      if (!trimmed || trimmed.startsWith("#")) {
        return acc;
      }

      const separatorIndex = trimmed.indexOf(":");

      if (separatorIndex === -1) {
        return acc;
      }

      const key = trimmed.slice(0, separatorIndex).trim();
      const value = trimmed.slice(separatorIndex + 1).trim().replace(/^['"]|['"]$/g, "");

      if (key) {
        acc[key] = value;
      }

      return acc;
    },
    {},
  );
}

function getGoogleAdsYamlCandidates() {
  const cwd = process.cwd();

  return [
    path.join(os.homedir(), ".google-ads.yaml"),
    path.join(cwd, "google-ads.yaml"),
    path.resolve(cwd, "..", "google-ads.yaml"),
    path.resolve(cwd, "..", "..", "google-ads.yaml"),
  ];
}

function readGoogleAdsYamlConfig(): ParsedGoogleAdsYaml | null {
  const uniqueCandidates = [...new Set(getGoogleAdsYamlCandidates())];

  for (const candidate of uniqueCandidates) {
    if (!fs.existsSync(candidate)) {
      continue;
    }

    try {
      const rawValue = fs.readFileSync(candidate, "utf8");

      return {
        path: candidate,
        values: parseGoogleAdsYaml(rawValue),
      };
    } catch {
      continue;
    }
  }

  return null;
}

function resolveGoogleAdsConfig(
  workspaceCustomerId?: string | null,
): GoogleAdsResolvedConfig {
  const yamlConfig = readGoogleAdsYamlConfig();
  const yamlValues = yamlConfig?.values ?? {};
  const workspaceTargetCustomerId = normalizeGoogleAdsCustomerId(workspaceCustomerId);
  const envTargetCustomerId = normalizeGoogleAdsCustomerId(
    process.env.GOOGLE_ADS_CUSTOMER_ID,
  );
  const developerToken =
    process.env.GOOGLE_ADS_DEVELOPER_TOKEN?.trim() ||
    yamlValues.developer_token ||
    "";
  const clientId =
    process.env.GOOGLE_ADS_CLIENT_ID?.trim() ||
    process.env.GOOGLE_CLIENT_ID?.trim() ||
    yamlValues.client_id ||
    "";
  const clientSecret =
    process.env.GOOGLE_ADS_CLIENT_SECRET?.trim() ||
    process.env.GOOGLE_CLIENT_SECRET?.trim() ||
    yamlValues.client_secret ||
    "";
  const refreshToken =
    process.env.GOOGLE_ADS_REFRESH_TOKEN?.trim() ||
    yamlValues.refresh_token ||
    "";
  const targetCustomerId =
    workspaceTargetCustomerId ||
    envTargetCustomerId ||
    normalizeGoogleAdsCustomerId(yamlValues.customer_id) ||
    null;
  const loginCustomerId =
    normalizeGoogleAdsCustomerId(process.env.GOOGLE_ADS_LOGIN_CUSTOMER_ID) ||
    normalizeGoogleAdsCustomerId(yamlValues.login_customer_id) ||
    null;

  const configMode: GoogleAdsConfigMode =
    yamlConfig &&
    !process.env.GOOGLE_ADS_DEVELOPER_TOKEN &&
    !process.env.GOOGLE_ADS_CLIENT_ID &&
    !process.env.GOOGLE_CLIENT_ID &&
    !process.env.GOOGLE_ADS_CLIENT_SECRET &&
    !process.env.GOOGLE_CLIENT_SECRET &&
    !process.env.GOOGLE_ADS_REFRESH_TOKEN
      ? "yaml"
      : developerToken || clientId || clientSecret || refreshToken
        ? "env"
        : "missing";

  return {
    configMode,
    configPath: yamlConfig?.path ?? null,
    developerToken,
    clientId,
    clientSecret,
    refreshToken,
    targetCustomerId,
    loginCustomerId,
  };
}

function parseAccessibleCustomerIds(resourceNames?: string[]) {
  return (resourceNames ?? [])
    .map((resourceName) => {
      const match = resourceName.match(/^customers\/(\d+)$/);

      return match?.[1] ?? null;
    })
    .filter((value): value is string => Boolean(value));
}

function extractGoogleAdsApiError(payload: GoogleAdsApiErrorPayload | null) {
  const firstInnerError = payload?.error?.details?.[0]?.errors?.[0];
  const nestedErrorCode = firstInnerError?.errorCode
    ? Object.entries(firstInnerError.errorCode)
        .find(([, value]) => Boolean(value))
        ?.join(": ")
    : null;

  return {
    code: payload?.error?.code ?? null,
    detailMessage: firstInnerError?.message ?? null,
    message: payload?.error?.message ?? null,
    nestedErrorCode: nestedErrorCode ?? null,
    status: payload?.error?.status ?? null,
  };
}

async function parseGoogleAdsJsonResponse<T>(response: Response) {
  const payload = (await response.json().catch(() => null)) as T | GoogleAdsApiErrorPayload | null;
  const requestId = response.headers.get("request-id");

  if (!response.ok) {
    const error = extractGoogleAdsApiError(payload as GoogleAdsApiErrorPayload | null);
    const parts = [
      error.status,
      error.code ? String(error.code) : null,
      error.nestedErrorCode,
      error.detailMessage,
      error.message,
    ].filter(Boolean);

    throw new Error(
      parts.length > 0
        ? `Google Ads API retornou erro: ${parts.join(" | ")}`
        : "Google Ads API retornou erro inesperado.",
    );
  }

  return {
    payload: (payload ?? {}) as T,
    requestId,
  };
}

async function listAccessibleCustomers(config: GoogleAdsResolvedConfig) {
  const tokenResult = await exchangeGoogleAdsRefreshToken({
    clientId: config.clientId,
    clientSecret: config.clientSecret,
    refreshToken: config.refreshToken,
  });
  const response = await fetch(
    `${GOOGLE_ADS_API_BASE_URL}/customers:listAccessibleCustomers`,
    {
      headers: {
        Authorization: `Bearer ${tokenResult.accessToken}`,
        "developer-token": config.developerToken,
      },
      cache: "no-store",
    },
  );
  const { payload, requestId } =
    await parseGoogleAdsJsonResponse<GoogleAdsListAccessibleCustomersResponse>(response);

  return {
    accessibleCustomerIds: parseAccessibleCustomerIds(payload.resourceNames),
    requestId,
  };
}

async function lookupTargetCustomer(
  config: GoogleAdsResolvedConfig,
): Promise<GoogleAdsLiveConnectionCheck["targetCustomer"]> {
  if (!config.targetCustomerId) {
    return null;
  }

  const tokenResult = await exchangeGoogleAdsRefreshToken({
    clientId: config.clientId,
    clientSecret: config.clientSecret,
    refreshToken: config.refreshToken,
  });
  const headers = new Headers({
    Authorization: `Bearer ${tokenResult.accessToken}`,
    "Content-Type": "application/json",
    "developer-token": config.developerToken,
  });

  if (config.loginCustomerId) {
    headers.set("login-customer-id", config.loginCustomerId);
  }

  const response = await fetch(
    `${GOOGLE_ADS_API_BASE_URL}/customers/${config.targetCustomerId}/googleAds:search`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({
        query:
          "SELECT customer.id, customer.descriptive_name, customer.currency_code, customer.time_zone, customer.manager FROM customer LIMIT 1",
      }),
      cache: "no-store",
    },
  );
  const { payload } =
    await parseGoogleAdsJsonResponse<GoogleAdsCustomerLookupResponse>(response);
  const customer = payload.results?.[0]?.customer;

  if (!customer?.id) {
    return {
      currencyCode: null,
      customerId: config.targetCustomerId,
      descriptiveName: null,
      isManager: null,
      timeZone: null,
    };
  }

  return {
    currencyCode: customer.currencyCode ?? null,
    customerId: customer.id,
    descriptiveName: customer.descriptiveName ?? null,
    isManager:
      typeof customer.manager === "boolean" ? customer.manager : null,
    timeZone: customer.timeZone ?? null,
  };
}

function buildOauthStatusDetail(hasAnyOauthSignal: boolean, hasOauthReady: boolean) {
  if (hasOauthReady) {
    return "Client ID, client secret e refresh token ja estao presentes para autenticar a API.";
  }

  if (hasAnyOauthSignal) {
    return "Parte do OAuth ja existe, mas ainda faltam credenciais para a API do Google Ads ficar utilizavel.";
  }

  return "Sem OAuth completo, o app nao consegue consultar nem publicar campanhas via API.";
}

export function getGoogleAdsConnectionDiagnostic(
  workspaceCustomerId?: string | null,
): GoogleAdsConnectionDiagnostic {
  const yamlConfig = readGoogleAdsYamlConfig();
  const yamlValues = yamlConfig?.values ?? {};
  const resolvedConfig = resolveGoogleAdsConfig(workspaceCustomerId);
  const hasYamlReady = REQUIRED_YAML_KEYS.every((key) => Boolean(yamlValues[key]));
  const hasYamlSignal = Boolean(yamlConfig);
  const hasEnvDeveloperToken = Boolean(process.env.GOOGLE_ADS_DEVELOPER_TOKEN?.trim());
  const hasEnvOauthReady = Boolean(
    (process.env.GOOGLE_ADS_CLIENT_ID?.trim() ||
      process.env.GOOGLE_CLIENT_ID?.trim()) &&
      (process.env.GOOGLE_ADS_CLIENT_SECRET?.trim() ||
        process.env.GOOGLE_CLIENT_SECRET?.trim()) &&
      process.env.GOOGLE_ADS_REFRESH_TOKEN?.trim(),
  );
  const hasAnyEnvOauthSignal = Boolean(
    process.env.GOOGLE_ADS_CLIENT_ID?.trim() ||
      process.env.GOOGLE_CLIENT_ID?.trim() ||
      process.env.GOOGLE_ADS_CLIENT_SECRET?.trim() ||
      process.env.GOOGLE_CLIENT_SECRET?.trim() ||
      process.env.GOOGLE_ADS_REFRESH_TOKEN?.trim(),
  );
  const hasAnyAuthSignal = hasYamlSignal || hasEnvDeveloperToken || hasAnyEnvOauthSignal;
  const hasValidTargetCustomerId = Boolean(
    resolvedConfig.targetCustomerId && /^\d{10}$/.test(resolvedConfig.targetCustomerId),
  );
  const isConfigured =
    hasValidTargetCustomerId &&
    Boolean(
      resolvedConfig.developerToken &&
        resolvedConfig.clientId &&
        resolvedConfig.clientSecret &&
        resolvedConfig.refreshToken,
    );

  const configMode = resolvedConfig.configMode;

  const status: IntegrationCardStatus = isConfigured
    ? "connected"
    : hasAnyAuthSignal || hasValidTargetCustomerId
      ? "attention"
      : "disconnected";

  const missingRequirements = [
    hasEnvDeveloperToken || Boolean(yamlValues.developer_token)
      ? null
      : "developer token",
    resolvedConfig.clientId && resolvedConfig.clientSecret && resolvedConfig.refreshToken
      ? null
      : "OAuth completo",
    hasValidTargetCustomerId ? null : "customer id da conta",
  ].filter(Boolean) as string[];

  const credentialSourceLabel = isConfigured
    ? configMode === "yaml"
      ? "Configurado via google-ads.yaml"
      : "Configurado via variaveis de ambiente"
    : hasYamlSignal
      ? "Arquivo local encontrado"
      : hasAnyAuthSignal
        ? "Credenciais parciais encontradas"
        : "Credenciais ainda nao configuradas";

  const summary = isConfigured
    ? `Google Ads pronto para API mode com conta alvo ${resolvedConfig.targetCustomerId}.`
    : hasAnyAuthSignal || hasValidTargetCustomerId
      ? "Parte da configuracao do Google Ads ja existe, mas a conexao ainda nao esta completa."
      : "Ainda nao existe configuracao utilizavel do Google Ads API neste ambiente.";

  const nextStep = isConfigured
    ? "Validar a conta no Google Ads e seguir para leitura das campanhas ou publicacao controlada."
    : hasYamlSignal
      ? "Completar o customer id alvo e revisar se o google-ads.yaml tem developer token, OAuth e refresh token validos."
      : hasAnyAuthSignal
        ? "Completar as credenciais que faltam e informar a conta alvo para liberar a API."
        : "Adicionar developer token, OAuth, refresh token e o customer id da conta que recebera a primeira campanha.";

  const checks: ReadinessCheck[] = [
    {
      label: "Developer token",
      status:
        hasEnvDeveloperToken || Boolean(yamlValues.developer_token)
          ? "ready"
          : "missing",
      detail:
        hasEnvDeveloperToken || Boolean(yamlValues.developer_token)
          ? "O developer token ja esta presente para autenticar chamadas da API."
          : "Sem developer token aprovado, a API do Google Ads nao responde em modo real.",
    },
    {
      label: "OAuth da API",
      status:
        hasEnvOauthReady || hasYamlReady
          ? "ready"
          : hasAnyEnvOauthSignal || hasYamlSignal
            ? "warning"
            : "missing",
      detail: buildOauthStatusDetail(
        hasAnyEnvOauthSignal || hasYamlSignal,
        hasEnvOauthReady || hasYamlReady,
      ),
    },
    {
      label: "Conta alvo",
      status: hasValidTargetCustomerId
        ? "ready"
        : resolvedConfig.targetCustomerId
          ? "warning"
          : "missing",
      detail: hasValidTargetCustomerId
        ? `A primeira conta alvo foi definida como ${resolvedConfig.targetCustomerId}.`
        : resolvedConfig.targetCustomerId
          ? "O customer id foi encontrado, mas ainda nao esta no formato esperado de 10 digitos."
          : "Sem customer id alvo, o produto nao sabe em qual conta operar.",
    },
    {
      label: "Conta gerente (MCC)",
      status: resolvedConfig.loginCustomerId ? "ready" : "warning",
      detail: resolvedConfig.loginCustomerId
        ? `Login customer id identificado: ${resolvedConfig.loginCustomerId}.`
        : "Opcional. Preencha apenas se voce acessa a conta por uma MCC.",
    },
    {
      label: "Arquivo local google-ads.yaml",
      status: yamlConfig ? "ready" : "warning",
      detail: yamlConfig
        ? `Arquivo detectado em ${yamlConfig.path}.`
        : "Nao existe google-ads.yaml local. Tudo bem se as credenciais vierem por env vars.",
    },
  ];

  return {
    status,
    configMode,
    isConfigured,
    targetCustomerId: hasValidTargetCustomerId ? resolvedConfig.targetCustomerId : null,
    loginCustomerId: resolvedConfig.loginCustomerId,
    credentialSourceLabel,
    summary,
    nextStep,
    checks,
    missingRequirements,
    configPath: resolvedConfig.configPath,
  };
}

export async function getGoogleAdsLiveConnectionCheck(
  workspaceCustomerId?: string | null,
): Promise<GoogleAdsLiveConnectionCheck> {
  const config = resolveGoogleAdsConfig(workspaceCustomerId);
  const missingRequirements = [
    config.developerToken ? null : "developer token",
    config.clientId ? null : "client id",
    config.clientSecret ? null : "client secret",
    config.refreshToken ? null : "refresh token",
  ].filter(Boolean) as string[];

  if (missingRequirements.length > 0) {
    return {
      accessibleCustomerIds: [],
      detail: `Faltam ${missingRequirements.join(", ")} para a chamada real da API.`,
      requestId: null,
      status: "missing",
      summary: "A validacao real da API ainda nao pode rodar neste ambiente.",
      targetCustomer: null,
    };
  }

  try {
    const accessibleCustomers = await listAccessibleCustomers(config);
    let targetCustomer: GoogleAdsLiveConnectionCheck["targetCustomer"] = null;
    let detail =
      accessibleCustomers.accessibleCustomerIds.length > 0
        ? `OAuth e developer token responderam corretamente. ${accessibleCustomers.accessibleCustomerIds.length} conta(s) acessivel(is) foram encontradas.`
        : "OAuth e developer token responderam corretamente, mas nenhuma conta acessivel foi retornada.";
    let status: GoogleAdsLiveConnectionCheck["status"] =
      accessibleCustomers.accessibleCustomerIds.length > 0 ? "ready" : "warning";
    let summary = "Google Ads respondeu a uma chamada real da API.";

    if (config.targetCustomerId) {
      try {
        targetCustomer = await lookupTargetCustomer(config);

        if (targetCustomer?.descriptiveName || targetCustomer?.currencyCode) {
          detail = `Conta alvo ${targetCustomer.customerId} validada com sucesso${targetCustomer.descriptiveName ? ` (${targetCustomer.descriptiveName})` : ""}.`;
          status = "ready";
        } else if (accessibleCustomers.accessibleCustomerIds.includes(config.targetCustomerId)) {
          detail = `A conta alvo ${config.targetCustomerId} aparece entre as contas acessiveis pelo OAuth atual.`;
          status = "ready";
        } else {
          detail = `A API respondeu, mas a conta alvo ${config.targetCustomerId} nao foi confirmada nesta validacao. Se voce opera via MCC, preencha GOOGLE_ADS_LOGIN_CUSTOMER_ID com a conta gerente correta.`;
          status = "warning";
        }
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Falha ao validar a conta alvo.";
        detail = `${message} Se voce acessa a conta por MCC, confirme o login customer id.`;
        status = "warning";
        summary = "Google Ads autenticou, mas a conta alvo ainda nao foi validada.";
      }
    }

    return {
      accessibleCustomerIds: accessibleCustomers.accessibleCustomerIds,
      detail,
      requestId: accessibleCustomers.requestId,
      status,
      summary,
      targetCustomer,
    };
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Falha inesperada na validacao real da API do Google Ads.";

    return {
      accessibleCustomerIds: [],
      detail: message,
      requestId: null,
      status: "warning",
      summary: "A chamada real para o Google Ads falhou com as credenciais atuais.",
      targetCustomer: null,
    };
  }
}
