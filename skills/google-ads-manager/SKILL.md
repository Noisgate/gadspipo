---
name: google-ads-manager
description: |
  Gerencie campanhas Google Ads com análise inteligente e recomendações em português.
  Use esta skill para: criar/pausar/editar/deletar campanhas, analisar performance,
  gerar relatórios, receber recomendações de otimização, monitorar ROI e CPA.
  Pré-configurado para sua conta Google Ads, integrado com PostgreSQL para histórico
  e análises avançadas. Conversacional: explica ideias antes de executar. Error-smart:
  lê erros, discute soluções, nunca fica em loop. Agent-based: quebra projetos complexos
  em agentes independentes. SEMPRE use quando mencionar Google Ads, campanhas,
  análise de performance, relatórios, otimizações, bids, budgets ou ROI.
---

# Google Ads Manager

**Gerenciador inteligente de campanhas Google Ads com análise conversacional.**

Pré-configurado para sua conta Google Ads (oauth2), integrado com PostgreSQL para
histórico de dados, e construído com padrão conversacional (explica antes de agir),
error-smart (nunca fica em loop), e agent-based (entende projetos complexos).

---

## 🚀 Quick Start

### Opção 1: Setup Automático (Recomendado)

```bash
python ~/.claude/skills/google-ads-manager/setup.py
```

O script vai:
- ✅ Copiar `.env.example` para `.env` (se não existir)
- ✅ Instalar dependências automaticamente
- ✅ Criar marcador para não rodar de novo
- ✅ Verificar conexão com Google Ads API

### Opção 2: Setup Manual

```bash
# Step 1: Copy configuration template
cp .env.example .env

# Step 2: Edit with your credentials
nano .env

# Step 3: Install dependencies
pip install -r requirements.txt

# Step 4: Test connection
python -c "from google_ads_client import GoogleAdsManagerClient; client = GoogleAdsManagerClient(); print('✅ Conectado!' if client.verify_connection() else '❌ Falhou')"
```

---

## 📊 Core Concepts

### Filosofia de Interação

#### 1. **Conversacional**
Antes de executar qualquer ação, explica a ideia:

```
📋 Ideia: Pausar campanhas com ROAS < 1.5 dos últimos 30 dias
🔄 Fluxo:
   Buscar campanhas (Google Ads API)
   ↓
   Analisar ROAS últimos 30d (PostgreSQL)
   ↓
   Filtrar ROAS < 1.5
   ↓
   Pausar no Google Ads
   ↓
   Log em audit trail

✨ Impactos esperados:
   - Reduzir desperdício em campanhas baixo-performing
   - Preservar 5-7 campanhas com bom ROAS
   - Manter histórico para análise posterior

❓ Proceder? [sim/não/modificar]
```

#### 2. **Error-Smart**
Quando erros ocorrem, discute soluções (nunca loop):

```
❌ Problema: 401 Unauthorized na Google Ads API
💡 Discussão:
   - Último acesso bem-sucedido: há 2h
   - Token OAuth2 provavelmente expirou
   - Credenciais no .env estão corretas
🔧 Soluções (rankeadas):
   1. Regenerar token OAuth2 (rápido)
   2. Verificar permissões na Google Cloud Console
   3. Verificar se API está ativada
```

#### 3. **Agent-Based**
Entende projetos complexos, quebra em agentes independentes:

```
📦 Projeto: "Otimizar 50 campanhas, gerar relatório, propor mudanças"

Agente 1: Data Collection
└─ Buscar 50 campanhas + métricas últimos 30d

Agente 2: Analysis
└─ Análise ROAS, CPA, CTR por campanha

Agente 3: Recommendations
└─ Gerar 5-10 recomendações priorizadas

Agente 4: Reporting
└─ Criar relatório markdown com insights

Agente 5: Implementation
└─ Executar mudanças aprovadas
```

---

## 🎯 Operações Principais

### 1. Gerenciar Campanhas

#### Listar Campanhas

```
Prompt: "Me mostre as campanhas ativas com seus status"

Saída:
📊 Campanhas Ativas (8):
├─ Campaign A - Status: ENABLED, Budget: R$ 1.000/dia, Spend: R$ 892
├─ Campaign B - Status: ENABLED, Budget: R$ 500/dia, Spend: R$ 412
├─ Campaign C - Status: PAUSED, Budget: R$ 200/dia, Spend: R$ 0
└─ ...

Total: R$ 3.200/dia gastos em 8 campanhas
```

