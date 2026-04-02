# 📦 Deployment Guide - Marketing Manager na VPS (Easypanel)

## ✅ Pré-requisitos

- [x] Easypanel instalado na VPS
- [x] PostgreSQL configurado (via skill)
- [x] Domínio: **armattiusa.com**
- [x] SSL será configurado automaticamente

---

## 🚀 Fase 1: Preparar Arquivos de Produção

### 1.1 Atualizar `.env` para Produção

Criar arquivo `.env.production` na raiz do projeto:

```bash
# ========================================
# PRODUCTION CONFIGURATION
# ========================================

# Database (PostgreSQL no Easypanel)
DATABASE_URL=postgresql://postgres:<SUA-SENHA>@seu-postgres-host:5432/marketing_manager?sslmode=require

# Auth & Security
JWT_SECRET_KEY=<GERAR-CHAVE-SEGURA-32-CARACTERES>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Google OAuth2 (IMPORTANTE: Atualizar com domínio de produção)
GOOGLE_CLIENT_ID=<YOUR_GOOGLE_CLIENT_ID>
GOOGLE_CLIENT_SECRET=<YOUR_GOOGLE_CLIENT_SECRET>
GOOGLE_REDIRECT_URI=https://armattiusa.com/api/v1/auth/google/callback

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=<SEU-DEVELOPER-TOKEN>
GOOGLE_ADS_LOGIN_CUSTOMER_ID=<SEU-CUSTOMER-ID>

# OpenAI (opcional)
OPENAI_API_KEY=<SUA-CHAVE>
OPENAI_MODEL=gpt-4o

# App Settings
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=https://armattiusa.com,https://www.armattiusa.com

# Scheduler
SCHEDULER_ENABLED=true
SYNC_SCHEDULE_HOUR=6

# Frontend
NEXT_PUBLIC_API_URL=https://armattiusa.com
```

### 1.2 Gerar JWT_SECRET_KEY Segura

```bash
openssl rand -hex 16
```

---

## 🐳 Fase 2: Docker Compose para Produção

### 2.1 Criar `docker-compose.prod.yml`

```yaml
version: '3.8'

services:
  # FastAPI Backend
  backend:
    image: marketing-manager-backend:latest
    container_name: marketing-manager-backend-prod
    command: uvicorn main:app --host 0.0.0.0 --port 8000
    environment:
      DATABASE_URL: ${DATABASE_URL}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
      GOOGLE_REDIRECT_URI: ${GOOGLE_REDIRECT_URI}
      GOOGLE_ADS_DEVELOPER_TOKEN: ${GOOGLE_ADS_DEVELOPER_TOKEN}
      DEBUG: ${DEBUG}
      LOG_LEVEL: ${LOG_LEVEL}
    ports:
      - "8000:8000"
    restart: always
    networks:
      - marketing-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Next.js Frontend
  frontend:
    image: marketing-manager-frontend:latest
    container_name: marketing-manager-frontend-prod
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
    ports:
      - "3000:3000"
    restart: always
    networks:
      - marketing-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  marketing-network:
    driver: bridge
```

---

## 🔧 Fase 3: Atualizar Google Cloud Console

⚠️ **IMPORTANTE:** Você precisa atualizar as credenciais OAuth no Google Cloud Console

### Passos:

