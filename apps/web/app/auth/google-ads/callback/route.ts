import { NextResponse } from "next/server";
import {
  buildGoogleAdsOauthRedirectUri,
  exchangeGoogleAdsAuthCode,
  getGoogleAdsOauthEnv,
  maskGoogleAdsSecret,
} from "../../../../lib/google-ads-oauth";

const GOOGLE_ADS_OAUTH_STATE_COOKIE = "google_ads_oauth_state";

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderHtmlPage(input: {
  title: string;
  description: string;
  details?: string[];
  snippet?: string;
  tone: "success" | "warning";
  dashboardUrl: string;
}) {
  const badgeLabel =
    input.tone === "success" ? "OAuth concluido" : "OAuth exige atencao";
  const detailsMarkup = (input.details ?? [])
    .map((detail) => `<li>${escapeHtml(detail)}</li>`)
    .join("");
  const snippetMarkup = input.snippet
    ? `<pre>${escapeHtml(input.snippet)}</pre>`
    : "";

  return `<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(input.title)}</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f4efe7;
        --surface: rgba(255, 255, 255, 0.9);
        --text: #1b1712;
        --muted: #665c51;
        --line: rgba(27, 23, 18, 0.12);
        --success: #1f4f46;
        --warning: #835d22;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        padding: 24px;
        background:
          radial-gradient(circle at top left, rgba(31, 79, 70, 0.12), transparent 30%),
          radial-gradient(circle at bottom right, rgba(155, 122, 79, 0.12), transparent 26%),
          var(--bg);
        color: var(--text);
        font-family: "Avenir Next", "Segoe UI", sans-serif;
      }

      main {
        width: min(760px, 100%);
        padding: 28px;
        border: 1px solid var(--line);
        border-radius: 28px;
        background: var(--surface);
        box-shadow: 0 24px 80px rgba(34, 26, 18, 0.08);
      }

      .badge {
        display: inline-flex;
        align-items: center;
        min-height: 34px;
        padding: 0 12px;
        border-radius: 999px;
        border: 1px solid var(--line);
        color: ${input.tone === "success" ? "var(--success)" : "var(--warning)"};
        background: ${
          input.tone === "success"
            ? "rgba(31, 79, 70, 0.1)"
            : "rgba(155, 122, 79, 0.12)"
        };
        font-size: 0.85rem;
      }

      h1 {
        margin: 18px 0 0;
        font: 500 clamp(2.2rem, 5vw, 3.4rem) / 0.96 "Iowan Old Style", "Palatino Linotype", serif;
        letter-spacing: -0.04em;
      }

      p,
      li {
        color: var(--muted);
        line-height: 1.75;
        font-size: 1rem;
      }

      ul {
        margin: 18px 0 0;
        padding-left: 20px;
      }

      pre {
        margin: 18px 0 0;
        padding: 16px;
        border-radius: 20px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.72);
        white-space: pre-wrap;
        word-break: break-word;
        font: 0.88rem/1.7 "SFMono-Regular", "IBM Plex Mono", monospace;
        color: var(--text);
      }

      a {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 44px;
        margin-top: 20px;
        padding: 0 18px;
        border-radius: 999px;
        background: var(--text);
        color: #fbf8f3;
        text-decoration: none;
      }
    </style>
  </head>
  <body>
    <main>
      <span class="badge">${escapeHtml(badgeLabel)}</span>
      <h1>${escapeHtml(input.title)}</h1>
      <p>${escapeHtml(input.description)}</p>
      ${detailsMarkup ? `<ul>${detailsMarkup}</ul>` : ""}
      ${snippetMarkup}
      <a href="${escapeHtml(input.dashboardUrl)}">Voltar ao dashboard</a>
    </main>
  </body>
</html>`;
}

