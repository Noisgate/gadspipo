# 🚀 Plano de Migração para Coolify

Migração completa: **Easypanel → Coolify** (N8N + PostgreSQL + Marketing Manager)

---

## 📊 Visão Geral

### Antes (Easypanel):
```
Easypanel
├── N8N (workflows de automação)
├── PostgreSQL (banco de dados)
└── [Vazio - esperando Marketing Manager]
```

### Depois (Coolify):
```
Coolify
├── N8N (workflows importados)
├── PostgreSQL (dados migrados)
└── Marketing Manager (Frontend + Backend com auto-deploy)
```

---

## ✅ Fase 1: Preparação (Backup de Tudo)

### 1.1 Exportar Workflows N8N

```bash
# SSH na VPS
ssh seu-usuario@seu-vps-ip

# Listar containers N8N
docker ps | grep n8n

# Acessar N8N e exportar via API
curl -H "Authorization: Bearer SEU_N8N_TOKEN" \
  http://localhost:5678/api/v1/workflows \
  > /home/seu-usuario/n8n_workflows_backup.json

# Ou via UI:
# 1. Vá para http://seu-vps-ip:5678
# 2. Menu → Export Workflows → Download JSON
```

### 1.2 Backup Completo do PostgreSQL

```bash
# Fazer backup do banco
pg_dump -h seu-postgres-host \
  -U postgres \
  -d marketing_manager \
  --format=custom \
  > /home/seu-usuario/postgres_backup.dump

# Backup em SQL também
pg_dump -h seu-postgres-host \
  -U postgres \
  -d marketing_manager \
  > /home/seu-usuario/postgres_backup.sql
```

### 1.3 Backup do N8N Configuration

```bash
# Se usar volumes, fazer backup da pasta
docker inspect seu-container-n8n | grep Mounts

# Copiar dados do N8N
docker cp seu-container-n8n:/root/.n8n /home/seu-usuario/n8n_config_backup/
```

### 1.4 Copiar Backups para Local

```bash
# No seu computador local
scp seu-usuario@seu-vps-ip:/home/seu-usuario/n8n_workflows_backup.json ./backups/
scp seu-usuario@seu-vps-ip:/home/seu-usuario/postgres_backup.sql ./backups/
scp seu-usuario@seu-vps-ip:/home/seu-usuario/postgres_backup.dump ./backups/
```

**✅ Agora você tem tudo salvo localmente!**

---

## 🔧 Fase 2: Instalar Coolify

### 2.1 SSH na VPS

```bash
ssh seu-usuario@seu-vps-ip
```

### 2.2 Instalar Coolify

```bash
# Docker + Docker Compose devem estar instalados
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Coolify (recomenda 2GB RAM mínimo)
docker run -d \
  --name coolify \
  -p 80:80 \
  -p 443:443 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v coolify:/data \
  coollabs/coolify:latest
```

### 2.3 Acessar Coolify

1. Vá para: `https://seu-vps-ip`
2. Crie conta admin
3. Configure domínio: `armattiusa.com`

---

## 📦 Fase 3: Migrar PostgreSQL

### 3.1 Criar PostgreSQL no Coolify

1. No Coolify: **Resources** → **Databases** → **PostgreSQL**
2. Configure:
   - Name: `marketing-manager-db`
   - Username: `postgres`
   - Password: `[gerar nova]`
   - Port: `5432`
3. Clique **Deploy**
4. Espere ficar **Healthy** ✅

### 3.2 Restaurar Dados

```bash
# Após PostgreSQL estar pronto, restaurar dados
pg_restore -h novo-postgres-host \
  -U postgres \
  -d marketing_manager \
  /caminho/para/postgres_backup.dump

# Ou usar SQL:
psql -h novo-postgres-host \
  -U postgres \
  -d marketing_manager \
  < /caminho/para/postgres_backup.sql
```

### 3.3 Verificar Dados

```bash
psql -h novo-postgres-host \
  -U postgres \
  -d marketing_manager

# No prompt psql:
\dt  # listar tabelas
SELECT COUNT(*) FROM users;  # verificar dados
```

---

## 🤖 Fase 4: Migrar N8N

### 4.1 Criar N8N no Coolify

1. No Coolify: **Resources** → **Services** → **N8N**
2. Configure:
   - Name: `n8n-automation`
   - Database: `marketing-manager-db` (criado acima)
3. Clique **Deploy**
4. Espere ficar **Healthy** ✅

### 4.2 Importar Workflows

1. Acesse novo N8N: `https://armattiusa.com/n8n`
2. Crie conta admin
3. Menu → **Import** → Selecione `n8n_workflows_backup.json`
4. Clique **Import**

### 4.3 Reconfigurar Credenciais

⚠️ **IMPORTANTE**: Credenciais não são exportadas por segurança!

Para cada workflow:
1. Abra o workflow
2. Vá para credenciais
3. Reconfigure (Google Ads API, OpenAI, etc)

---

## 🎯 Fase 5: Deploy Marketing Manager no Coolify

