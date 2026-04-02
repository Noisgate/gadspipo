# 🔧 Coolify Migration - Comandos Rápidos

Snippets prontos para copiar/colar durante a migração

---

## 🔐 FASE 1: Backups

### Exportar N8N Workflows (via API)

```bash
# Definir variáveis
N8N_HOST="seu-vps-ip"
N8N_PORT="5678"
N8N_TOKEN="seu-token-n8n"  # Gere em: N8N Settings → API Tokens

# Exportar
curl -X GET \
  -H "Authorization: Bearer ${N8N_TOKEN}" \
  http://${N8N_HOST}:${N8N_PORT}/api/v1/workflows \
  > n8n_workflows_backup.json

# Verificar
cat n8n_workflows_backup.json | jq '.[0:2]'  # Ver primeiros 2 workflows
```

### Backup PostgreSQL

```bash
# Conectar na VPS
ssh seu-usuario@seu-vps-ip

# Definir variáveis
PG_HOST="seu-postgres-host"
PG_USER="postgres"
PG_DB="marketing_manager"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

# Backup em format custom (mais compacto)
pg_dump -h ${PG_HOST} \
  -U ${PG_USER} \
  -d ${PG_DB} \
  --format=custom \
  > postgres_backup_${BACKUP_DATE}.dump

# Backup em SQL (legível)
pg_dump -h ${PG_HOST} \
  -U ${PG_USER} \
  -d ${PG_DB} \
  > postgres_backup_${BACKUP_DATE}.sql

# Copiar para local
exit  # sair do SSH

scp seu-usuario@seu-vps-ip:/home/seu-usuario/postgres_backup_*.dump ./backups/
scp seu-usuario@seu-vps-ip:/home/seu-usuario/postgres_backup_*.sql ./backups/
```

### Validar Backups

```bash
# Verificar tamanho
ls -lh backups/postgres_backup*.dump
ls -lh backups/n8n_workflows_backup.json

# Validar JSON (workflows)
cat backups/n8n_workflows_backup.json | jq . > /dev/null && echo "✅ JSON válido"

# Contar workflows
cat backups/n8n_workflows_backup.json | jq 'length'

# Validar dump PostgreSQL
file backups/postgres_backup*.dump
```

---

## 🔧 FASE 2: Instalar Coolify

### Instalação Rápida

```bash
# SSH na VPS
ssh seu-usuario@seu-vps-ip

# Instalar Docker (se não tiver)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker seu-usuario

# Logout e login para ativar grupos
exit
ssh seu-usuario@seu-vps-ip

# Instalar Coolify
docker run -d \
  --name coolify \
  -p 80:80 \
  -p 443:443 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v coolify:/data \
  coollabs/coolify:latest

# Aguardar 30 segundos
sleep 30

# Verificar status
docker logs coolify | tail -20

# Acessar em: https://seu-vps-ip
```

### Pré-requisitos Check

```bash
# Docker
docker --version
docker run hello-world

# Espaço em disco
df -h | grep -E "/$|/home"

# Memória
free -h

# Ports disponíveis
netstat -tuln | grep -E ":80|:443"
```

---

## 📦 FASE 3: PostgreSQL no Coolify

### Via CLI Docker (alternativo)

```bash
# Se preferir não usar UI do Coolify, rodar direto:
docker run -d \
  --name postgresql \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=SUA_SENHA_SUPER_SEGURA \
  -e POSTGRES_DB=marketing_manager \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15-alpine

# Aguardar inicialização
sleep 10

# Testar conexão
docker exec postgresql psql -U postgres -d marketing_manager -c "SELECT 1;"
```

### Restaurar Dados

```bash
# Definir variáveis
NEW_PG_HOST="novo-postgres-host"  # ou "localhost" se na mesma VPS
NEW_PG_USER="postgres"
NEW_PG_DB="marketing_manager"
BACKUP_FILE="postgres_backup_YYYYMMDD_HHMMSS.dump"

# Restaurar
pg_restore -h ${NEW_PG_HOST} \
  -U ${NEW_PG_USER} \
  -d ${NEW_PG_DB} \
  -v \
  /caminho/para/${BACKUP_FILE}

# Ou com SQL:
psql -h ${NEW_PG_HOST} \
  -U ${NEW_PG_USER} \
  -d ${NEW_PG_DB} \
  < postgres_backup_YYYYMMDD_HHMMSS.sql
```

### Verificar Restauração

```bash
# Conectar ao banco
psql -h novo-postgres-host -U postgres -d marketing_manager

# Listar tabelas
\dt

# Contar registros
SELECT
  schemaname,
  tablename,
  (SELECT count(*) FROM information_schema.tables t WHERE t.table_name = tablename) as rows
FROM pg_tables
WHERE schemaname = 'public';

# Sair
\q
```

---

## 🤖 FASE 4: N8N no Coolify

### Instalar N8N (alternativo ao UI)

```bash
# Se preferir via Docker direto:
docker run -d \
  --name n8n \
  -e DB_TYPE=postgresdb \
  -e DB_POSTGRESDB_HOST=novo-postgres-host \
  -e DB_POSTGRESDB_USER=postgres \
  -e DB_POSTGRESDB_PASSWORD=SUA_SENHA \
  -e DB_POSTGRESDB_DATABASE=marketing_manager \
  -e N8N_HOST=seu-vps-ip \
  -e N8N_PROTOCOL=https \
  -e WEBHOOK_URL=https://seu-vps-ip \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest

# Aguardar inicialização
sleep 30

# Ver logs
docker logs n8n | tail -50
```

### Importar Workflows

