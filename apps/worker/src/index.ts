import {
  campaignObjectiveOptions,
  defaultGuardrails,
  mvpFeatureSequence,
} from "@adsmcp/domain";
import {
  createGoogleAdsGateway,
  createGoogleDriveGateway,
  createLlmGateway,
} from "@adsmcp/integrations";
import { campaignDraftSystemPrompt } from "@adsmcp/prompts";

const googleAds = createGoogleAdsGateway();
const googleDrive = createGoogleDriveGateway();
const llm = createLlmGateway();

function bootstrapWorker() {
  console.log("adsmcp worker booting...");
  console.log("supported campaign objectives:", campaignObjectiveOptions.join(", "));
  console.log("mvp sequence:", mvpFeatureSequence.map((item) => item.id).join(" -> "));
  console.log("default guardrails:", JSON.stringify(defaultGuardrails, null, 2));
  console.log("prompt template loaded:", campaignDraftSystemPrompt.slice(0, 72) + "...");
  console.log("registered integrations:", {
    googleAds: googleAds.name,
    googleDrive: googleDrive.name,
    llm: llm.name,
  });
}

bootstrapWorker();
