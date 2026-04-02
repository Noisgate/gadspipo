# n8n Setup & Workflows - Step by Step Guide

Como criar e testar os 3 workflows no n8n.

---

## 🚀 Passo 1: Setup n8n Local

### Docker Compose (Recomendado)

```bash
cd /Users/felipeassinato/marketing-manager

# Adicione ao docker-compose.yml:
cat >> docker-compose.yml << 'DOCKER'

  # n8n
  n8n:
    image: n8nio/n8n:latest
    container_name: marketing-manager-n8n
    ports:
      - "5678:5678"
    environment:
      DB_TYPE: postgre
      DB_POSTGRE_HOST: postgres
      DB_POSTGRE_PORT: 5432
      DB_POSTGRE_DATABASE: ${DB_NAME:-marketing_manager}
      DB_POSTGRE_USER: ${DB_USER:-marketing_user}
      DB_POSTGRE_PASSWORD: ${DB_PASSWORD:-marketing_password}
      N8N_BASIC_AUTH_ACTIVE: "false"
      WEBHOOK_TUNNEL_URL: http://localhost:5678/
    depends_on:
      - postgres
    networks:
      - marketing-network
DOCKER

# Restart containers
docker-compose down
docker-compose up -d n8n postgres
```

Acesse: **http://localhost:5678**

### Ou Manual (sem Docker)

```bash
npm install -g n8n
n8n start

# Acesse http://localhost:5678
```

---

## 📋 Passo 2: Configurar Credentials

No n8n UI:

1. **Settings** → **Credentials**

2. Crie credencial **HTTP Header Auth**
   - Name: `Marketing Manager API`
   - Header Name: `Authorization`
   - Header Value: `Bearer <seu_jwt_token>`
   - URL: (deixe em branco, será usado em requests)

3. Crie credencial **PostgreSQL**
   - Name: `Marketing Manager DB`
   - Host: `postgres` (ou `localhost`)
   - Port: `5432`
   - User: `marketing_user`
   - Password: `marketing_password`
   - Database: `marketing_manager`
   - SSL: `false` (se local)

4. Crie credencial **OpenAI**
   - Name: `OpenAI API`
   - API Key: `sk-...`

---

## 🔄 Passo 3: Criar Workflow 1 - Daily Sync

### No n8n:

1. **+ Create New** → **Workflow**
2. Nome: `Daily Sync - Google Ads to PostgreSQL`

### Nodes:

#### 1️⃣ Cron Trigger
- Search: `Cron`
- Add node
- Settings:
  - Expression: `0 6 * * *` (6h da manhã)
  - Timezone: `America/Sao_Paulo`

#### 2️⃣ HTTP Request
- Search: `HTTP Request`
- Add node
- Configuration:
  - URL: `http://localhost:8000/api/v1/campaigns`
  - Method: `GET`
  - Headers: Add
    - Key: `Authorization`
    - Value: `Bearer <jwt_token>`
  - Response format: JSON

#### 3️⃣ Loop Over Items
- Search: `Loop Over Items`
- Add node
- Input: (conecte do HTTP Request)
- Mode: `Loop over all items`

#### 4️⃣ PostgreSQL Insert
- Search: `PostgreSQL`
- Add node (dentro do loop)
- Credentials: Selecione `Marketing Manager DB`
- Configuration:
  ```sql
  INSERT INTO campaign_metrics (
    campaign_id, date, impressions, clicks, 
    conversions, cost, ctr, avg_cpc, roas, time
  ) VALUES (
    '{{ $json.id }}',
    CURRENT_DATE,
    {{ $json.latest_metrics.impressions || 0 }},
    {{ $json.latest_metrics.clicks || 0 }},
    {{ $json.latest_metrics.conversions || 0 }},
    {{ $json.latest_metrics.cost || 0 }},
    {{ $json.latest_metrics.ctr || 0 }},
    {{ $json.latest_metrics.avg_cpc || 0 }},
    {{ $json.latest_metrics.roas || 0 }},
    NOW()
  )
  ON CONFLICT (campaign_id, date) DO UPDATE
  SET impressions = EXCLUDED.impressions,
      clicks = EXCLUDED.clicks,
      conversions = EXCLUDED.conversions,
      cost = EXCLUDED.cost,
      ctr = EXCLUDED.ctr,
      avg_cpc = EXCLUDED.avg_cpc,
      roas = EXCLUDED.roas,
      time = NOW();
  ```

