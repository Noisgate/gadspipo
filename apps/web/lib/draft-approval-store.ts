import { cookies } from "next/headers";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { SearchCampaignDraftPreview } from "@adsmcp/domain";
import { getPostgresPool } from "./postgres/server";

const SEARCH_DRAFT_APPROVAL_COOKIE_NAME = "adsmcp-search-draft-approval";
const SEARCH_CAMPAIGN_DRAFT_APPROVALS_TABLE = "search_campaign_draft_approvals";
const SEARCH_CAMPAIGN_DRAFT_APPROVALS_COLUMNS = [
  "owner_user_id",
  "campaign_name",
  "objective",
  "source_folder_id",
  "draft_payload",
  "approval_status",
  "approval_summary",
  "approved_at",
  "created_at",
  "updated_at",
].join(", ");

type WorkspaceStoreContext = {
  supabase?: SupabaseClient | null;
  userId?: string | null;
};

type ApprovalStatus = "pending_review" | "approved" | "changes_requested";

type SearchCampaignDraftApprovalRow = {
  owner_user_id: string;
  campaign_name: string;
  objective: string;
  source_folder_id: string | null;
  draft_payload: SearchCampaignDraftPreview;
  approval_status: ApprovalStatus;
  approval_summary: string;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
};

type SearchCampaignDraftApprovalCookie = {
  draft: SearchCampaignDraftPreview;
  sourceFolderId: string | null;
  approvalStatus: ApprovalStatus;
  approvalSummary: string;
  approvedAt: string | null;
  updatedAt: string | null;
};

export type SearchCampaignDraftApprovalRecord = {
  draft: SearchCampaignDraftPreview | null;
  sourceFolderId: string | null;
  hasApprovalRequest: boolean;
  status: "not_requested" | ApprovalStatus;
  statusLabel: string;
  statusDetail: string;
  approvalSummary: string | null;
  persistenceMode: "workspace" | "preview_local";
  persistenceLabel: string;
  updatedAt: string | null;
  approvedAt: string | null;
};

function buildEmptyApprovalRecord(): SearchCampaignDraftApprovalRecord {
  return {
    draft: null,
    sourceFolderId: null,
    hasApprovalRequest: false,
    status: "not_requested",
    statusLabel: "Aguardando envio para aprovacao",
    statusDetail:
      "Quando o snapshot do draft estiver salvo, voce pode envia-lo para aprovacao e manter a decisao registrada antes da publicacao.",
    approvalSummary: null,
    persistenceMode: "preview_local",
    persistenceLabel: "Sem aprovacao registrada",
    updatedAt: null,
    approvedAt: null,
  };
}

function getStatusCopy(status: ApprovalStatus) {
  if (status === "approved") {
    return {
      label: "Aprovado para publicacao",
      detail:
        "Este snapshot ja foi aprovado e pode alimentar a proxima etapa de publicacao assistida no Google Ads.",
    };
  }

  if (status === "changes_requested") {
    return {
      label: "Ajustes solicitados",
      detail:
        "O draft precisa de mais refinamento antes de seguir para publicacao. Salve um novo snapshot e reenvie quando estiver pronto.",
    };
  }

  return {
    label: "Em aprovacao",
    detail:
      "O snapshot salvo ja foi enviado para aprovacao. O proximo passo e aprovar para publicar ou solicitar ajustes.",
  };
}

function buildApprovalRecord(input: {
  draft: SearchCampaignDraftPreview;
  sourceFolderId?: string | null;
  approvalStatus: ApprovalStatus;
  approvalSummary: string;
  approvedAt: string | null;
  persistenceMode: "workspace" | "preview_local";
  updatedAt: string | null;
}): SearchCampaignDraftApprovalRecord {
  const statusCopy = getStatusCopy(input.approvalStatus);

  return {
    draft: input.draft,
    sourceFolderId: input.sourceFolderId ?? null,
    hasApprovalRequest: true,
    status: input.approvalStatus,
    statusLabel: statusCopy.label,
    statusDetail: statusCopy.detail,
    approvalSummary: input.approvalSummary,
    persistenceMode: input.persistenceMode,
    persistenceLabel:
      input.persistenceMode === "workspace"
        ? "Aprovacao salva no workspace"
        : "Aprovacao salva localmente",
    updatedAt: input.updatedAt,
    approvedAt: input.approvedAt,
  };
}

async function readDraftApprovalCookie(): Promise<SearchCampaignDraftApprovalCookie | null> {
  const cookieStore = await cookies();
  const rawValue = cookieStore.get(SEARCH_DRAFT_APPROVAL_COOKIE_NAME)?.value;

  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as SearchCampaignDraftApprovalCookie;
  } catch {
    return null;
  }
}

