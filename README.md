# GadsPipo - Google Ads Copilot for Business Owners

Sistema completo de gerenciamento, analise e automacao de campanhas Google Ads. Combina uma interface web (Next.js), integracao direta com a Google Ads API, skills de IA para analise e otimizacao, e automacao via n8n.

---

## Visao Geral do Projeto

O GadsPipo nasceu da necessidade de controlar campanhas Google Ads de forma inteligente e automatizada. O sistema permite:

- Conectar a conta Google Ads via OAuth 2.0
- Listar, analisar e diagnosticar campanhas em tempo real
- Criar e gerenciar campanhas via API
- Gerar relatorios automaticos de performance
- Otimizar keywords, anuncios e orcamentos com IA
- Automatizar fluxos com n8n e persistir dados em PostgreSQL

### Contas Gerenciadas

| Cliente | Campanhas | Segmento |
|---------|-----------|----------|
| Armatti Yachts | PIP2026ARMATTI1803 | Yachts e embarcacoes de luxo |
| BoatSP Seminovos | SEMINOVO BOATSP-1803 | Barcos e lanchas seminovas |

---

## Stack Tecnologico

| Camada | Tecnologia | Funcao |
|--------|-----------|--------|
| Frontend | Next.js + App Router + TypeScript | Interface do produto |
| Backend | Supabase (Auth + PostgreSQL) | Autenticacao e persistencia |
| API | Google Ads API v23 | Leitura e escrita de campanhas |
| Skills IA | Python + google-ads-python | Analise, diagnostico e automacao |
| MCP Server | google_ads_mcp | Integracao Claude + Google Ads |
| Automacao | n8n | Workflows automatizados |
| Database | PostgreSQL (VPS) | Armazenamento historico |

---

## Estrutura do Repositorio

```
gadspipo/
|
|-- apps/
|   |-- web/                          # Next.js App (dashboard, login, OAuth)
|   |   |-- app/
|   |   |   |-- auth/
|   |   |   |   |-- google-ads/       # OAuth flow Google Ads
|   |   |   |   |   |-- start/route.ts
|   |   |   |   |   |-- callback/route.ts
|   |   |   |   |-- actions.ts
|   |   |   |   |-- callback/route.ts
|   |   |   |-- dashboard/
|   |   |   |   |-- page.tsx           # Dashboard principal
|   |   |   |   |-- actions.ts
|   |   |   |   |-- search-draft-actions.tsx
|   |   |   |   |-- draft-approval-actions.tsx
|   |   |   |   |-- drive-intake-form.tsx
|   |   |   |-- login/
|   |   |   |   |-- login-form.tsx
|   |   |   |-- layout.tsx
|   |   |   |-- page.tsx
|   |   |   |-- globals.css
|   |-- worker/                        # Worker para jobs assincronos
|
|-- packages/
|   |-- domain/                        # Contratos e estados do produto
|   |-- integrations/                  # Gateways Google Ads, Drive, LLM
|   |-- prompts/                       # Prompts e templates de IA
|   |-- ui/                            # Componentes compartilhados
|
|-- skills/
|   |-- google-ads-manager/            # Skill principal de gerenciamento
|   |   |-- SKILL.md                   # Instrucoes da skill
|   |   |-- google_ads_client.py       # Cliente Python Google Ads API
|   |   |-- .env.example               # Template de credenciais
|   |   |-- requirements.txt
|   |   |-- setup.py
|   |   |-- scripts/
|   |   |   |-- campaign_manager.py    # CRUD de campanhas
|   |   |   |-- performance_analyzer.py # Analise de performance
|   |   |   |-- recommendation_engine.py # Motor de recomendacoes
|   |
|   |-- google_ads_mcp/                # MCP Server Google Ads
|       |-- ads_mcp/
|       |   |-- server.py              # Servidor MCP
|       |   |-- coordinator.py         # Coordenador de requests
|       |   |-- stdio.py              # Interface stdio
|       |   |-- utils.py              # Utilitarios
|       |   |-- tools/
|       |   |   |-- api.py            # Ferramentas de API
|       |   |   |-- docs.py           # Ferramentas de documentacao
|       |   |-- context/
|       |       |-- GAQL.md           # Referencia Google Ads Query Language
|       |       |-- views.yaml        # Views de reporting
|       |-- tests/                    # Testes unitarios
|       |-- pyproject.toml
|
|-- config/
|   |-- google-ads.yaml.example        # Template de configuracao da API
|
|-- scripts/
|   |-- diagnostics/
|   |   |-- create_campaigns.py        # Script de criacao de campanhas via API
|   |-- check-node-version.mjs
|
|-- docs/
|   |-- diagnostics/
|   |   |-- DIAGNOSTICO_CAMPANHAS_2026-03-29.md  # Relatorio de diagnostico
|   |   |-- SETUP_OAUTH.md             # Guia completo de setup OAuth
|   |-- ways-of-work/
|       |-- plan/google-ads-copilot/
|           |-- epic.md                # Epic do produto
|           |-- arch.md                # Arquitetura
|           |-- mvp-features.md        # Features do MVP
|           |-- search-campaign-draft-builder/prd.md
|           |-- drive-context-ingestion/prd.md
|           |-- approval-publishing-audit/prd.md
|           |-- optimization-recommendations-center/prd.md
|           |-- workspace-onboarding/prd.md
|
|-- supabase/
|   |-- migrations/                    # Migrations Supabase
|
|-- postgres/
|   |-- migrations/                    # Migrations PostgreSQL direto
|
|-- .gitignore
|-- package.json
|-- turbo.json
|-- tsconfig.base.json
```

