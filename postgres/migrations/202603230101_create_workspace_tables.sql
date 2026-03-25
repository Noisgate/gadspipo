create table if not exists public.workspace_campaign_intakes (
  owner_user_id uuid primary key,
  google_ads_customer_id text not null default '',
  drive_folder_input text not null default '',
  drive_folder_id text,
  objective text not null default 'leads',
  offer_summary text not null default '',
  landing_page_url text not null default '',
  notes text not null default '',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint workspace_campaign_intakes_objective_check
    check (objective in ('leads', 'vendas', 'agendamentos', 'trafego qualificado'))
);

create table if not exists public.search_campaign_drafts (
  owner_user_id uuid primary key,
  campaign_name text not null,
  objective text not null,
  source_folder_id text,
  draft_payload jsonb not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint search_campaign_drafts_objective_check
    check (objective in ('leads', 'vendas', 'agendamentos', 'trafego qualificado'))
);

create table if not exists public.search_campaign_draft_approvals (
  owner_user_id uuid primary key,
  campaign_name text not null,
  objective text not null,
  source_folder_id text,
  draft_payload jsonb not null,
  approval_status text not null,
  approval_summary text not null,
  approved_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint search_campaign_draft_approvals_objective_check
    check (objective in ('leads', 'vendas', 'agendamentos', 'trafego qualificado')),
  constraint search_campaign_draft_approvals_status_check
    check (approval_status in ('pending_review', 'approved', 'changes_requested'))
);

create or replace function public.handle_workspace_campaign_intakes_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create or replace function public.handle_search_campaign_drafts_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create or replace function public.handle_search_campaign_draft_approvals_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists set_workspace_campaign_intakes_updated_at
on public.workspace_campaign_intakes;

create trigger set_workspace_campaign_intakes_updated_at
before update on public.workspace_campaign_intakes
for each row
execute function public.handle_workspace_campaign_intakes_updated_at();

drop trigger if exists set_search_campaign_drafts_updated_at
on public.search_campaign_drafts;

create trigger set_search_campaign_drafts_updated_at
before update on public.search_campaign_drafts
for each row
execute function public.handle_search_campaign_drafts_updated_at();

drop trigger if exists set_search_campaign_draft_approvals_updated_at
on public.search_campaign_draft_approvals;

create trigger set_search_campaign_draft_approvals_updated_at
before update on public.search_campaign_draft_approvals
for each row
execute function public.handle_search_campaign_draft_approvals_updated_at();