function buildHtmlResponse(input: {
  title: string;
  description: string;
  details?: string[];
  snippet?: string;
  tone: "success" | "warning";
  dashboardUrl: string;
}) {
  const response = new NextResponse(renderHtmlPage(input), {
    headers: {
      "content-type": "text/html; charset=utf-8",
    },
  });

  response.cookies.delete(GOOGLE_ADS_OAUTH_STATE_COOKIE);

  return response;
}

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const dashboardUrl = new URL("/dashboard", requestUrl.origin).toString();
  const error = requestUrl.searchParams.get("error");
  const errorDescription = requestUrl.searchParams.get("error_description");
  const code = requestUrl.searchParams.get("code");
  const state = requestUrl.searchParams.get("state");
  const oauthEnv = getGoogleAdsOauthEnv();
  const storedState = request.headers
    .get("cookie")
    ?.split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${GOOGLE_ADS_OAUTH_STATE_COOKIE}=`))
    ?.split("=")[1];

  if (!oauthEnv.isReady) {
    return buildHtmlResponse({
      title: "Faltam credenciais do app OAuth",
      description:
        "O callback do Google voltou, mas o app nao encontrou client id e client secret suficientes para trocar o code por tokens.",
      details: [
        "Preencha GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET no ambiente local do web app.",
        "Reinicie o servidor do Next.js antes de tentar novamente.",
      ],
      tone: "warning",
      dashboardUrl,
    });
  }

  if (error) {
    return buildHtmlResponse({
      title: "O consentimento do Google nao foi concluido",
      description:
        "O Google retornou um erro antes da troca de tokens, entao o refresh token ainda nao foi gerado.",
      details: [error, errorDescription ?? "Sem detalhes adicionais."],
      tone: "warning",
      dashboardUrl,
    });
  }

  if (!code || !state || !storedState || state !== storedState) {
    return buildHtmlResponse({
      title: "Nao foi possivel validar o retorno do OAuth",
      description:
        "O estado do consentimento nao bateu com o valor esperado, entao o app bloqueou a troca de tokens por seguranca.",
      details: [
        "Tente iniciar novamente pelo botao de conexao no dashboard.",
        "Se o erro persistir, confira se o callback esta voltando para a mesma URL usada no inicio do fluxo.",
      ],
      tone: "warning",
      dashboardUrl,
    });
  }

  try {
    const tokenResult = await exchangeGoogleAdsAuthCode({
      clientId: oauthEnv.clientId,
      clientSecret: oauthEnv.clientSecret,
      code,
      redirectUri: buildGoogleAdsOauthRedirectUri(requestUrl.origin),
    });
    const snippet = tokenResult.refreshToken
      ? `GOOGLE_ADS_REFRESH_TOKEN=${tokenResult.refreshToken}`
      : "";

    return buildHtmlResponse({
      title: tokenResult.refreshToken
        ? "Refresh token gerado para o Google Ads"
        : "O Google respondeu sem refresh token",
      description: tokenResult.refreshToken
        ? "A etapa de OAuth do Google Ads foi concluida. Agora falta salvar o refresh token localmente e adicionar o developer token da API."
        : "A troca de code por token funcionou, mas o Google nao devolveu um refresh token novo nesta resposta.",
      details: tokenResult.refreshToken
        ? [
            "Adicione a linha abaixo em apps/web/.env.local ou no seu ~/.google-ads.yaml.",
            "Garanta tambem GOOGLE_ADS_DEVELOPER_TOKEN antes de voltar ao dashboard.",
            `Access token temporario emitido com escopo ${tokenResult.scope ?? "nao informado"}.`,
          ]
        : [
            "Isso costuma acontecer quando o usuario ja autorizou esse client antes.",
            "Revogue o acesso do app na Conta Google e rode o fluxo novamente se precisar de um novo refresh token.",
            `Access token temporario emitido como ${maskGoogleAdsSecret(tokenResult.accessToken)}.`,
          ],
      snippet,
      tone: tokenResult.refreshToken ? "success" : "warning",
      dashboardUrl,
    });
  } catch (caughtError) {
    const message =
      caughtError instanceof Error
        ? caughtError.message
        : "Falha inesperada ao trocar o code por tokens.";

    return buildHtmlResponse({
      title: "Falha ao trocar o code por tokens",
      description:
        "O consentimento chegou ate o callback, mas a chamada para o endpoint de tokens do Google nao foi aceita.",
      details: [
        message,
        "Confirme se este callback esta cadastrado como redirect URI no Google Cloud Console.",
      ],
      tone: "warning",
      dashboardUrl,
    });
  }
}