---

## Como Comecar

### Pre-requisitos

- Node.js 22 LTS
- Python 3.8+
- Conta Google Ads ativa
- Projeto no Google Cloud Console
- PostgreSQL (local ou VPS)

### 1. Clonar e instalar

```bash
git clone https://github.com/Noisgate/gadspipo.git
cd gadspipo
npm install
```

### 2. Configurar Google Ads API

Siga o guia completo em [`docs/diagnostics/SETUP_OAUTH.md`](docs/diagnostics/SETUP_OAUTH.md).

Resumo rapido:

```bash
# Copiar template de configuracao
cp config/google-ads.yaml.example ~/google-ads.yaml

# Editar com suas credenciais
nano ~/google-ads.yaml
```

Preencha:

```yaml
client_id: SEU_CLIENT_ID.apps.googleusercontent.com
client_secret: SEU_CLIENT_SECRET
refresh_token: SEU_REFRESH_TOKEN
developer_token: SEU_DEVELOPER_TOKEN
login_customer_id: "SEU_CUSTOMER_ID_SEM_HIFENS"
use_proto_plus: true
```

### 3. Configurar variaveis de ambiente

```bash
# App web
cp .env.example .env

# Google Ads Manager skill
cp skills/google-ads-manager/.env.example skills/google-ads-manager/.env
```

### 4. Configurar banco de dados

**Opcao A: Supabase**
```bash
# Aplicar migrations
supabase db push
```

**Opcao B: PostgreSQL direto**
```bash
# Definir DATABASE_URL
export DATABASE_URL=postgresql://user:password@host:5432/dbname

# Aplicar migration
psql $DATABASE_URL < postgres/migrations/202603230101_create_workspace_tables.sql
```

### 5. Executar

```bash
# Desenvolvimento
npm run dev

# Apenas web
npm run dev:web

# Apenas worker
npm run dev:worker
```

---

## Autenticacao OAuth 2.0

O sistema usa OAuth 2.0 para conectar contas Google Ads. O fluxo completo:

```
Usuario -> Login (Supabase Auth)
       -> Conectar Google Ads (OAuth 2.0)
       -> Autorizar scope: googleapis.com/auth/adwords
       -> Receber Refresh Token
       -> Salvar no banco (Supabase/PostgreSQL)
       -> Acessar dados via API
```

### Geracao do Refresh Token

