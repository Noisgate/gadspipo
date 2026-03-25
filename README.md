# adsmcp

Scaffold inicial do produto `Google Ads Copilot for Business Owners`.

## Stack inicial

- `apps/web`: Next.js com App Router para a experiencia do produto
- `apps/worker`: worker TypeScript para jobs e processamento assíncrono
- `packages/domain`: contratos de domínio e estados do produto
- `packages/integrations`: gateways para Google Ads, Google Drive e LLM
- `packages/ui`: componentes compartilhados da interface
- `packages/prompts`: prompts e templates de IA

## Como começar

```bash
npm install
npm run dev
```

## Runtime local

- Use `Node 22 LTS`.
- O repositorio agora inclui [.nvmrc](/Users/felipeassinato/Documents/projetos%20codex/adsmcp/.nvmrc) para facilitar isso.
- Se voce estiver com `Node 25`, o app pode ficar preso na inicializacao sem abrir a porta local do Next.js. Nesse caso, troque para `Node 22`, rode `npm install` novamente e depois `npm run dev:web`.

## Banco de dados

O projeto agora suporta dois caminhos de persistencia:

- `Supabase Auth + Supabase Postgres`
- `Supabase Auth + PostgreSQL direto` via `DATABASE_URL`

Se `DATABASE_URL` estiver configurada, o app prioriza `PostgreSQL` direto para salvar intake, drafts e aprovacoes. Se nao estiver, ele continua usando o caminho atual do `Supabase client`. Sem banco pronto, o app ainda cai no fallback local por cookie.

### Usando Supabase Postgres

Aplique as migrations em `supabase/migrations/202603220001_create_workspace_campaign_intakes.sql`, `supabase/migrations/202603230001_create_search_campaign_drafts.sql`, `supabase/migrations/202603230002_create_search_campaign_draft_approvals.sql` e `supabase/migrations/202603230004_fix_search_campaign_draft_approvals_objective_check.sql`.

### Usando PostgreSQL direto

1. Defina `DATABASE_URL` no ambiente.
2. Se o banco exigir conexao sem SSL em ambiente local, defina `POSTGRES_SSL_DISABLED=true`.
3. Aplique [postgres/migrations/202603230101_create_workspace_tables.sql](/Users/felipeassinato/Workspace/gadspipo/postgres/migrations/202603230101_create_workspace_tables.sql).

Observacao:

- o login continua vindo de `Supabase Auth`
- a persistencia direta em `PostgreSQL` usa o mesmo `owner_user_id` do usuario autenticado
- enquanto isso nao estiver configurado, o app continua funcionando em modo preview com fallback local

## Comandos úteis

```bash
npm run dev
npm run dev:web
npm run dev:worker
npm run build
npm run typecheck
```

## Estrutura

```text
apps/
  web/
  worker/
packages/
  domain/
  integrations/
  prompts/
  ui/
docs/
  ways-of-work/plan/google-ads-copilot/
supabase/
  migrations/
```

## Próximos passos

1. Aplicar as migrations de `workspace_campaign_intakes`, `search_campaign_drafts` e `search_campaign_draft_approvals` no Supabase.
2. Conectar Google Drive real e sincronizar a pasta selecionada.
3. Construir o pipeline de ingestão da pasta do Drive.
4. Mapear a aprovacao do draft para a etapa de publicacao assistida no Google Ads.
