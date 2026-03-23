import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import type { IntegrationCardStatus, ReadinessCheck } from "@adsmcp/domain";

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

const REQUIRED_YAML_KEYS = [
  "developer_token",
  "client_id",
  "client_secret",
  "refresh_token",
] as const;

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
  const envDeveloperToken = process.env.GOOGLE_ADS_DEVELOPER_TOKEN?.trim() ?? "";
  const envClientId =
    process.env.GOOGLE_ADS_CLIENT_ID?.trim() ||
    process.env.GOOGLE_CLIENT_ID?.trim() ||
    "";
  const envClientSecret =
    process.env.GOOGLE_ADS_CLIENT_SECRET?.trim() ||
    process.env.GOOGLE_CLIENT_SECRET?.trim() ||
    "";
  const envRefreshToken = process.env.GOOGLE_ADS_REFRESH_TOKEN?.trim() ?? "";
  const workspaceTargetCustomerId = normalizeGoogleAdsCustomerId(workspaceCustomerId);
  const envTargetCustomerId = normalizeGoogleAdsCustomerId(
    process.env.GOOGLE_ADS_CUSTOMER_ID,
  );
  const targetCustomerId = workspaceTargetCustomerId || envTargetCustomerId || null;
  const loginCustomerId =
    normalizeGoogleAdsCustomerId(process.env.GOOGLE_ADS_LOGIN_CUSTOMER_ID) ||
    normalizeGoogleAdsCustomerId(yamlValues.login_customer_id) ||
    null;

  const hasYamlReady = REQUIRED_YAML_KEYS.every((key) => Boolean(yamlValues[key]));
  const hasYamlSignal = Boolean(yamlConfig);
  const hasEnvDeveloperToken = Boolean(envDeveloperToken);
  const hasEnvOauthReady = Boolean(envClientId && envClientSecret && envRefreshToken);
  const hasAnyEnvOauthSignal = Boolean(envClientId || envClientSecret || envRefreshToken);
  const hasAnyAuthSignal = hasYamlSignal || hasEnvDeveloperToken || hasAnyEnvOauthSignal;
  const hasValidTargetCustomerId = Boolean(targetCustomerId && /^\d{10}$/.test(targetCustomerId));
  const isConfigured =
    hasValidTargetCustomerId && (hasYamlReady || (hasEnvDeveloperToken && hasEnvOauthReady));

  const configMode: GoogleAdsConfigMode = hasYamlReady
    ? "yaml"
    : hasEnvDeveloperToken || hasAnyEnvOauthSignal
      ? "env"
      : "missing";

  const status: IntegrationCardStatus = isConfigured
    ? "connected"
    : hasAnyAuthSignal || hasValidTargetCustomerId
      ? "attention"
      : "disconnected";

  const missingRequirements = [
    hasEnvDeveloperToken || Boolean(yamlValues.developer_token)
      ? null
      : "developer token",
    hasEnvOauthReady || hasYamlReady ? null : "OAuth completo",
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
    ? `Google Ads pronto para API mode com conta alvo ${targetCustomerId}.`
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
        : targetCustomerId
          ? "warning"
          : "missing",
      detail: hasValidTargetCustomerId
        ? `A primeira conta alvo foi definida como ${targetCustomerId}.`
        : targetCustomerId
          ? "O customer id foi encontrado, mas ainda nao esta no formato esperado de 10 digitos."
          : "Sem customer id alvo, o produto nao sabe em qual conta operar.",
    },
    {
      label: "Conta gerente (MCC)",
      status: loginCustomerId ? "ready" : "warning",
      detail: loginCustomerId
        ? `Login customer id identificado: ${loginCustomerId}.`
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
    targetCustomerId: hasValidTargetCustomerId ? targetCustomerId : null,
    loginCustomerId,
    credentialSourceLabel,
    summary,
    nextStep,
    checks,
    missingRequirements,
    configPath: yamlConfig?.path ?? null,
  };
}