1. Acessar [OAuth Playground](https://developers.google.com/oauthplayground/)
2. Configurar **Use your own OAuth credentials**
3. Inserir Client ID e Client Secret
4. Autorizar scope: `https://www.googleapis.com/auth/adwords`
5. Trocar authorization code por tokens
6. Copiar o `refresh_token`

**Importante:** O Refresh Token DEVE ser gerado com o MESMO Client ID e Client Secret configurados no sistema. Usar credenciais diferentes resulta em erro `unauthorized_client`.

---

## Skills de IA

### google-ads-manager

Skill principal para gerenciamento de campanhas via Claude. Capacidades:

| Funcao | Descricao |
|--------|-----------|
| Listar campanhas | Lista todas as campanhas com status e orcamento |
| Analisar performance | Metricas de 30/60/90 dias (impressoes, cliques, conversoes, custo) |
| Diagnosticar problemas | Identifica por que campanhas nao estao performando |
| Criar campanhas | Cria campanhas, ad groups, keywords e anuncios via API |
| Otimizar keywords | Analisa Quality Score e sugere melhorias |
| Gerenciar orcamento | Ajusta budgets e estrategias de lance |
| Gerar relatorios | Exporta dados de performance em diversos formatos |

Uso:

```python
from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_storage("~/google-ads.yaml")
ga_service = client.get_service("GoogleAdsService")

# Listar campanhas
query = """
SELECT
    campaign.name,
    campaign.status,
    campaign_budget.amount_micros
FROM campaign
WHERE campaign.status = 'ENABLED'
"""

results = ga_service.search_stream(customer_id="8960664207", query=query)
for batch in results:
    for row in batch.results:
        budget = row.campaign_budget.amount_micros / 1_000_000
        print(f"{row.campaign.name}: R$ {budget:.2f}/dia")
```

### google_ads_mcp

Servidor MCP (Model Context Protocol) que permite ao Claude interagir diretamente com a Google Ads API.

Configuracao no `settings.json`:

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "ads_mcp.server"],
      "cwd": "skills/google_ads_mcp",
      "env": {
        "GOOGLE_ADS_CONFIG_PATH": "~/google-ads.yaml"
      }
    }
  }
}
```

### Outras Skills Disponiveis

| Skill | Funcao |
|-------|--------|
| ads-google | Auditoria completa (74 checks) |
| ads-create | Geracao de conceitos de campanha |
| ads-audit | Auditoria multi-plataforma |
| ads-budget | Otimizacao de orcamento |
| ads-creative | Estrategia criativa |
| ads-competitor | Analise competitiva |
| ads-landing | Otimizacao de landing pages |
| ads-dna | Extracao de brand profile |
| ads-generate | Geracao de imagens com IA |
| copy-writer | Copy de anuncios |
| creative-strategist | Estrategia de campanhas |
| audit-tracking | Rastreamento de conversoes |
| audit-compliance | Conformidade regulatoria |

---

## Diagnostico de Campanhas (29/03/2026)

Ultimo diagnostico executado via API. Relatorio completo em [`docs/diagnostics/DIAGNOSTICO_CAMPANHAS_2026-03-29.md`](docs/diagnostics/DIAGNOSTICO_CAMPANHAS_2026-03-29.md).

### Resumo

| Metrica | Valor |
|---------|-------|
| Campanhas ativas | 2 |
| Orcamento diario total | R$ 120,00 |
| Keywords aprovadas | 67 (100%) |
| Anuncios ativos | 2 (Responsive Search Ads) |
| Impressoes (90 dias) | 0 |
| Cliques (90 dias) | 0 |
| Conversoes (90 dias) | 0 |

### Campanhas

| Campanha | Keywords | Headlines | Descriptions | Budget |
|----------|----------|-----------|--------------|--------|
| PIP2026ARMATTI1803 | 13 | 5 | 4 | R$ 60/dia |
| SEMINOVO BOATSP-1803 | 54 | 9 | 2 | R$ 60/dia |

### Problema Identificado

Campanhas 100% configuradas (keywords aprovadas, anuncios qualificados, orcamento alocado, cartao ativo) porem com ZERO impressoes em 90 dias. Causas provaveis:

1. Quality Score muito baixo
2. Landing pages com problemas
3. Targeting excessivamente restritivo
4. Lances abaixo do minimo competitivo
5. Problema interno na conta

### Faturamento

- Cartao: Mastercard ...3003 (ativo)
- Ultimo pagamento: 2 de marco - R$ 545,82
- Custo liquido (jan-mar): R$ 0,00

### Budgets Criados via API

| Budget | Valor | Status |
|--------|-------|--------|
| Lead Gen Budget 2026 | R$ 10/dia | Criado |
| Brand Awareness Budget 2026 | R$ 15/dia | Criado |

---

## Integracao com n8n

O sistema integra com n8n para automacao de workflows:

- **URL:** Configurar no ambiente
- **Workflow Principal:** Brunna_workflow_CORRIGIDO
- **Funcao:** match_documents com pgvector para busca semantica

### Workflows Planejados

1. Relatorio diario de performance via email
2. Alerta de anomalias (queda de impressoes, aumento de CPC)
3. Sincronizacao de dados com PostgreSQL
4. Backup automatico de configuracoes

---

## Persistencia de Dados

O projeto suporta dois caminhos:

### Supabase (padrao)

```
Supabase Auth -> Login do usuario
Supabase PostgreSQL -> workspace_campaign_intakes
                    -> search_campaign_drafts
                    -> search_campaign_draft_approvals
