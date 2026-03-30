# Google Ads Manager - Skill para Claude

**Gerenciador inteligente de campanhas Google Ads com análise conversacional em português.**

## 🚀 Quick Start

### Setup Automático (Recomendado)
```bash
python ~/.claude/skills/google-ads-manager/setup.py
```

### Setup Manual
```bash
cp .env.example .env
nano .env  # Preencha com suas credenciais
pip install -r requirements.txt
```

### Verificar Conexão
```bash
python -c "from google_ads_client import GoogleAdsManagerClient; client = GoogleAdsManagerClient(); print('✅ Conectado!' if client.verify_connection() else '❌ Falhou')"
```

---

## 📚 Documentação Completa

Veja **SKILL.md** para:
- Conceitos de interação (Conversacional, Error-Smart, Agent-Based)
- Operações principais (Campanhas, Análise, Recomendações)
- Exemplos de uso completos
- Filosofia da skill

---

## 🔧 O que Você Pode Fazer

### Gerenciar Campanhas
- ✅ Listar campanhas com filtros
- ✅ Criar novas campanhas
- ✅ Pausar/Resumir campanhas
- ✅ Atualizar budgets

### Analisar Performance
- 📊 Análise de ROAS, CPA, CTR
- 📈 Tendências dos últimos 30 dias
- 💰 Gasto total e ROI
- 🎯 Top performers vs underperformers

### Obter Recomendações
- 💡 Recomendações automáticas priorizadas
- ⚡ Quick wins (oportunidades rápidas)
- 📉 Campanhas para pausar
- 🚀 Campanhas para escalar

---

## 🔐 Configuração de Credenciais

Crie `.env` com:

```env
# Google Ads (obrigatório)
GOOGLE_ADS_CLIENT_ID=seu_client_id
GOOGLE_ADS_CLIENT_SECRET=seu_client_secret
GOOGLE_ADS_REFRESH_TOKEN=seu_refresh_token
GOOGLE_ADS_CUSTOMER_ID=seu_customer_id
GOOGLE_ADS_DEVELOPER_TOKEN=seu_developer_token

# PostgreSQL (opcional)
DB_HOST=seu_host
DB_PORT=5432
DB_NAME=seu_database
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

---

## 💬 Como Usar com Claude

Simplesmente converse naturalmente sobre Google Ads:

```
"Me mostra as campanhas ativas com performance"
"Analisa as últimas 30 dias e recomenda otimizações"
"Pausa campanhas com ROAS menor que 1.0"
"Qual é o orçamento ideal para escalar Campaign A?"
```

A skill vai:
1. ✅ Explicar a ideia antes de executar
2. ✅ Ler erros e discutir soluções (nunca loop)
3. ✅ Quebrar projetos complexos em agentes independentes

---

## 📁 Estrutura

```
google-ads-manager/
├── SKILL.md                      # Documentação completa
├── README.md                     # Este arquivo
├── google_ads_client.py          # Cliente pré-configurado
├── setup.py                      # Setup automático
├── requirements.txt              # Dependências
├── .env.example                  # Template de credenciais
├── .gitignore                    # Protege .env
└── scripts/
    ├── campaign_manager.py       # CRUD de campanhas
    ├── performance_analyzer.py   # Análise de performance
    └── recommendation_engine.py  # Recomendações
```

---

## ✨ Características

- **Pré-configurada**: Auto-load de `.env`, setup único
- **Conversacional**: Explica antes de executar
- **Error-Smart**: Classifica erros, nunca fica em loop
- **Agent-Based**: Entende projetos complexos
- **Em Português**: Todas as mensagens em PT-BR
- **Production-Ready**: Retry logic, exponential backoff

---

## 🆘 Suporte

Para informações completas: **Veja SKILL.md**

Para exemplos: **Veja scripts/**

Credenciais: **Edite .env**

---

**Status:** ✅ Production Ready | **Criado:** Março 2026 | **Linguagem:** Português