async function writeDraftApprovalCookie(
  value: SearchCampaignDraftApprovalCookie,
): Promise<void> {
  const cookieStore = await cookies();

  cookieStore.set(SEARCH_DRAFT_APPROVAL_COOKIE_NAME, JSON.stringify(value), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });
}

async function clearDraftApprovalCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(SEARCH_DRAFT_APPROVAL_COOKIE_NAME);
}

export async function readSearchCampaignDraftApproval(
  context: WorkspaceStoreContext = {},
): Promise<SearchCampaignDraftApprovalRecord> {
  const cookieApproval = await readDraftApprovalCookie();
  const postgres = getPostgresPool();

  if (postgres && context.userId) {
    try {
      const result = await postgres.query<SearchCampaignDraftApprovalRow>(
        `select ${SEARCH_CAMPAIGN_DRAFT_APPROVALS_COLUMNS}
         from public.${SEARCH_CAMPAIGN_DRAFT_APPROVALS_TABLE}
         where owner_user_id = $1
         limit 1`,
        [context.userId],
      );
      const row = result.rows[0];

      if (row) {
        return buildApprovalRecord({
          draft: row.draft_payload,
          sourceFolderId: row.source_folder_id,
          approvalStatus: row.approval_status,
          approvalSummary: row.approval_summary,
          approvedAt: row.approved_at,
          persistenceMode: "workspace",
          updatedAt: row.updated_at,
        });
      }
    } catch {
      // Fall through to the existing Supabase/cookie path if direct Postgres is unavailable.
    }
  }

  if (!context.supabase || !context.userId) {
    return cookieApproval
      ? buildApprovalRecord({
          draft: cookieApproval.draft,
          sourceFolderId: cookieApproval.sourceFolderId,
          approvalStatus: cookieApproval.approvalStatus,
          approvalSummary: cookieApproval.approvalSummary,
          approvedAt: cookieApproval.approvedAt,
          persistenceMode: "preview_local",
          updatedAt: cookieApproval.updatedAt,
        })
      : buildEmptyApprovalRecord();
  }

  const { data, error } = await context.supabase
    .from(SEARCH_CAMPAIGN_DRAFT_APPROVALS_TABLE)
    .select(SEARCH_CAMPAIGN_DRAFT_APPROVALS_COLUMNS)
    .eq("owner_user_id", context.userId)
    .maybeSingle<SearchCampaignDraftApprovalRow>();

  if (error || !data) {
    return cookieApproval
      ? buildApprovalRecord({
          draft: cookieApproval.draft,
          sourceFolderId: cookieApproval.sourceFolderId,
          approvalStatus: cookieApproval.approvalStatus,
          approvalSummary: cookieApproval.approvalSummary,
          approvedAt: cookieApproval.approvedAt,
          persistenceMode: "preview_local",
          updatedAt: cookieApproval.updatedAt,
        })
      : buildEmptyApprovalRecord();
  }

  return buildApprovalRecord({
    draft: data.draft_payload,
    sourceFolderId: data.source_folder_id,
    approvalStatus: data.approval_status,
    approvalSummary: data.approval_summary,
    approvedAt: data.approved_at,
    persistenceMode: "workspace",
    updatedAt: data.updated_at,
  });
}