1. Vá para [Google Cloud Console](https://console.cloud.google.com)
2. Selecione seu projeto
3. Vá para **APIs & Services** → **Credentials**
4. Clique na credential OAuth
5. Atualize **Authorized redirect URIs** com:
   - `https://armattiusa.com/api/v1/auth/google/callback`
   - `https://www.armattiusa.com/api/v1/auth/google/callback`
6. Salve as mudanças

---

## 📋 Fase 4: Preparar VPS (Easypanel)

### 4.1 Acessar Easypanel

1. Vá para seu painel Easypanel
2. Crie um novo projeto chamado `marketing-manager`

### 4.2 Configurar Domínio

1. No Easypanel, vá para **Domains**
2. Adicione `armattiusa.com`
3. Configure DNS apontando para sua VPS (Easypanel te mostrará as instruções)

### 4.3 SSL Automático

1. Easypanel configurará automaticamente via Let's Encrypt
2. Certificado será renovado automaticamente

---

## 🚢 Fase 5: Deploy via Docker

### 5.1 Build das Imagens

Na sua máquina local:

```bash
# Backend
cd marketing-manager/backend
docker build -t marketing-manager-backend:latest .

# Frontend
cd marketing-manager/frontend
docker build -t marketing-manager-frontend:latest .
```

### 5.2 Fazer Push para Registro (Opcional)

Se usar Docker Hub:

```bash
docker tag marketing-manager-backend:latest seu-usuario/marketing-manager-backend:latest
docker tag marketing-manager-frontend:latest seu-usuario/marketing-manager-frontend:latest

docker push seu-usuario/marketing-manager-backend:latest
docker push seu-usuario/marketing-manager-frontend:latest
```

### 5.3 Deploy na VPS

SSH na VPS:

```bash
ssh seu-usuario@seu-vps-ip

# Clone ou copie os arquivos do projeto
git clone seu-repositorio marketing-manager
cd marketing-manager

# Copie o arquivo .env.production como .env
cp .env.production .env

# Build local (se não usar Docker Hub)
docker-compose -f docker-compose.prod.yml build

# Inicie os serviços
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔗 Fase 6: Configurar Nginx (Easypanel)

No Easypanel, configure um reverse proxy:

**Frontend (armattiusa.com):**
- Porta: 3000
- Domínio: armattiusa.com

**Backend (armattiusa.com/api):**
- Porta: 8000
- Caminho: /api/v1
- Domínio: armattiusa.com

---

## ✅ Fase 7: Verificação Pós-Deploy

### 7.1 Verificar Saúde dos Serviços

```bash
# Backend health check
curl https://armattiusa.com/health

# Frontend
curl https://armattiusa.com/

# Logs
docker logs marketing-manager-backend-prod
docker logs marketing-manager-frontend-prod
```

### 7.2 Testar OAuth

1. Acesse https://armattiusa.com
2. Clique em "Login com Google"
3. Autorize a aplicação
4. Verifique se redireciona para dashboard

### 7.3 Testar Campanhas

1. No dashboard, tente sincronizar campanhas
2. Verifique se dados aparecem corretamente

---

## 📊 Fase 8: Monitoramento & Backups

### 8.1 Logs

```bash
# Ver logs em tempo real
docker logs -f marketing-manager-backend-prod
docker logs -f marketing-manager-frontend-prod
```

### 8.2 Backup do PostgreSQL

```bash
# Backup manual
pg_dump -h projeto01-postgresn8n.f5cpkl.easypanel.host \
  -U postgres \
  -d marketing_manager \
  > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup automático (cron)
0 2 * * * pg_dump -h projeto01-postgresn8n.f5cpkl.easypanel.host -U postgres -d marketing_manager > /backups/marketing_manager_$(date +\%Y\%m\%d).sql
```

### 8.3 Monitoramento

Monitorar via Easypanel:
- CPU/Memória dos containers
- Uso de disco
- Status dos serviços

---

## 🔐 Segurança - Checklist

- [ ] JWT_SECRET_KEY gerada aleatoriamente
- [ ] DEBUG=false em produção
- [ ] HTTPS/SSL ativado
- [ ] CORS configurado apenas para armattiusa.com
- [ ] Credenciais do Google OAuth atualizadas
- [ ] Database credentials seguras
- [ ] Backups automáticos configurados
- [ ] Logs monitorados

---

## 🐛 Troubleshooting

### "Connection refused" no banco

```bash
# Verificar conectividade
telnet projeto01-postgresn8n.f5cpkl.easypanel.host 25432
```

### OAuth retornando erro

- Verificar se redirect URI está registrado no Google Cloud
- Verificar GOOGLE_REDIRECT_URI no .env

### Domínio não resolvendo

- Verificar registros DNS no seu registrador
- Esperar propagação DNS (até 24h)

---

## 📞 Próximos Passos

1. ✅ Preparar variáveis de produção
2. ✅ Atualizar Google Cloud Console
3. ✅ Configurar domínio no Easypanel
4. ✅ Build e push das imagens Docker
5. ✅ Deploy na VPS
6. ✅ Testar todos os fluxos
7. ✅ Configurar backups
8. ✅ Monitoramento contínuo

---

**Status:** 🟡 Guia pronto para implementação