```bash
# Se tiver API token, importar via script:

N8N_HOST="seu-vps-ip"
N8N_PORT="5678"
N8N_TOKEN="seu-token-n8n"
WORKFLOWS_FILE="n8n_workflows_backup.json"

# Ler workflows
WORKFLOWS=$(cat ${WORKFLOWS_FILE} | jq -c '.[]')

echo "$WORKFLOWS" | while read workflow; do
  curl -X POST \
    -H "Authorization: Bearer ${N8N_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$workflow" \
    http://${N8N_HOST}:${N8N_PORT}/api/v1/workflows
done

echo "✅ Workflows importados"
```

---

## 🎯 FASE 5: Marketing Manager no Coolify

### Preparar Repositório GitHub

```bash
# Se não tiver git remoto
cd marketing-manager

# Adicionar remoto
git remote add origin https://github.com/seu-usuario/marketing-manager.git
git branch -M main
git push -u origin main

# Verificar
git remote -v
```

### Criar .env para Coolify

```bash
# Criar arquivo .env para deploy
cat > .env.coolify << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:SUA_SENHA@novo-postgres-host:5432/marketing_manager

# Auth
JWT_SECRET_KEY=$(openssl rand -hex 16)
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Google OAuth
GOOGLE_CLIENT_ID=seu-client-id
GOOGLE_CLIENT_SECRET=seu-client-secret
GOOGLE_REDIRECT_URI=https://armattiusa.com/api/v1/auth/google/callback

# Google Ads
GOOGLE_ADS_DEVELOPER_TOKEN=seu-token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=seu-customer-id

# OpenAI
OPENAI_API_KEY=seu-api-key
OPENAI_MODEL=gpt-4o

# Frontend
NEXT_PUBLIC_API_URL=https://armattiusa.com
NEXT_PUBLIC_API_VERSION=v1

# App
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=["https://armattiusa.com"]
EOF

# Gerar JWT seguro
openssl rand -hex 16
# Copiar output e colar em JWT_SECRET_KEY acima
```

### Build Local (teste rápido)

```bash
cd backend
docker build -t marketing-manager-backend:test .

cd ../frontend
docker build -t marketing-manager-frontend:test .

# Testar
docker run -p 3000:3000 marketing-manager-frontend:test
docker run -p 8000:8000 marketing-manager-backend:test
```

---

## 🔄 FASE 6: Auto-Deploy

### Fazer Teste de Auto-Deploy

```bash
# No seu repositório local
echo "# Deploy Test - $(date)" >> README.md
git add README.md
git commit -m "test: trigger coolify deploy"
git push origin main

# Coolify deve detectar push e disparar build
# Verificar em: Coolify Dashboard → Applications → Logs
```

### Monitorar Deploy

```bash
# SSH na VPS
ssh seu-usuario@seu-vps-ip

# Ver logs do container
docker logs -f marketing-manager-frontend

docker logs -f marketing-manager-backend

# Verificar saúde
docker ps --filter "name=marketing-manager"
```

---

## ✅ FASE 7: Verificações

### Health Checks

```bash
# Frontend
curl -I https://armattiusa.com

# Backend health
curl https://armattiusa.com/health

# Backend API docs
curl https://armattiusa.com/api/v1/docs

# N8N
curl -I https://armattiusa.com/n8n
```

### DNS & SSL

```bash
# DNS
nslookup armattiusa.com
dig armattiusa.com

# SSL Certificate
openssl s_client -connect armattiusa.com:443 -servername armattiusa.com

# Validade
echo | openssl s_client -servername armattiusa.com -connect armattiusa.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Logs e Monitoramento

```bash
# Todos os containers
docker ps

# Verificar espaço
docker system df

# Logs de erro
docker logs marketing-manager-backend 2>&1 | grep -i error

# Performance
docker stats
```

---

## 🐛 Troubleshooting

### Coolify não acessa GitHub

```bash
# Regenerar personal access token GitHub:
# https://github.com/settings/tokens

# Permissões necessárias:
# - repo (full control)
# - admin:repo_hook (write access to hooks)

# No Coolify Settings, adicionar novo token
```

### Database Connection Error

```bash
# Testar conectividade
telnet novo-postgres-host 5432

# Com psql
psql -h novo-postgres-host \
  -U postgres \
  -d marketing_manager \
  -c "SELECT 1;" \
  --echo-all

# Ver erro específico
psql -h novo-postgres-host \
  -U postgres \
  -d marketing_manager \
  -c "SELECT 1;" 2>&1
```

### Container não start

```bash
# Ver erro específico
docker logs marketing-manager-backend

# Rebuild sem cache
docker build --no-cache -t marketing-manager-backend .

# Tentar novamente
docker run ... marketing-manager-backend:latest
```

### Out of Memory

```bash
# Ver consumo
docker stats --no-stream

# Limpar espaço
docker system prune -a

# Aumentar swap (emergência)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📝 Notas Importantes

```bash
# Salvar credenciais seguras (não commitear!)
# Use .env.local ou .env.production.local

# Exemplo de .gitignore
echo "
.env
.env.local
.env.production.local
.env.development.local
*.dump
*.sql
" >> .gitignore

# Verificar
git status | grep .env
```

---

## 🎯 Checklist Rápido

```bash
✅ Backups feitos e testados
✅ Coolify instalado
✅ PostgreSQL migrado
✅ N8N workflows importados
✅ Frontend deployado
✅ Backend deployado
✅ SSL funcionando
✅ Auto-deploy testado
✅ Health checks passando
✅ Workflows executando
```

---

**Sucesso na migração!** 🚀