async function persistDraftApproval(
  input: {
    draft: SearchCampaignDraftPreview;
    sourceFolderId?: string | null;
    approvalStatus: ApprovalStatus;
    approvalSummary: string;
    approvedAt: string | null;
  },
  context: WorkspaceStoreContext = {},
): Promise<SearchCampaignDraftApprovalRecord> {
  const updatedAt = new Date().toISOString();

  await writeDraftApprovalCookie({
    draft: input.draft,
    sourceFolderId: input.sourceFolderId ?? null,
    approvalStatus: input.approvalStatus,
    approvalSummary: input.approvalSummary,
    approvedAt: input.approvedAt,
    updatedAt,
  });
  const postgres = getPostgresPool();

  if (postgres && context.userId) {
    try {
      const result = await postgres.query<{ updated_at: string }>(
        `insert into public.${SEARCH_CAMPAIGN_DRAFT_APPROVALS_TABLE} (
          owner_user_id,
          campaign_name,
          objective,
          source_folder_id,
          draft_payload,
          approval_status,
          approval_summary,
          approved_at
        ) values ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)
        on conflict (owner_user_id) do update
        set
          campaign_name = excluded.campaign_name,
          objective = excluded.objective,
          source_folder_id = excluded.source_folder_id,
          draft_payload = excluded.draft_payload,
          approval_status = excluded.approval_status,
          approval_summary = excluded.approval_summary,
          approved_at = excluded.approved_at
        returning updated_at`,
        [
          context.userId,
          input.draft.campaignName,
          input.draft.objective,
          input.sourceFolderId ?? null,
          JSON.stringify(input.draft),
          input.approvalStatus,
          input.approvalSummary,
          input.approvedAt,
        ],
      );

      return buildApprovalRecord({
        draft: input.draft,
        sourceFolderId: input.sourceFolderId,
        approvalStatus: input.approvalStatus,
        approvalSummary: input.approvalSummary,
        approvedAt: input.approvedAt,
        persistenceMode: "workspace",
        updatedAt: result.rows[0]?.updated_at ?? updatedAt,
      });
    } catch {
      // Fall through to the existing Supabase/cookie path if direct Postgres is unavailable.
    }
  }

  if (!context.supabase || !context.userId) {
    return buildApprovalRecord({
      draft: input.draft,
      sourceFolderId: input.sourceFolderId,
      approvalStatus: input.approvalStatus,
      approvalSummary: input.approvalSummary,
      approvedAt: input.approvedAt,
      persistenceMode: "preview_local",
      updatedAt,
    });
  }

  const { data, error } = await context.supabase
    .from(SEARCH_CAMPAIGN_DRAFT_APPROVALS_TABLE)
    .upsert(
      {
        owner_user_id: context.userId,
        campaign_name: input.draft.campaignName,
        objective: input.draft.objective,
        source_folder_id: input.sourceFolderId ?? null,
        draft_payload: input.draft,
        approval_status: input.approvalStatus,
        approval_summary: input.approvalSummary,
        approved_at: input.approvedAt,
      },
      {
        onConflict: "owner_user_id",
      },
    )
    .select("updated_at, approved_at")
    .single<{ updated_at: string; approved_at: string | null }>();

  if (error) {
    return buildApprovalRecord({
      draft: input.draft,
      sourceFolderId: input.sourceFolderId,
      approvalStatus: input.approvalStatus,
      approvalSummary: input.approvalSummary,
      approvedAt: input.approvedAt,
      persistenceMode: "preview_local",
      updatedAt,
    });
  }

  return buildApprovalRecord({
    draft: input.draft,
    sourceFolderId: input.sourceFolderId,
    approvalStatus: input.approvalStatus,
    approvalSummary: input.approvalSummary,
    approvedAt: data?.approved_at ?? input.approvedAt,
    persistenceMode: "workspace",
    updatedAt: data?.updated_at ?? updatedAt,
  });
}

export async function submitSearchCampaignDraftForApproval(
  input: {
    draft: SearchCampaignDraftPreview;
    sourceFolderId?: string | null;
  },
  context: WorkspaceStoreContext = {},
): Promise<SearchCampaignDraftApprovalRecord> {
  return persistDraftApproval(
    {
      draft: input.draft,
      sourceFolderId: input.sourceFolderId,
      approvalStatus: "pending_review",
      approvalSummary:
        "Snapshot enviado para aprovacao manual antes da publicacao. Aguardando decisao do dono do negocio.",
      approvedAt: null,
    },
    context,
  );
}

export async function approveSearchCampaignDraftForPublication(
  input: {
    draft: SearchCampaignDraftPreview;
    sourceFolderId?: string | null;
  },
  context: WorkspaceStoreContext = {},
): Promise<SearchCampaignDraftApprovalRecord> {
  const approvedAt = new Date().toISOString();

  return persistDraftApproval(
    {
      draft: input.draft,
      sourceFolderId: input.sourceFolderId,
      approvalStatus: "approved",
      approvalSummary:
        "Draft aprovado para alimentar a etapa de publicacao assistida. O proximo passo e mapear essa aprovacao para a rotina de publishing.",
      approvedAt,
    },
    context,
  );
}

export async function requestSearchCampaignDraftChanges(
  input: {
    draft: SearchCampaignDraftPreview;
    sourceFolderId?: string | null;
  },
  context: WorkspaceStoreContext = {},
): Promise<SearchCampaignDraftApprovalRecord> {
  return persistDraftApproval(
    {
      draft: input.draft,
      sourceFolderId: input.sourceFolderId,
      approvalStatus: "changes_requested",
      approvalSummary:
        "O draft foi devolvido para refinamento antes da publicacao. Gere um novo snapshot e reenvie quando estiver pronto.",
      approvedAt: null,
    },
    context,
  );
}

export async function clearSearchCampaignDraftApproval(
  context: WorkspaceStoreContext = {},
): Promise<void> {
  await clearDraftApprovalCookie();
  const postgres = getPostgresPool();

  if (postgres && context.userId) {
    try {
      await postgres.query(
        `delete from public.${SEARCH_CAMPAIGN_DRAFT_APPROVALS_TABLE}
         where owner_user_id = $1`,
        [context.userId],
      );
      return;
    } catch {
      // Fall through to the existing Supabase path if direct Postgres is unavailable.
    }
  }

  if (!context.supabase || !context.userId) {
    return;
  }

  await context.supabase
    .from(SEARCH_CAMPAIGN_DRAFT_APPROVALS_TABLE)
    .delete()
    .eq("owner_user_id", context.userId);
}
