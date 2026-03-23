"use server";

import { redirect } from "next/navigation";
import { createServerSupabaseClient } from "../../lib/supabase/server";
import { writeSavedSearchCampaignDraft, clearSavedSearchCampaignDraft } from "../../lib/draft-store";
import { buildWorkspaceDriveIntake, getWorkspaceSnapshot } from "../../lib/workspace";
import {
  clearWorkspaceDriveIntake,
  readWorkspaceDriveIntake,
  writeWorkspaceDriveIntake,
} from "../../lib/workspace-store";

async function getWorkspaceStoreContext() {
  const supabase = await createServerSupabaseClient();

  if (!supabase) {
    return {
      supabase: null,
      userId: null,
      userEmail: null,
    };
  }

  const {
    data: { user },
  } = await supabase.auth.getUser();

  return {
    supabase,
    userId: user?.id ?? null,
    userEmail: user?.email ?? null,
  };
}

export async function saveDriveIntakeAction(formData: FormData) {
  const intake = buildWorkspaceDriveIntake({
    googleAdsCustomerId: String(formData.get("googleAdsCustomerId") ?? ""),
    folderInput: String(formData.get("folderInput") ?? ""),
    objective: String(formData.get("objective") ?? ""),
    offerSummary: String(formData.get("offerSummary") ?? ""),
    landingPageUrl: String(formData.get("landingPageUrl") ?? ""),
    notes: String(formData.get("notes") ?? ""),
  });

  const context = await getWorkspaceStoreContext();
  await writeWorkspaceDriveIntake(intake, context);
  redirect("/dashboard");
}

export async function clearDriveIntakeAction() {
  const context = await getWorkspaceStoreContext();
  await clearWorkspaceDriveIntake(context);
  redirect("/dashboard");
}

export async function saveSearchCampaignDraftAction() {
  const context = await getWorkspaceStoreContext();
  const driveIntakeRecord = await readWorkspaceDriveIntake(context);
  const workspace = getWorkspaceSnapshot(context.userEmail, driveIntakeRecord.intake);

  if (workspace.searchCampaignDraft.status !== "ready") {
    redirect("/dashboard");
  }

  await writeSavedSearchCampaignDraft(
    {
      draft: workspace.searchCampaignDraft,
      sourceFolderId: driveIntakeRecord.intake.folderId,
    },
    context,
  );
  redirect("/dashboard");
}

export async function clearSavedSearchCampaignDraftAction() {
  const context = await getWorkspaceStoreContext();
  await clearSavedSearchCampaignDraft(context);
  redirect("/dashboard");
}
