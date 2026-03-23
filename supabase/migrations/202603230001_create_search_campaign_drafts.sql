create table if not exists public.search_campaign_drafts (
  owner_user_id uuid primary key references auth.users(id) on delete cascade,
  campaign_name text not null,
  objective text not null,
  source_folder_id text,
  draft_payload jsonb not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  constraint search_campaign_drafts_objective_check
    check (objective in ('leads', 'vendas', 'agendamentos', 'trafego qualificado'))
);

alter table public.search_campaign_drafts enable row level security;

create or replace function public.handle_search_campaign_drafts_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

drop trigger if exists set_search_campaign_drafts_updated_at
on public.search_campaign_drafts;

create trigger set_search_campaign_drafts_updated_at
before update on public.search_campaign_drafts
for each row
execute function public.handle_search_campaign_drafts_updated_at();

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'search_campaign_drafts'
      and policyname = 'search_campaign_drafts_select_own'
  ) then
    create policy search_campaign_drafts_select_own
      on public.search_campaign_drafts
      for select
      using (auth.uid() = owner_user_id);
  end if;
end
$$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'search_campaign_drafts'
      and policyname = 'search_campaign_drafts_insert_own'
  ) then
    create policy search_campaign_drafts_insert_own
      on public.search_campaign_drafts
      for insert
      with check (auth.uid() = owner_user_id);
  end if;
end
$$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'search_campaign_drafts'
      and policyname = 'search_campaign_drafts_update_own'
  ) then
    create policy search_campaign_drafts_update_own
      on public.search_campaign_drafts
      for update
      using (auth.uid() = owner_user_id)
      with check (auth.uid() = owner_user_id);
  end if;
end
$$;

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'search_campaign_drafts'
      and policyname = 'search_campaign_drafts_delete_own'
  ) then
    create policy search_campaign_drafts_delete_own
      on public.search_campaign_drafts
      for delete
      using (auth.uid() = owner_user_id);
  end if;
end
$$;
