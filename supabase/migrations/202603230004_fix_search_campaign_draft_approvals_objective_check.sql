alter table public.search_campaign_draft_approvals
drop constraint if exists search_campaign_draft_approvals_objective_check;

alter table public.search_campaign_draft_approvals
add constraint search_campaign_draft_approvals_objective_check
check (objective in ('leads', 'vendas', 'agendamentos', 'trafego qualificado'));
