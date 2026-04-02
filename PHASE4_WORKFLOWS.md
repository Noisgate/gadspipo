# ✅ Fase 4 - n8n Workflows (Documentação Completa)

## 📊 Três Workflows Documentados

### 1️⃣ **Daily Sync** (6h da manhã)
- Fetch campanhas do Google Ads API
- Calcula métricas (CTR, CPC, ROAS)
- Save no PostgreSQL (campaign_metrics table)
- Notifica backend (webhook)

### 2️⃣ **Automation Execution** (a cada hora)
- Query automations habilitadas
- Avalia regras (ROAS < 1.0, budget low, etc)
- Executa ações (pause, bid update, budget increase)
- Update last_run_at no DB
- Notifica usuário (Slack opcional)

### 3️⃣ **AI Recommendations** (8h da noite)
- Query últimos 30 dias de métricas
- Call GPT-4o para análise inteligente
- Gera recomendações (PAUSE, BID_ADJUSTMENT, etc)
- Save no PostgreSQL (recommendations table)
- Notifica usuário via webhook

---

## 📁 Arquivos Criados

```
/Users/felipeassinato/marketing-manager/
├── N8N_WORKFLOWS.md              ✅ (Documentação técnica)
├── N8N_SETUP_GUIDE.md            ✅ (Step-by-step UI guide)
└── PHASE4_WORKFLOWS.md           ✅ (Este arquivo)
```

---

## 🚀 Como Começar

### Passo 1: Start n8n

```bash
cd /Users/felipeassinato/marketing-manager

# Inicie n8n (Docker)
docker-compose up -d n8n postgres

# Acesse: http://localhost:5678
```

### Passo 2: Configure Credentials

No n8n UI:
1. **Settings** → **Credentials**
2. Crie 3 credentials:
   - HTTP Header Auth (Marketing Manager API)
   - PostgreSQL (Marketing Manager DB)
   - OpenAI API (para recomendações)

### Passo 3: Crie os 3 Workflows

Siga **N8N_SETUP_GUIDE.md** para criar:
- [ ] Workflow 1: Daily Sync
- [ ] Workflow 2: Automation Execution
- [ ] Workflow 3: AI Recommendations

### Passo 4: Teste & Ative

1. **Execute Workflow** button para testar cada um
2. **Activate** para ligar o scheduling
3. Monitore execuções em n8n UI

---

## 🔄 Fluxo End-to-End

```
6:00 AM → Daily Sync
  ├─ Fetch campaigns
  ├─ Calculate metrics
  ├─ Insert PostgreSQL
  └─ Notify ✓

1:00 PM → Automation Execution (hourly)
  ├─ Query enabled rules
  ├─ Evaluate campaigns
  ├─ Execute actions (pause, bid, budget)
  └─ Update DB ✓

8:00 PM → AI Recommendations
  ├─ Fetch 30-day metrics
  ├─ Call GPT-4o
  ├─ Generate recommendations
  ├─ Insert PostgreSQL
  └─ Notify user ✓
```

---

## 📊 Dados Trafegados

### Workflow 1 (Sync)
- Input: Campanhas do Google Ads
- Output: campaign_metrics table
- Volume: ~100-1000 campanhas/dia
- Latência: ~30-60s

### Workflow 2 (Automations)
- Input: Automations rules + metrics
- Output: Ações executadas (pause, bid, budget)
- Volume: ~10-50 ações/hora
- Latência: ~5-10s

### Workflow 3 (Recommendations)
- Input: 30 dias de métricas
- Output: Recomendações IA
- Volume: ~20-100 recomendações/dia
- Latência: ~30-60s (depende GPT-4o)

---

## 💾 Database Impact

### Tables Afetadas:
- `campaign_metrics` - insert diariamente (Workflow 1)
- `automations` - read/update hourly (Workflow 2)
- `recommendations` - insert diariamente (Workflow 3)
- `audit_logs` - read para context (Workflow 2)

### Queries Estimadas:
- Workflow 1: 1-2 inserts/segundo durante 6h
- Workflow 2: 10-20 queries/hora
- Workflow 3: 100-200 GPT-4o calls (async)

### Índices Importantes:
```sql
CREATE INDEX idx_automations_enabled 
  ON automations(enabled, account_id);

CREATE INDEX idx_campaign_metrics_date 
  ON campaign_metrics(campaign_id, date DESC);

CREATE INDEX idx_recommendations_status 
  ON recommendations(status, account_id);
```

---

## ⚡ Performance Otimizações

### Workflow 1 (Sync)
- ✅ Batch inserts (100 campanhas/query)
- ✅ Compress metrics antes de store
- ✅ Archive old metrics (>90 days) para history table

### Workflow 2 (Automations)
- ✅ Cache rule config em memory
- ✅ Limit queries a últimas 30 métricas
- ✅ Async execução de ações (não-blocking)

### Workflow 3 (Recommendations)
- ✅ Batch GPT-4o calls (agrupar campanhas)
- ✅ Cache respostas similares
- ✅ Async insert recomendações

---

## 🔐 Security Checklist

- [ ] JWT tokens com validade
- [ ] API keys em n8n credentials (não hardcoded)
- [ ] HTTPS entre n8n ↔ backend
- [ ] Database credentials encrypted
- [ ] Rate limiting no backend
- [ ] Audit logs de todas ações
- [ ] Error notifications (Slack)
- [ ] Scheduled backups antes de mutations

---

## 📈 Monitoring

### What to Watch:

1. **Execution Success Rate**
   - n8n UI → Workflow → Execution History
   - Target: >99% success rate

2. **Database Growth**
   ```sql
   -- Check campaign_metrics size
   SELECT pg_size_pretty(pg_total_relation_size('campaign_metrics'));
   ```

3. **API Response Times**
   - Backend logs → request latency
   - Target: <500ms para sync, <100ms para automations

4. **Recommendation Quality**
   - Dashboard → Recommendations accepted/rejected rate
   - Target: >60% acceptance rate

---

## 🆘 Troubleshooting

### Workflow não executa
1. Verifique Cron expression (use online cron parser)
2. Verifique timezone (America/Sao_Paulo)
3. Verifique n8n está running: `curl http://localhost:5678`

### Database connection erro
1. Verifique PostgreSQL está rodando
2. Verifique credentials em n8n
3. Teste manualmente: `psql postgresql://...`

### GPT-4o timeout
1. Aumentar timeout em OpenAI node (default 30s)
2. Reduzir batch size (menos campanhas/request)
3. Implementar retry logic

---

## 🎯 Próxima Fase: Production Deploy

### Checklist:
- [ ] VPS setup (DigitalOcean / AWS)
- [ ] Docker Compose em produção
- [ ] HTTPS para todos endpoints
- [ ] Database backup strategy
- [ ] Monitoring (Grafana/Prometheus)
- [ ] Log aggregation (ELK stack)
- [ ] Alerting (email/Slack)
- [ ] Load testing
- [ ] Disaster recovery plan

---

**Status:** ✅ Fase 4 Documentação Completa | **Próximo:** Fase 5 - Production Deploy