### 5.1 Conectar GitHub

1. No Coolify: **Settings** → **Git Provider**
2. Autorizar GitHub
3. Conectar seu repositório `marketing-manager`

### 5.2 Criar Aplicação Frontend

1. Coolify → **Applications** → **Create**
2. Configure:
   - **Name**: `marketing-manager-frontend`
   - **Source**: GitHub `seu-repo/marketing-manager`
   - **Build**: `cd frontend && npm run build`
   - **Start**: `npm start`
   - **Port**: `3000`
   - **Domain**: `armattiusa.com`
3. Clique **Deploy**

### 5.3 Criar Aplicação Backend

1. Coolify → **Applications** → **Create**
2. Configure:
   - **Name**: `marketing-manager-backend`
   - **Source**: GitHub `seu-repo/marketing-manager`
   - **Build**: `cd backend && docker build -t backend .`
   - **Start**: `uvicorn main:app --host 0.0.0.0 --port 8000`
   - **Port**: `8000`
   - **Path**: `/api/v1`
   - **Environment Variables**:
     ```
     DATABASE_URL=postgresql://postgres:senha@marketing-manager-db:5432/marketing_manager
     GOOGLE_REDIRECT_URI=https://armattiusa.com/api/v1/auth/google/callback
     JWT_SECRET_KEY=sua-chave-gerada
     [outras credenciais]
     ```
3. Clique **Deploy**

### 5.4 Configurar Auto-Deploy

1. No Coolify → Application → **Settings**
2. **Auto Deploy**: `Enabled`
3. Cada `git push` dispara novo deploy automático ✅

---

## 🔒 Fase 6: Configurar SSL e Domínio

1. Coolify faz SSL automaticamente via Let's Encrypt
2. Mape domínios:
   - `armattiusa.com` → Frontend
   - `armattiusa.com/api/v1` → Backend
   - `armattiusa.com/n8n` → N8N

---

## ✅ Fase 7: Verificação Pós-Migração

### 7.1 Testar N8N
```bash
curl https://armattiusa.com/n8n
# Deve carregar interface do N8N
```

### 7.2 Testar Marketing Manager
```bash
curl https://armattiusa.com
# Deve carregar frontend

curl https://armattiusa.com/health
# Deve retornar {"status":"ok"}
```

### 7.3 Testar Banco de Dados
```bash
# Via N8N ou Marketing Manager
# Verifique se consegue ler/escrever dados
```

### 7.4 Testar Workflows N8N
1. Abra um workflow no N8N
2. Clique **Test Workflow**
3. Verifique se funciona

---

## 🗑️ Fase 8: Limpeza (Remover Easypanel)

⚠️ **APENAS APÓS TUDO FUNCIONAR PERFEITAMENTE**

```bash
# Parar Easypanel
docker stop easypanel
docker rm easypanel

# Remover volumes (opcional)
docker volume rm easypanel_data

# Verificar espaço liberado
docker system prune -a
```

---

## 🔄 Fluxo de Trabalho Novo

Após migração:

```
Você edita código do Marketing Manager
    ↓
git push para GitHub
    ↓
Coolify webhook dispara
    ↓
Coolify faz build
    ↓
Coolify faz deploy
    ↓
App atualiza em https://armattiusa.com ✅
    ↓
N8N pode acessar dados via API
    ↓
Workflows executam normalmente
```

---

## 📊 Comparação

| Aspecto | Easypanel | Coolify |
|---------|-----------|---------|
| **Deploy Manual** | ✅ Sim | ✅ Sim |
| **Auto-Deploy** | ❌ Não | ✅ Sim (GitHub) |
| **N8N** | ✅ Suportado | ✅ Suportado |
| **PostgreSQL** | ✅ Suportado | ✅ Suportado |
| **UI** | ✅ Simples | ✅ Mais completa |
| **Custo** | Livre | Livre (open-source) |

---

## 🆘 Troubleshooting

### Workflows não importam
```bash
# Verifique se JSON está válido
cat n8n_workflows_backup.json | jq .

# Se erro, tente editor: https://jsonlint.com/
```

### Banco não restaura
```bash
# Verificar erro
pg_restore -v -h host -U user -d db backup.dump

# Se erro de permissão, criar banco primeiro
createdb -h host -U user marketing_manager
```

### Coolify não encontra GitHub
```bash
# Verificar token GitHub
# Settings → Personal Access Tokens → Criar novo com permissões repo
```

---

## ✨ Benefícios Pós-Migração

✅ **Único painel** (Coolify) para tudo
✅ **Auto-deploy** via GitHub (tipo Vercel!)
✅ **Melhor integração** entre serviços
✅ **Mais escalável** para crescimento
✅ **Open-source** (código aberto)
✅ **Sem custo** (rooda na sua VPS)

---

**Status**: 🟡 Plano pronto para execução
**Tempo Estimado**: 2-3 horas
**Risco**: Baixo (você tem backups!)

Quer começar? 🚀