#### 5️⃣ HTTP Request (Notify Backend)
- Search: `HTTP Request`
- Add node
- Configuration:
  - URL: `http://localhost:8000/api/v1/sync/complete`
  - Method: `POST`
  - Headers:
    - `Authorization: Bearer <jwt_token>`
  - Body:
    ```json
    {
      "status": "success",
      "synced_campaigns": "{{ $json.length }}",
      "timestamp": "{{ now() }}"
    }
    ```

### Test & Save:
1. Click **Execute Workflow** para testar
2. Click **Save** quando funcionar
3. Click **Activate** para ativar schedule

---

## 🎯 Passo 4: Criar Workflow 2 - Automation Execution

### No n8n:

1. **+ Create New** → **Workflow**
2. Nome: `Hourly Automations`

### Nodes:

#### 1️⃣ Cron Trigger
- Expression: `0 * * * *` (every hour)
- Timezone: `America/Sao_Paulo`

#### 2️⃣ PostgreSQL - Query Automations
- SQL:
  ```sql
  SELECT * FROM automations 
  WHERE enabled = true
  LIMIT 100
  ```

#### 3️⃣ Loop Over Items
- Loop over automations

#### 4️⃣ PostgreSQL - Get Campaign Metrics
- SQL:
  ```sql
  SELECT c.*, cm.* FROM campaigns c
  LEFT JOIN campaign_metrics cm ON c.id = cm.campaign_id
  WHERE c.account_id = '{{ $item.json.account_id }}'
  ORDER BY cm.date DESC 
  LIMIT 30
  ```

#### 5️⃣ Function - Evaluate Rule
- Search: `Function`
- Language: `JavaScript`
- Code:
  ```javascript
  const automation = $input.first().json;
  const campaigns = $input.all().map(x => x.json);
  
  const actions = [];
  
  // Example rule: Pause low ROAS campaigns
  if (automation.rule_type === 'PAUSE_LOW_PERFORMERS') {
    for (const c of campaigns) {
      const roas = c.conversion_value / Math.max(c.cost, 1);
      if (roas < 1.0 && c.cost > 100) {
        actions.push({
          campaignId: c.id,
          action: 'pause'
        });
      }
    }
  }
  
  return actions;
  ```

#### 6️⃣ HTTP Request - Execute Action
- URL: `http://localhost:8000/api/v1/automations/execute`
- Method: `POST`
- Body:
  ```json
  {
    "campaign_id": "{{ $json.campaignId }}",
    "action": "{{ $json.action }}",
    "automation_id": "{{ $item.json.id }}"
  }
  ```

#### 7️⃣ PostgreSQL - Update Automation
- SQL:
  ```sql
  UPDATE automations
  SET last_run_at = NOW(),
      next_run_at = NOW() + INTERVAL '1 hour'
  WHERE id = '{{ $item.json.id }}'
  ```

### Test & Save:
- Click **Execute Workflow**
- Verifique se campanhas foram pausadas
- **Save** + **Activate**

---

## 🤖 Passo 5: Criar Workflow 3 - AI Recommendations

### No n8n:

1. **+ Create New** → **Workflow**
2. Nome: `Daily AI Recommendations`

### Nodes:

#### 1️⃣ Cron Trigger
- Expression: `0 20 * * *` (8 PM)
- Timezone: `America/Sao_Paulo`

