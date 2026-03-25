import { NextResponse } from "next/server";
import {
  buildGoogleAdsAuthUrl,
  buildGoogleAdsOauthRedirectUri,
  createGoogleAdsOauthState,
  getGoogleAdsOauthEnv,
} from "../../../../lib/google-ads-oauth";

const GOOGLE_ADS_OAUTH_STATE_COOKIE = "google_ads_oauth_state";

export function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const oauthEnv = getGoogleAdsOauthEnv();

  if (!oauthEnv.isReady) {
    return NextResponse.redirect(new URL("/dashboard", requestUrl.origin));
  }

  const state = createGoogleAdsOauthState();
  const redirectUri = buildGoogleAdsOauthRedirectUri(requestUrl.origin);
  const authUrl = buildGoogleAdsAuthUrl({
    clientId: oauthEnv.clientId,
    redirectUri,
    state,
  });
  const response = NextResponse.redirect(authUrl);

  response.cookies.set(GOOGLE_ADS_OAUTH_STATE_COOKIE, state, {
    httpOnly: true,
    maxAge: 60 * 10,
    path: "/",
    sameSite: "lax",
    secure: requestUrl.protocol === "https:",
  });

  return response;
}
