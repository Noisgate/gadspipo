import { randomBytes } from "node:crypto";

const GOOGLE_ADS_SCOPE = "https://www.googleapis.com/auth/adwords";
const GOOGLE_OAUTH_AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth";
const GOOGLE_OAUTH_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token";

export type GoogleAdsOauthEnv = {
  clientId: string;
  clientSecret: string;
  isReady: boolean;
  missingRequirements: string[];
};

type ExchangeGoogleAdsAuthCodeInput = {
  clientId: string;
  clientSecret: string;
  code: string;
  redirectUri: string;
};

type ExchangeGoogleAdsRefreshTokenInput = {
  clientId: string;
  clientSecret: string;
  refreshToken: string;
};

type GoogleOauthTokenResponse = {
  access_token?: string;
  error?: string;
  error_description?: string;
  expires_in?: number;
  refresh_token?: string;
  scope?: string;
  token_type?: string;
};

export type GoogleAdsTokenExchangeResult = {
  accessToken: string;
  expiresIn: number | null;
  refreshToken: string | null;
  scope: string | null;
  tokenType: string | null;
};

async function exchangeGoogleOauthToken(
  body: URLSearchParams,
): Promise<GoogleAdsTokenExchangeResult> {
  const response = await fetch(GOOGLE_OAUTH_TOKEN_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
    cache: "no-store",
  });

  const payload = (await response
    .json()
    .catch(() => null)) as GoogleOauthTokenResponse | null;

  if (!response.ok || !payload?.access_token) {
    const detail = [payload?.error, payload?.error_description]
      .filter(Boolean)
      .join(": ");

    throw new Error(
      detail || "Falha ao trocar credenciais por tokens do Google.",
    );
  }

  return {
    accessToken: payload.access_token,
    expiresIn:
      typeof payload.expires_in === "number" ? payload.expires_in : null,
    refreshToken: payload.refresh_token ?? null,
    scope: payload.scope ?? null,
    tokenType: payload.token_type ?? null,
  };
}

function readGoogleAdsClientId() {
  return (
    process.env.GOOGLE_ADS_CLIENT_ID?.trim() ||
    process.env.GOOGLE_CLIENT_ID?.trim() ||
    ""
  );
}

function readGoogleAdsClientSecret() {
  return (
    process.env.GOOGLE_ADS_CLIENT_SECRET?.trim() ||
    process.env.GOOGLE_CLIENT_SECRET?.trim() ||
    ""
  );
}

export function getGoogleAdsOauthEnv(): GoogleAdsOauthEnv {
  const clientId = readGoogleAdsClientId();
  const clientSecret = readGoogleAdsClientSecret();
  const missingRequirements = [
    clientId ? null : "client id",
    clientSecret ? null : "client secret",
  ].filter(Boolean) as string[];

  return {
    clientId,
    clientSecret,
    isReady: missingRequirements.length === 0,
    missingRequirements,
  };
}

export function getRequestOrigin(headers: Pick<Headers, "get">) {
  const host = headers.get("x-forwarded-host") ?? headers.get("host");

  if (!host) {
    return null;
  }

  const proto =
    headers.get("x-forwarded-proto") ??
    (host.includes("localhost") || host.startsWith("127.0.0.1")
      ? "http"
      : "https");

  return `${proto}://${host}`;
}

export function buildGoogleAdsOauthRedirectUri(origin: string) {
  return new URL("/auth/google-ads/callback", origin).toString();
}

export function createGoogleAdsOauthState() {
  return randomBytes(24).toString("hex");
}

export function buildGoogleAdsAuthUrl(input: {
  clientId: string;
  redirectUri: string;
  state: string;
}) {
  const searchParams = new URLSearchParams({
    access_type: "offline",
    client_id: input.clientId,
    include_granted_scopes: "true",
    prompt: "consent",
    redirect_uri: input.redirectUri,
    response_type: "code",
    scope: GOOGLE_ADS_SCOPE,
    state: input.state,
  });

  return `${GOOGLE_OAUTH_AUTHORIZE_ENDPOINT}?${searchParams.toString()}`;
}

export async function exchangeGoogleAdsAuthCode(
  input: ExchangeGoogleAdsAuthCodeInput,
): Promise<GoogleAdsTokenExchangeResult> {
  return exchangeGoogleOauthToken(
    new URLSearchParams({
      client_id: input.clientId,
      client_secret: input.clientSecret,
      code: input.code,
      grant_type: "authorization_code",
      redirect_uri: input.redirectUri,
    }),
  );
}

export async function exchangeGoogleAdsRefreshToken(
  input: ExchangeGoogleAdsRefreshTokenInput,
): Promise<GoogleAdsTokenExchangeResult> {
  return exchangeGoogleOauthToken(
    new URLSearchParams({
      client_id: input.clientId,
      client_secret: input.clientSecret,
      grant_type: "refresh_token",
      refresh_token: input.refreshToken,
    }),
  );
}

export function maskGoogleAdsSecret(value: string, visibleCount = 4) {
  if (!value) {
    return "";
  }

  if (value.length <= visibleCount * 2) {
    return value;
  }

  return `${value.slice(0, visibleCount)}...${value.slice(-visibleCount)}`;
}
