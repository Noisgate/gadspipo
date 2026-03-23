import { cookies } from "next/headers";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { SearchCampaignDraftPreview } from "@adsmcp/domain";

const SEARCH_DRAFT_COOKIE_NAME = "adsmcp-search-draft";
const SEARCH_CAMPAIGN_DRAFTS_TABLE = "search_campaign_drafts";
const SEARCH_CAMPAIGN_DRAFTS_COLUMNS = [
  "owner_user_id",
  "campaign_name",
  "objective",
  "source_folder_id",
  "draft_payload",
  "created_at",
  "updated_at",
].join(", ");

type WorkspaceStoreContext = {
  supabase?: SupabaseClient | null;
  userId?: string | null;
};

type SearchCampaignDraftRow = {
  owner_user_id: string;
  campaign_name: string;
  objective: string;
  source_folder_id: string | null;
  draft_payload: SearchCampaignDraftPreview;
  created_at: string;
  updated_at: string;
};

export type SavedSearchCampaignDraftRecord = {
  draft: SearchCampaignDraftPreview | null;
  hasSavedDraft: boolean;
  sourceFolderId: string | null;
  persistenceMode: "workspace" | "preview_local";
  persistenceLabel: string;
  persistenceDetail: string;
  updatedAt: string | null;
};

function buildEmptyDraftRecord(): SavedSearchCampaignDraftRecord {
  return {
    draft: null,
    hasSavedDraft: false,
    sourceFolderId: null,
    persistenceMode: "preview_local",
    persistenceLabel: "Nenhum draft salvo",
    persistenceDetail:
      "O produto ainda nao tem um snapshot salvo desta campanha. Quando voce salvar, ele fica pronto para aprovacao futura.",
    updatedAt: null,
  };
}

function buildSavedDraftRecord(input: {
  draft: SearchCampaignDraftPreview;
  sourceFolderId?: string | null;
  persistenceMode: "workspace" | "preview_local";
  updatedAt: string | null;
}): SavedSearchCampaignDraftRecord {
  return {
    draft: input.draft,
    hasSavedDraft: true,
    sourceFolderId: input.sourceFolderId ?? null,
    persistenceMode: input.persistenceMode,
    persistenceLabel:
      input.persistenceMode === "workspace"
        ? "Draft salvo no workspace"
        : "Draft salvo localmente",
    persistenceDetail:
      input.persistenceMode === "workspace"
        ? "Este snapshot do draft ja esta persistido por usuario no Supabase e pronto para alimentar aprovacao e auditoria."
        : "Enquanto a tabela do workspace ainda nao estiver pronta, o snapshot do draft fica salvo em modo preview no proprio app.",
    updatedAt: input.updatedAt,
  };
}

async function readSearchCampaignDraftCookie(): Promise<SearchCampaignDraftPreview | null> {
  const cookieStore = await cookies();
  const rawValue = cookieStore.get(SEARCH_DRAFT_COOKIE_NAME)?.value;

  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as SearchCampaignDraftPreview;
  } catch {
    return null;
  }
}

async function writeSearchCampaignDraftCookie(
  value: SearchCampaignDraftPreview,
): Promise<void> {
  const cookieStore = await cookies();

  cookieStore.set(SEARCH_DRAFT_COOKIE_NAME, JSON.stringify(value), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });
}

async function clearSearchCampaignDraftCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SEARCH_DRAFT_COOKIE_NAME);
}

export async function readSavedSearchCampaignDraft(
  context: WorkspaceStoreContext = {},
): Promise<SavedSearchCampaignDraftRecord> {
  const cookieDraft = await readSearchCampaignDraftCookie();

  if (!context.supabase || !context.userId) {
    return cookieDraft
      ? buildSavedDraftRecord({
          draft: cookieDraft,
          sourceFolderId: null,
          persistenceMode: "preview_local",
          updatedAt: null,
        })
      : buildEmptyDraftRecord();
  }

  const { data, error } = await context.supabase
    .from(SEARCH_CAMPAIGN_DRAFTS_TABLE)
    .select(SEARCH_CAMPAIGN_DRAFTS_COLUMNS)
    .eq("owner_user_id", context.userId)
    .maybeSingle<SearchCampaignDraftRow>();

  if (error || !data) {
    return cookieDraft
      ? buildSavedDraftRecord({
          draft: cookieDraft,
          sourceFolderId: null,
          persistenceMode: "preview_local",
          updatedAt: null,
        })
      : buildEmptyDraftRecord();
  }

  return buildSavedDraftRecord({
    draft: data.draft_payload,
    sourceFolderId: data.source_folder_id,
    persistenceMode: "workspace",
    updatedAt: data.updated_at ?? null,
  });
}

export async function writeSavedSearchCampaignDraft(
  input: {
    draft: SearchCampaignDraftPreview;
    sourceFolderId?: string | null;
  },
  context: WorkspaceStoreContext = {},
): Promise<SavedSearchCampaignDraftRecord> {
  await writeSearchCampaignDraftCookie(input.draft);

  if (!context.supabase || !context.userId) {
    return buildSavedDraftRecord({
      draft: input.draft,
      sourceFolderId: input.sourceFolderId ?? null,
      persistenceMode: "preview_local",
      updatedAt: null,
    });
  }

  const { data, error } = await context.supabase
    .from(SEARCH_CAMPAIGN_DRAFTS_TABLE)
    .upsert(
      {
        owner_user_id: context.userId,
        campaign_name: input.draft.campaignName,
        objective: input.draft.objective,
        source_folder_id: input.sourceFolderId ?? null,
        draft_payload: input.draft,
      },
      {
        onConflict: "owner_user_id",
      },
    )
    .select("updated_at")
    .single<{ updated_at: string }>();

  if (error) {
    return buildSavedDraftRecord({
      draft: input.draft,
      persistenceMode: "preview_local",
      updatedAt: null,
    });
  }

  return buildSavedDraftRecord({
    draft: input.draft,
    sourceFolderId: input.sourceFolderId ?? null,
    persistenceMode: "workspace",
    updatedAt: data?.updated_at ?? null,
  });
}

export async function clearSavedSearchCampaignDraft(
  context: WorkspaceStoreContext = {},
): Promise<void> {
  await clearSearchCampaignDraftCookie();

  if (!context.supabase || !context.userId) {
    return;
  }

  await context.supabase
    .from(SEARCH_CAMPAIGN_DRAFTS_TABLE)
    .delete()
    .eq("owner_user_id", context.userId);
}