```

### PostgreSQL Direto

```
Supabase Auth -> Login (continua via Supabase)
PostgreSQL -> Todas as tabelas de dados
           -> Definir DATABASE_URL no ambiente
           -> Aplicar migration: postgres/migrations/202603230101_*.sql
```

Se `DATABASE_URL` estiver configurada, o app prioriza PostgreSQL direto. Sem banco configurado, funciona em modo preview com fallback local por cookie.

---

## Seguranca

### Credenciais

- **NUNCA** commitar credenciais reais no repositorio
- Usar `.env` para credenciais locais (protegido pelo `.gitignore`)
- Usar `google-ads.yaml.example` como template (sem dados reais)
- GitHub Push Protection ativo para bloquear vazamentos

### .gitignore

```
.env
.env.local
.env.production
.env.development
google-ads.yaml
*.yaml.credentials
skills/google-ads-manager/.env
skills/google_ads_mcp/.env
__pycache__/
*.pyc
*.egg-info/
```

### OAuth

- Refresh Tokens devem ser gerados com as credenciais corretas
- Access Tokens expiram em 1 hora (renovados automaticamente)
- Scope minimo: `https://www.googleapis.com/auth/adwords`

---

## Comandos Uteis

```bash
# Desenvolvimento
npm run dev              # Iniciar tudo
npm run dev:web          # Apenas frontend
npm run dev:worker       # Apenas worker
npm run build            # Build de producao
npm run typecheck        # Verificacao de tipos

# Google Ads API (Python)
pip install google-ads   # Instalar biblioteca
python3 scripts/diagnostics/create_campaigns.py  # Criar campanhas

# Database
supabase db push         # Aplicar migrations Supabase
```

---

## Troubleshooting

### Erro: unauthorized_client

O Refresh Token foi gerado com credenciais OAuth diferentes das configuradas.

**Solucao:** Gere um novo Refresh Token no [OAuth Playground](https://developers.google.com/oauthplayground/) usando exatamente o mesmo Client ID e Client Secret do arquivo `google-ads.yaml`.

### Erro: UNRECOGNIZED_FIELD

Campos inexistentes na versao da API sendo usada.

**Solucao:** Consulte a documentacao da versao atual. Campos como `campaign.start_date`, `campaign.daily_budget_micros` e `ad.status` nao existem na v23.

### Erro: 404 na REST API

URL do endpoint incorreta ou versao da API nao suportada.

**Solucao:** Use a versao correta da API (v14, v16, v23) conforme a biblioteca instalada.

### Node.js preso na inicializacao

Se estiver usando Node 25, o Next.js pode travar.

**Solucao:** Use Node 22 LTS (verificar `.nvmrc`):
```bash
nvm use
npm install
npm run dev:web
```

### Campanhas sem impressoes

Mesmo com keywords aprovadas e orcamento alocado, campanhas podem nao receber impressoes.

**Verificar:**
1. Quality Score das keywords (minimo 5/10)
2. Landing page funcionando e relevante
3. Configuracao de targeting (localizacao, idioma)
4. Lances competitivos para o segmento
5. Status da conta no Google Ads Console

---

## Roadmap

- [x] Setup OAuth Google Ads
- [x] Integracao com Google Ads API v23
- [x] Skill google-ads-manager
- [x] MCP Server google_ads_mcp
- [x] Diagnostico automatizado de campanhas
- [x] Criacao de budgets via API
- [ ] Criacao de campanhas via API (bloqueio tecnico em resolucao)
- [ ] Criacao de campanhas via browser automation (Claude in Chrome)
- [ ] Dashboard de performance em tempo real
- [ ] Alertas automaticos via n8n
- [ ] Integracao Google Drive para ingestao de contexto
- [ ] Pipeline de aprovacao e publicacao de campanhas
- [ ] Centro de recomendacoes de otimizacao
- [ ] Multi-tenant SaaS para multiplos clientes

---

## Licenca

Projeto privado. Todos os direitos reservados.

---

*Ultima atualizacao: 29 de marco de 2026*
*Mantido por: Felipe Assinato (noisgate@gmail.com)*
