import { cookies } from "next/headers";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { WorkspaceDriveIntake } from "@adsmcp/domain";
import { getPostgresPool } from "./postgres/server";
import { buildWorkspaceDriveIntake } from "./workspace";

const WORKSPACE_COOKIE_NAME = "adsmcp-workspace-intake";
const WORKSPACE_CAMPAIGN_INTAKES_TABLE = "workspace_campaign_intakes";
const WORKSPACE_CAMPAIGN_INTAKES_COLUMNS = [
  "owner_user_id",
  "google_ads_customer_id",
  "drive_folder_input",
  "drive_folder_id",
  "objective",
  "offer_summary",
  "landing_page_url",
  "notes",
  "created_at",
  "updated_at",
].join(", ");

type WorkspaceStoreContext = {
  supabase?: SupabaseClient | null;
  userId?: string | null;
};

type WorkspaceCampaignIntakeRow = {
  owner_user_id: string;
  google_ads_customer_id: string;
  drive_folder_input: string;
  drive_folder_id: string | null;
  objective: string;
  offer_summary: string;
  landing_page_url: string;
  notes: string;
  created_at: string;
  updated_at: string;
};

export type WorkspaceDriveIntakeRecord = {
  intake: WorkspaceDriveIntake;
  persistenceMode: "workspace" | "preview_local";
  persistenceLabel: string;
  persistenceDetail: string;
  updatedAt: string | null;
};

function buildPreviewRecord(
  intake: WorkspaceDriveIntake,
): WorkspaceDriveIntakeRecord {
  return {
    intake,
    persistenceMode: "preview_local",
    persistenceLabel: "Contexto salvo localmente",
    persistenceDetail:
      "Enquanto a tabela do workspace ainda nao estiver pronta, o intake continua salvo em modo preview no proprio app.",
    updatedAt: null,
  };
}

function buildWorkspaceRecord(
  intake: WorkspaceDriveIntake,
  updatedAt: string | null,
): WorkspaceDriveIntakeRecord {
  return {
    intake,
    persistenceMode: "workspace",
    persistenceLabel: "Contexto salvo no workspace",
    persistenceDetail:
      "O intake ja esta persistido por usuario no banco do workspace e pronto para acompanhar a evolucao real do produto.",
    updatedAt,
  };
}

function mapRowToDriveIntake(
  row: WorkspaceCampaignIntakeRow,
): WorkspaceDriveIntake {
  return buildWorkspaceDriveIntake({
    googleAdsCustomerId: row.google_ads_customer_id,
    folderInput: row.drive_folder_input,
    objective: row.objective,
    offerSummary: row.offer_summary,
    landingPageUrl: row.landing_page_url,
    notes: row.notes,
  });
}

function mapDriveIntakeToRow(
  userId: string,
  intake: WorkspaceDriveIntake,
) {
  return {
    owner_user_id: userId,
    google_ads_customer_id: intake.googleAdsCustomerId,
    drive_folder_input: intake.folderInput,
    drive_folder_id: intake.folderId,
    objective: intake.objective,
    offer_summary: intake.offerSummary,
    landing_page_url: intake.landingPageUrl,
    notes: intake.notes,
  };
}

async function readWorkspaceDriveIntakeCookie(): Promise<WorkspaceDriveIntake> {
  const cookieStore = await cookies();
  const rawValue = cookieStore.get(WORKSPACE_COOKIE_NAME)?.value;

  if (!rawValue) {
    return buildWorkspaceDriveIntake();
  }

  try {
    const parsed = JSON.parse(rawValue) as Partial<WorkspaceDriveIntake>;

    return buildWorkspaceDriveIntake(parsed);
  } catch {
    return buildWorkspaceDriveIntake();
  }
}

async function writeWorkspaceDriveIntakeCookie(
  value: WorkspaceDriveIntake,
): Promise<void> {
  const cookieStore = await cookies();

  cookieStore.set(WORKSPACE_COOKIE_NAME, JSON.stringify(value), {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 60 * 60 * 24 * 30,
  });
}

async function clearWorkspaceDriveIntakeCookie(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(WORKSPACE_COOKIE_NAME);
}