#### Criar Campanha

```
Prompt: "Cria uma campanha de busca para palavras-chave de 'python tutorial' com budget R$ 500/dia"

Conversação:
📋 Ideia: Criar campanha Search para "python tutorial"
🔄 Fluxo:
   Nome: "Python Tutorial - Search"
   Tipo: SEARCH
   Budget: R$ 500/dia
   Status inicial: PAUSED (você ativa depois)
   Palavras-chave: ["python tutorial", "learn python", "python beginners"]

✨ Impactos:
   - Novo fluxo de tráfego para "python tutorial"
   - Budget isolado (não afeta outras campanhas)
   - Fácil de pausar se não performar

❓ Proceder? [sim/não/modificar]

✅ Campanha criada: Campaign ID 123456789
```

#### Pausar/Resumir Campanha

```
Prompt: "Pausa a campanha 'Campaign A' por enquanto"

✅ Campanha pausada
Antes: Status ENABLED, Spend R$ 892/dia
Depois: Status PAUSED, Spend R$ 0
```

#### Ajustar Budget

```
Prompt: "Aumenta o budget da Campaign B de R$ 500 para R$ 1.000 por dia"

✅ Budget atualizado
Antes: R$ 500/dia
Depois: R$ 1.000/dia
```

### 2. Análise de Performance

#### Analisar Campanhas

```
Prompt: "Analisa a performance das minhas campanhas dos últimos 30 dias"

Saída:
📊 Performance Analysis (Últimos 30 dias)

🏆 Top Performers:
├─ Campaign A: ROAS 3.2, CPA R$ 15, CTR 4.2%
├─ Campaign B: ROAS 2.8, CPA R$ 18, CTR 3.9%

⚠️ Underperformers:
├─ Campaign C: ROAS 0.8, CPA R$ 45, CTR 1.2%
├─ Campaign D: ROAS 1.1, CPA R$ 38, CTR 1.5%

📈 Tendências:
├─ Spend total: R$ 95.000 (↑ 5% vs semana anterior)
├─ Conversões: 425 (↑ 12%)
├─ CPA médio: R$ 223 (↓ 3%)
└─ ROAS médio: 1.9 (↑ 7%)

💡 Insights:
   - Campaign A é a stella do portfólio (ROAS 3.2)
   - Campaign C está perdendo dinheiro (ROAS 0.8)
   - Sugestão: Aumentar budget de A, pausar/otimizar C
```

#### Gerar Relatório

```
Prompt: "Gera um relatório completo de performance para apresentar ao cliente"

Saída: Relatório em markdown com:
- Executive Summary (3-5 bullets)
- KPIs principais (Spend, Conversões, ROAS, CPA)
- Performance por campanha (tabela)
- Tendências gráficas (últimos 30d)
- Top performers e underperformers
- Recomendações priorizadas
- Próximos passos sugeridos
```

### 3. Recomendações de Otimização

#### Obter Recomendações

```
Prompt: "Quais são suas recomendações para melhorar o ROAS das minhas campanhas?"

Saída:
💡 Recomendações Priorizadas (por impacto esperado):

1. ⭐⭐⭐ Pausar Campaign C (ROAS 0.8)
   Impacto: -R$ 1.200/mês, libera budget para crescimento
   Confiança: 95%

2. ⭐⭐⭐ Aumentar budget Campaign A (ROAS 3.2)
   Impacto: +R$ 2.500/mês em conversões
   Confiança: 89%

3. ⭐⭐ Otimizar landing page Campaign B (CTR 3.9%)
   Impacto: +0.8% CTR, +R$ 800/mês
   Confiança: 72%

4. ⭐ Testar ad copy novo para Campaign D
   Impacto: +1.2% CTR, +R$ 450/mês
   Confiança: 65%
```

---

## 🔧 Python Client Usage

### Basic Operations

