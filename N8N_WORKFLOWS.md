# n8n Workflows - Marketing Manager

Documentação dos 3 workflows principais para automação do Marketing Manager.

---

## 📋 Workflow 1: Daily Sync (Google Ads → PostgreSQL)

**Propósito:** Sincronizar campanhas e métricas diariamente às 6h da manhã

**Trigger:** Cron (6:00 AM timezone America/Sao_Paulo)

### Nodes:

1. **Cron Trigger**
   - Schedule: `0 6 * * *` (6h da manhã, todos os dias)
   - Timezone: America/Sao_Paulo

2. **HTTP Request** (GET /api/v1/campaigns)
   - URL: `http://localhost:8000/api/v1/campaigns`
   - Auth: Bearer Token (N8N_API_KEY do backend)
   - Headers: `Authorization: Bearer <JWT_TOKEN>`

3. **For Each Loop** (iterate campaigns)
   - Iterate over: `data.campaigns`
   
4. **PostgreSQL Insert** (campaign_metrics)
   ```sql
   INSERT INTO campaign_metrics (
     campaign_id, date, impressions, clicks, 
     conversions, cost, ctr, avg_cpc, roas
   ) VALUES (
     $1, $2, $3, $4, $5, $6, $7, $8, $9
   )
   ```

5. **Notification** (Webhook to backend)
   - POST to: `/api/v1/sync/complete`
   - Body: `{ status: "success", synced_campaigns: 123 }`

### Execução:
```
Cron 6h → Fetch campaigns → Loop each → Insert metrics → Notify
```

---

## 📋 Workflow 2: Automation Execution (Hourly Rules)

**Propósito:** Executar regras de automação (pause, bid update, budget control)

**Trigger:** Cron (a cada hora: 0 * * * *)

### Nodes:

1. **Cron Trigger**
   - Schedule: `0 * * * *` (every hour)
   - Timezone: America/Sao_Paulo

2. **PostgreSQL Query** (fetch enabled automations)
   ```sql
   SELECT * FROM automations 
   WHERE enabled = true 
   AND account_id IN (SELECT id FROM google_ads_accounts)
   ```

3. **For Each Loop** (each automation rule)

4. **PostgreSQL Query** (get campaign metrics for evaluation)
   ```sql
   SELECT c.*, cm.* FROM campaigns c
   LEFT JOIN campaign_metrics cm ON c.id = cm.campaign_id
   WHERE c.account_id = $1
   ORDER BY cm.date DESC LIMIT 30
   ```

5. **Function Node** (JavaScript - evaluate rule)
   ```javascript
   // Example: Pause campaigns with ROAS < 1.0 and cost > 100
   const automation = $input.first().json.automation;
   const campaigns = $input.all().map(item => item.json);
   
   const actionsToExecute = [];
   
   for (const campaign of campaigns) {
     const roas = campaign.conversion_value / campaign.cost;
     if (roas < 1.0 && campaign.cost > 100) {
       actionsToExecute.push({
         campaignId: campaign.id,
         action: 'pause'
       });
     }
   }
   
   return actionsToExecute;
   ```

6. **For Each** (each action)

7. **HTTP Request** (POST action to backend)
   - URL: `http://localhost:8000/api/v1/automations/execute`
   - Method: POST
   - Body:
     ```json
     {
       "campaign_id": "uuid",
       "action": "pause|bid_update|budget_increase",
       "params": {}
     }
     ```

8. **PostgreSQL Update** (update automation.last_run_at)
   ```sql
   UPDATE automations 
   SET last_run_at = NOW(), next_run_at = NOW() + INTERVAL '1 hour'
   WHERE id = $1
   ```

9. **Slack Notification** (optional)
   - Send summary of executed actions

### Execução:
```
Cron 1h → Query automations → Loop each → Evaluate rule → 
Execute action (HTTP) → Update DB → Notify
```

---

## 📋 Workflow 3: AI Recommendations (Daily Analysis)

**Propósito:** Gerar recomendações inteligentes com GPT-4o

**Trigger:** Cron (8:00 PM daily: 20 0 * * *)

### Nodes:

1. **Cron Trigger**
   - Schedule: `0 20 * * *` (8 PM)
   - Timezone: America/Sao_Paulo

2. **PostgreSQL Query** (last 30 days metrics)
   ```sql
   SELECT 
     c.id, c.name, c.status,
     COUNT(cm.id) as days_tracked,
     SUM(cm.impressions) as total_impressions,
     SUM(cm.clicks) as total_clicks,
     SUM(cm.conversions) as total_conversions,
     SUM(cm.cost) as total_cost,
     AVG(cm.ctr) as avg_ctr,
     AVG(cm.roas) as avg_roas
   FROM campaigns c
   LEFT JOIN campaign_metrics cm ON c.id = cm.campaign_id
   WHERE cm.date >= NOW() - INTERVAL '30 days'
   GROUP BY c.id, c.name, c.status
   ```

