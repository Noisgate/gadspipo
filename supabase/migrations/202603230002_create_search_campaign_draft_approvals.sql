create table if not exists public.search_campaign_draft_approvals (
  owner_user_id uuid primary key references auth.users (id) on delete cascade,
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
    check (objective in ('leads', 'sales', 'appointments', 'custom')),
  constraint search_campaign_draft_approvals_status_check
    check (approval_status in ('pending_review', 'approved', 'changes_requested'))
);

alter table public.search_campaign_draft_approvals enable row level security;

create or replace function public.handle_search_campaign_draft_approvals_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists set_search_campaign_draft_approvals_updated_at
on public.search_campaign_draft_approvals;

create trigger set_search_campaign_draft_approvals_updated_at
before update on public.search_campaign_draft_approvals
for each row
execute function public.handle_search_campaign_draft_approvals_updated_at();

drop policy if exists search_campaign_draft_approvals_select_own
on public.search_campaign_draft_approvals;

create policy search_campaign_draft_approvals_select_own
on public.search_campaign_draft_approvals
for select
using (auth.uid() = owner_user_id);

drop policy if exists search_campaign_draft_approvals_insert_own
on public.search_campaign_draft_approvals;

create policy search_campaign_draft_approvals_insert_own
on public.search_campaign_draft_approvals
for insert
with check (auth.uid() = owner_user_id);

drop policy if exists search_campaign_draft_approvals_update_own
on public.search_campaign_draft_approvals;

create policy search_campaign_draft_approvals_update_own
on public.search_campaign_draft_approvals
for update
using (auth.uid() = owner_user_id)
with check (auth.uid() = owner_user_id);

drop policy if exists search_campaign_draft_approvals_delete_own
on public.search_campaign_draft_approvals;

create policy search_campaign_draft_approvals_delete_own
on public.search_campaign_draft_approvals
for delete
using (auth.uid() = owner_user_id);
