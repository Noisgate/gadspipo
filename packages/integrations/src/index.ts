export type IntegrationGateway = {
  name: string;
};

export function createGoogleAdsGateway(): IntegrationGateway {
  return {
    name: "google-ads",
  };
}

export function createGoogleDriveGateway(): IntegrationGateway {
  return {
    name: "google-drive",
  };
}

export function createLlmGateway(): IntegrationGateway {
  return {
    name: "llm-provider",
  };
}