```python
from google_ads_client import GoogleAdsManagerClient

client = GoogleAdsManagerClient()

# List campaigns
campaigns = client.list_campaigns(status='ENABLED')

# Get campaign details
campaign = client.get_campaign('campaign-id')

# Create campaign
new_campaign = client.create_campaign(
    name='New Campaign',
    campaign_type='SEARCH',
    daily_budget_micros=500000000  # R$ 500
)

# Pause/Resume campaign
client.update_campaign_status('campaign-id', 'PAUSED')

# Get performance metrics
metrics = client.get_campaign_metrics(
    campaign_id='campaign-id',
    date_from='2024-01-01',
    date_to='2024-01-31'
)
```

### Analysis Operations

```python
# Analyze performance
analysis = client.analyze_campaigns(days=30)

# Get recommendations
recommendations = client.get_recommendations()

# Generate report
report = client.generate_performance_report(days=30)
```

---

## 📁 File Structure

```
google-ads-manager/
├── SKILL.md                    # Documentação principal
├── README.md                   # Quick start guide
├── google_ads_client.py        # Cliente pré-configurado (400+ linhas)
├── .env.example                # Template de credenciais
├── setup.py                    # Setup automático
├── requirements.txt            # Dependências
├── .gitignore                  # Protege .env
└── scripts/
    ├── campaign_manager.py     # CRUD: listar, criar, pausar, editar
    ├── performance_analyzer.py # Análise: ROAS, CPA, CTR, tendências
    └── recommendation_engine.py# Recomendações: otimizações sugeridas
```

---

## 🔐 Security

- ✅ Credenciais em `.env`, nunca hardcoded
- ✅ OAuth2 tokens armazenados localmente, nunca transmitidos
- ✅ `.gitignore` protege `.env` e arquivos sensíveis
- ✅ Auto-refresh de tokens OAuth2
- ✅ Logs não expõem credenciais
- ✅ Audit trail de todas as mudanças

---

## 🚨 Error Handling

### Retry Logic

Cliente implementa retry automático com exponential backoff:
```
Tentativa 1: imediata
Tentativa 2: após 1s
Tentativa 3: após 2s
Tentativa 4: após 4s
Tentativa 5: após 8s
```

### Error Classification

Erros são classificados em 6 tipos:
1. **Authentication** - Token expirado, credenciais inválidas
2. **RateLimit** - API throttling, tente mais tarde
3. **QuotaExceeded** - Limite mensal atingido
4. **InvalidRequest** - Dados inválidos, valide entrada
5. **ServerError** - Problema no servidor Google
6. **Unknown** - Erro desconhecido

Cada tipo tem sugestões de solução rankeadas.

---

## 📋 Use Cases

### Daily Monitoring
1. Listar todas as campanhas
2. Analisar performance dos últimos 7 dias
3. Identificar underperformers (ROAS < 1.5)
4. Propor ações (pausar, otimizar, aumentar budget)

### Weekly Optimization
1. Gerar relatório completo
2. Comparar semana vs semana anterior
3. Identificar tendências (crescimento/queda)
4. Receber recomendações de otimização
5. Implementar mudanças aprovadas

### Monthly Review
1. Analisar performance do mês completo
2. Comparar vs mês anterior
3. Gerar relatório executivo
4. Planejar budget para mês próximo
5. Revisar ROI por campanha

### Budget Reallocation
1. Identificar campanhas high-ROI
2. Identificar campanhas low-ROI
3. Propor realocação de budget
4. Executar mudanças com histórico

---

## 🎯 Next Steps

1. **Setup**: Rode `python setup.py` para configurar
2. **Test**: Verifique `python -c "from google_ads_client import GoogleAdsManagerClient; GoogleAdsManagerClient().verify_connection()"`
3. **Explore**: Use `list_campaigns()` para ver suas campanhas
4. **Analyze**: Peça uma análise dos últimos 30 dias
5. **Optimize**: Implemente recomendações passo a passo

---

## ✨ Philosophy

**google-ads-manager é conversacional, error-smart, e agent-based:**

1. **Conversacional** - Explica ideias antes de criar/editar/deletar
2. **Error-Smart** - Lê erros, discute soluções, nunca loop
3. **Agent-Based** - Quebra projetos complexos em agentes independentes
4. **Reusable** - Funciona em qualquer projeto, qualquer conta Google Ads

---

**Status:** ✅ Production Ready
**Criado:** Março 2026
**Filosofia:** Conversacional. Error-Smart. Agent-Based.