#### 2️⃣ PostgreSQL - Analytics Query
- SQL:
  ```sql
  SELECT 
    c.id, c.account_id, c.name, c.status,
    SUM(cm.impressions) as total_impressions,
    SUM(cm.clicks) as total_clicks,
    SUM(cm.conversions) as total_conversions,
    SUM(cm.cost) as total_cost,
    AVG(cm.ctr) as avg_ctr,
    AVG(cm.roas) as avg_roas,
    c.budget_daily
  FROM campaigns c
  LEFT JOIN campaign_metrics cm ON c.id = cm.campaign_id
  WHERE cm.date >= NOW() - INTERVAL '30 days'
    AND c.account_id IN (SELECT id FROM google_ads_accounts WHERE is_active = true)
  GROUP BY c.id, c.account_id, c.name, c.status, c.budget_daily
  ORDER BY total_cost DESC
  ```

#### 3️⃣ Loop Over Items
- Loop over campaigns

#### 4️⃣ OpenAI Chat Model
- Model: `gpt-4o`
- Prompt:
  ```
  Você é um especialista em Google Ads. Analise esta campanha e gere uma recomendação JSON:
  
  Campanha: {{ $json.name }}
  Status: {{ $json.status }}
  Impressões (30d): {{ $json.total_impressions }}
  Cliques (30d): {{ $json.total_clicks }}
  Conversões (30d): {{ $json.total_conversions }}
  Custo (30d): R$ {{ $json.total_cost }}
  CTR: {{ $json.avg_ctr }}%
  ROAS: {{ $json.avg_roas }}x
  Budget diário: R$ {{ $json.budget_daily }}
  
  Retorne APENAS JSON com:
  {
    "type": "PAUSE|BID_ADJUSTMENT|BUDGET_REALLOC|REVIEW_LANDING_PAGE",
    "title": "string",
    "description": "string",
    "priority": "HIGH|MEDIUM|LOW",
    "estimated_impact": {
      "metric": "ROAS|CPA|CTR",
      "current": number,
      "projected": number,
      "confidence": number
    }
  }
  ```
- Temperature: `0.7`

#### 5️⃣ Function - Parse Response
- Language: `JavaScript`
- Code:
  ```javascript
  try {
    const text = $input.first().json.response;
    const json = JSON.parse(text);
    return {
      campaign_id: $item.json.id,
      account_id: $item.json.account_id,
      ...json
    };
  } catch (e) {
    return null;
  }
  ```

#### 6️⃣ PostgreSQL - Insert Recommendation
- SQL:
  ```sql
  INSERT INTO recommendations (
    id, account_id, campaign_id, type, title, description,
    priority, estimated_impact, action_payload, status,
    ai_model, created_at
  ) VALUES (
    gen_random_uuid(),
    '{{ $json.account_id }}',
    '{{ $json.campaign_id }}',
    '{{ $json.type }}',
    '{{ $json.title }}',
    '{{ $json.description }}',
    '{{ $json.priority }}',
    '{{ JSON.stringify($json.estimated_impact) }}',
    '{ "campaign_id": "{{ $json.campaign_id }}" }',
    'OPEN',
    'gpt-4o',
    NOW()
  )
  ```

#### 7️⃣ HTTP Request - Notify Backend
- URL: `http://localhost:8000/api/v1/recommendations/generated`
- Method: `POST`
- Body:
  ```json
  {
    "type": "{{ $json.type }}",
    "priority": "{{ $json.priority }}",
    "campaign_id": "{{ $json.campaign_id }}"
  }
  ```

### Test & Save:
- Click **Execute Workflow**
- Verifique se recomendações foram criadas em `recommendations` table
- **Save** + **Activate**

---

## ✅ Verificar Tudo Funcionando

```bash
# 1. Verifique n8n está rodando
curl http://localhost:5678

# 2. Verifique backend está respondendo
curl http://localhost:8000/health

# 3. Verifique PostgreSQL
psql postgresql://marketing_user:password@localhost:5432/marketing_manager
SELECT COUNT(*) FROM campaign_metrics;

# 4. Verifique workflows estão ativos
# → n8n UI → Workflows → check "Active" status
```

---

## 🎯 Próximos Passos

- [ ] Criar os 3 workflows no n8n
- [ ] Testar cada um (Execute Workflow button)
- [ ] Ativar schedules
- [ ] Monitorar execuções
- [ ] Setup email notifications
- [ ] Deploy em produção

---

**Status:** 📋 Documentação Completa | **Próximo:** Implementar workflows
