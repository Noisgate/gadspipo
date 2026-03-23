create table if not exists public.workspace_campaign_intakes (
  owner_user_id uuid primary key references auth.users(id) on delete cascade,
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

alter table public.workspace_campaign_intakes enable row level security;

create or replace function public.handle_workspace_campaign_intakes_updated_at()
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

do $$
begin
  if not exists (
    select 1
    from pg_policies
    where schemaname = 'public'
      and tablename = 'workspace_campaign_intakes'
      and policyname = 'workspace_campaign_intakes_select_own'
  ) then
    create policy workspace_campaign_intakes_select_own
      on public.workspace_campaign_intakes
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
      and tablename = 'workspace_campaign_intakes'
      and policyname = 'workspace_campaign_intakes_insert_own'
  ) then
    create policy workspace_campaign_intakes_insert_own
      on public.workspace_campaign_intakes
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
      and tablename = 'workspace_campaign_intakes'
      and policyname = 'workspace_campaign_intakes_update_own'
  ) then
    create policy workspace_campaign_intakes_update_own
      on public.workspace_campaign_intakes
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
      and tablename = 'workspace_campaign_intakes'
      and policyname = 'workspace_campaign_intakes_delete_own'
  ) then
    create policy workspace_campaign_intakes_delete_own
      on public.workspace_campaign_intakes
      for delete
      using (auth.uid() = owner_user_id);
  end if;
end
$$;