export async function readWorkspaceDriveIntake(
  context: WorkspaceStoreContext = {},
): Promise<WorkspaceDriveIntakeRecord> {
  const cookieIntake = await readWorkspaceDriveIntakeCookie();
  const postgres = getPostgresPool();

  if (postgres && context.userId) {
    try {
      const result = await postgres.query<WorkspaceCampaignIntakeRow>(
        `select ${WORKSPACE_CAMPAIGN_INTAKES_COLUMNS}
         from public.${WORKSPACE_CAMPAIGN_INTAKES_TABLE}
         where owner_user_id = $1
         limit 1`,
        [context.userId],
      );

      if (result.rows[0]) {
        return buildWorkspaceRecord(
          mapRowToDriveIntake(result.rows[0]),
          result.rows[0].updated_at ?? null,
        );
      }
    } catch {
      // Fall through to the existing Supabase/cookie path if direct Postgres is unavailable.
    }
  }

  if (!context.supabase || !context.userId) {
    return buildPreviewRecord(cookieIntake);
  }

  const { data, error } = await context.supabase
    .from(WORKSPACE_CAMPAIGN_INTAKES_TABLE)
    .select(WORKSPACE_CAMPAIGN_INTAKES_COLUMNS)
    .eq("owner_user_id", context.userId)
    .maybeSingle<WorkspaceCampaignIntakeRow>();

  if (error || !data) {
    return buildPreviewRecord(cookieIntake);
  }

  return buildWorkspaceRecord(mapRowToDriveIntake(data), data.updated_at ?? null);
}

export async function writeWorkspaceDriveIntake(
  value: WorkspaceDriveIntake,
  context: WorkspaceStoreContext = {},
): Promise<WorkspaceDriveIntakeRecord> {
  await writeWorkspaceDriveIntakeCookie(value);
  const postgres = getPostgresPool();

  if (postgres && context.userId) {
    try {
      const row = mapDriveIntakeToRow(context.userId, value);
      const result = await postgres.query<{ updated_at: string }>(
        `insert into public.${WORKSPACE_CAMPAIGN_INTAKES_TABLE} (
          owner_user_id,
          google_ads_customer_id,
          drive_folder_input,
          drive_folder_id,
          objective,
          offer_summary,
          landing_page_url,
          notes
        ) values ($1, $2, $3, $4, $5, $6, $7, $8)
        on conflict (owner_user_id) do update
        set
          google_ads_customer_id = excluded.google_ads_customer_id,
          drive_folder_input = excluded.drive_folder_input,
          drive_folder_id = excluded.drive_folder_id,
          objective = excluded.objective,
          offer_summary = excluded.offer_summary,
          landing_page_url = excluded.landing_page_url,
          notes = excluded.notes
        returning updated_at`,
        [
          row.owner_user_id,
          row.google_ads_customer_id,
          row.drive_folder_input,
          row.drive_folder_id,
          row.objective,
          row.offer_summary,
          row.landing_page_url,
          row.notes,
        ],
      );

      return buildWorkspaceRecord(value, result.rows[0]?.updated_at ?? null);
    } catch {
      // Fall through to the existing Supabase/cookie path if direct Postgres is unavailable.
    }
  }

  if (!context.supabase || !context.userId) {
    return buildPreviewRecord(value);
  }

  const { data, error } = await context.supabase
    .from(WORKSPACE_CAMPAIGN_INTAKES_TABLE)
    .upsert(mapDriveIntakeToRow(context.userId, value), {
      onConflict: "owner_user_id",
    })
    .select("updated_at")
    .single<{ updated_at: string }>();

  if (error) {
    return buildPreviewRecord(value);
  }

  return buildWorkspaceRecord(value, data?.updated_at ?? null);
}

export async function clearWorkspaceDriveIntake(
  context: WorkspaceStoreContext = {},
): Promise<void> {
  await clearWorkspaceDriveIntakeCookie();
  const postgres = getPostgresPool();

  if (postgres && context.userId) {
    try {
      await postgres.query(
        `delete from public.${WORKSPACE_CAMPAIGN_INTAKES_TABLE}
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
    .from(WORKSPACE_CAMPAIGN_INTAKES_TABLE)
    .delete()
    .eq("owner_user_id", context.userId);
}
