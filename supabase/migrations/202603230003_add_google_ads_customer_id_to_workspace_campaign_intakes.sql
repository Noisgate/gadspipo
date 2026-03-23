alter table public.workspace_campaign_intakes
add column if not exists google_ads_customer_id text not null default '';
