"use server";

import { redirect } from "next/navigation";
import {
  approveSearchCampaignDraftForPublication,
  clearSearchCampaignDraftApproval,
  readSearchCampaignDraftApproval,
  requestSearchCampaignDraftChanges,
  submitSearchCampaignDraftForApproval,
} from "../../lib/draft-approval-store";
import { readSavedSearchCampaignDraft } from "../../lib/draft-store";
import { getSupabaseEnv } from "../../lib/env";
import { createServerSupabaseClient } from "../../lib/supabase/server";

async function getApprovalStoreContext() {
  const env = getSupabaseEnv();

  if (!env.isConfigured) {
    return {
      supabase: null,
      userId: null,
    };
  }

  const supabase = await createServerSupabaseClient();

  if (!supabase) {
    return {
      supabase: null,
      userId: null,
    };
  }

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?next=/dashboard");
  }

  return {
    supabase,
    userId: user.id,
  };
}

async function getSavedDraftOrRedirect() {
  const context = await getApprovalStoreContext();
  const savedDraftRecord = await readSavedSearchCampaignDraft(context);

  if (!savedDraftRecord.draft) {
    redirect("/dashboard");
  }

  return {
    context,
    draft: savedDraftRecord.draft,
    sourceFolderId: savedDraftRecord.sourceFolderId,
  };
}

async function getApprovalRecordOrRedirect() {
  const context = await getApprovalStoreContext();
  const approvalRecord = await readSearchCampaignDraftApproval(context);

  if (!approvalRecord.draft || !approvalRecord.hasApprovalRequest) {
    redirect("/dashboard");
  }

  return {
    context,
    draft: approvalRecord.draft,
    sourceFolderId: approvalRecord.sourceFolderId,
  };
}

export async function submitSearchCampaignDraftForApprovalAction() {
  const { context, draft, sourceFolderId } = await getSavedDraftOrRedirect();

  await submitSearchCampaignDraftForApproval(
    {
      draft,
      sourceFolderId,
    },
    context,
  );

  redirect("/dashboard");
}

export async function approveSearchCampaignDraftForPublicationAction() {
  const { context, draft, sourceFolderId } = await getApprovalRecordOrRedirect();

  await approveSearchCampaignDraftForPublication(
    {
      draft,
      sourceFolderId,
    },
    context,
  );

  redirect("/dashboard");
}

export async function requestSearchCampaignDraftChangesAction() {
  const { context, draft, sourceFolderId } = await getApprovalRecordOrRedirect();

  await requestSearchCampaignDraftChanges(
    {
      draft,
      sourceFolderId,
    },
    context,
  );

  redirect("/dashboard");
}

export async function clearSearchCampaignDraftApprovalAction() {
  const context = await getApprovalStoreContext();

  await clearSearchCampaignDraftApproval(context);

  redirect("/dashboard");
}