3. **For Each Loop** (each account/group of campaigns)

4. **Prompt** (Prepare GPT-4o input)
   ```
   Analisar estes dados de campanhas Google Ads e gerar recomendações:
   
   Campanhas: {{ $json.campaigns }}
   
   Gerar recomendações em JSON com:
   {
     "recommendations": [
       {
         "campaign_id": "uuid",
         "type": "PAUSE|BID_ADJUSTMENT|BUDGET_REALLOC|REVIEW_LANDING_PAGE",
         "title": "string",
         "description": "string",
         "priority": "HIGH|MEDIUM|LOW",
         "estimated_impact": {
           "metric": "ROAS",
           "current": 0.8,
           "projected": 2.0,
           "confidence": 95
         }
       }
     ]
   }
   ```

5. **OpenAI Chat Model**
   - Model: gpt-4o
   - Temperature: 0.7
   - Max tokens: 2000
   - System: "You are a Google Ads optimization expert..."

6. **Parse JSON** (Extract recommendations from GPT response)

7. **PostgreSQL Insert** (insert recommendations)
   ```sql
   INSERT INTO recommendations (
     account_id, campaign_id, type, title, description,
     priority, estimated_impact, action_payload, status,
     ai_model, created_at
   ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'OPEN', 'gpt-4o', NOW())
   ```

8. **HTTP Webhook** (Notify backend/frontend)
   - POST to: `/api/v1/recommendations/generated`
   - Body: `{ count: 12, account_id: "uuid" }`

9. **Email Node** (optional - notify user)
   - Subject: "12 novas recomendações disponíveis"
   - Body: HTML com lista de recomendações

### Execução:
```
Cron 8PM → Query metrics (30d) → Loop accounts → Prepare prompt →
Call GPT-4o → Parse response → Insert DB → Webhook notify → Email
```

---

## 🔄 Fluxo Completo de Integração

```
┌─────────────────────────────┐
│     n8n Instance            │
│  (3 workflows + scheduling) │
└──────────┬──────────────────┘
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
┌─────┐┌──────┐┌─────────┐
│Sync │Automations│Recommendations│
│6h   │1h     │8PM      │
└──┬──┘└───┬──┘└────┬────┘
   │       │        │
   └───────┼────────┘
           ▼
   ┌───────────────────┐
   │ FastAPI Backend   │
   │ (validate, log)   │
   └───────┬───────────┘
           │
           ▼
   ┌───────────────────┐
   │ PostgreSQL        │
   │ (store metrics)   │
   └───────────────────┘
           │
           ▼
   ┌───────────────────┐
   │ Frontend (update) │
   │ via SWR re-fetch  │
   └───────────────────┘
```

---

## ⚙️ Setup no n8n

### 1. Variáveis de Ambiente (n8n)

Crie credentials no n8n:

```
# HTTP Auth (para chamar backend)
MARKETING_MANAGER_API_KEY = seu_jwt_token
MARKETING_MANAGER_API_URL = http://localhost:8000

# PostgreSQL Connection
DB_HOST = localhost
DB_PORT = 5432
DB_NAME = marketing_manager
DB_USER = user
DB_PASSWORD = password

# OpenAI
OPENAI_API_KEY = sk-...

# Slack (optional)
SLACK_WEBHOOK = https://hooks.slack.com/...
```

### 2. Criar Workflows

Para cada workflow:
1. Create new workflow
2. Add nodes conforme acima
3. Test com "Execute Workflow"
4. Save + Activate (ativar scheduling)

### 3. Testar Localmente

```bash
# n8n local
docker run -it -p 5678:5678 n8nio/n8n

# Acesse http://localhost:5678
# Crie os workflows
# Configure credentials
# Ative schedules
```

---

## 🔐 Security

- ✅ API Keys em n8n credentials (não hardcoded)
- ✅ JWT tokens com validade
- ✅ HTTPS em produção
- ✅ Rate limiting no backend
- ✅ Logs de todas as execuções

---

## 📊 Monitoramento

Cada workflow gera:
- Execution logs (sucesso/erro)
- Timestamp de execução
- Dados processados (count, affected rows)
- Erros detalhados (retry automático)

Verifique execuções em:
- n8n: Execution History
- PostgreSQL: audit_logs table
- Backend: Application logs

---

## 🚀 Production Checklist

- [ ] n8n running on VPS
- [ ] Credentials configuradas e seguras
- [ ] Workflows testados end-to-end
- [ ] Email notifications configuradas
- [ ] Database backups antes de automações
- [ ] Monitoring/alerting setup
- [ ] Error handling para falhas
- [ ] Rate limiting no backend
- [ ] HTTPS entre n8n ↔ backend
- [ ] Logs centralizados (ELK stack ou similar)

---

**Status:** 📋 Documentação Completa | **Próximo:** Implementar workflows no n8n
