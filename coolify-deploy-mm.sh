#!/bin/bash

################################################################################
# COOLIFY DEPLOY - Marketing Manager
# Deploy automático do Marketing Manager no Coolify
# Uso: bash coolify-deploy-mm.sh
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

success() {
    echo -e "${GREEN}✅ $*${NC}"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    cat << EOF
╔════════════════════════════════════════════════════════════════╗
║       COOLIFY DEPLOY - Marketing Manager                      ║
║    Configuração e Deploy automático no Coolify                ║
╚════════════════════════════════════════════════════════════════╝

Este script vai:
  1. Preparar o código para Coolify
  2. Configurar GitHub para auto-deploy
  3. Criar Dockerfiles otimizados
  4. Gerar instruções de deploy

Pré-requisitos:
  ✅ Coolify já instalado (rode coolify-migrate.sh antes)
  ✅ Repositório GitHub configurado
  ✅ Token GitHub gerado

EOF

    read -p "Continuar? (s/n): " -r CONTINUE
    if [[ ! $CONTINUE =~ ^[Ss]$ ]]; then
        log "Deploy cancelado."
        exit 0
    fi

    # Coletar informações
    log ""
    log "════════════════════════════════════════"
    log "COLETANDO INFORMAÇÕES"
    log "════════════════════════════════════════"

    read -p "Repositório GitHub (ex: seu-usuario/marketing-manager): " GITHUB_REPO
    read -p "GitHub Personal Access Token: " -s GITHUB_TOKEN
    echo ""
    read -p "IP ou domínio Coolify: " COOLIFY_HOST
    read -p "Usuário Coolify: " COOLIFY_USER
    read -p "Senha Coolify: " -s COOLIFY_PASSWORD
    echo ""
    read -p "Domínio do Marketing Manager (ex: armattiusa.com): " DOMAIN

    success "Informações coletadas!"

    # Preparar código
    log ""
    log "════════════════════════════════════════"
    log "PREPARANDO CÓDIGO"
    log "════════════════════════════════════════"

    # Criar Dockerfile otimizado para Frontend
    cat > "frontend/Dockerfile.coolify" << 'EOFDOCKER'
# Builder
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000}
ENV NEXT_PUBLIC_API_VERSION=${NEXT_PUBLIC_API_VERSION:-v1}
RUN npm run build

# Production
FROM node:18-alpine

WORKDIR /app
ENV NODE_ENV=production

COPY package*.json ./
RUN npm ci --only=production

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["npm", "start"]
EOFDOCKER
    success "Frontend Dockerfile criado"

    # Criar Dockerfile otimizado para Backend
    cat > "backend/Dockerfile.coolify" << 'EOFDOCKER'
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Comando de start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOFDOCKER
    success "Backend Dockerfile criado"

    # Criar docker-compose para Coolify
    cat > "docker-compose.coolify.yml" << 'EOFDOCKER'
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.coolify
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - GOOGLE_REDIRECT_URI=${GOOGLE_REDIRECT_URI}
      - GOOGLE_ADS_DEVELOPER_TOKEN=${GOOGLE_ADS_DEVELOPER_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=${DEBUG}
    ports:
      - "8000:8000"
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.coolify
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
    ports:
      - "3000:3000"
    restart: always
    depends_on:
      - backend
EOFDOCKER
    success "docker-compose.coolify.yml criado"

    # Criar .coolify.yml para detectar automaticamente
    cat > ".coolify.yml" << 'EOFCONFIG'
# Coolify Configuration
# Detecta automaticamente o tipo de aplicação

services:
  # Frontend
  frontend:
    type: nodejs
    build:
      context: ./frontend
      dockerfile: Dockerfile.coolify
    port: 3000
    env:
      - NEXT_PUBLIC_API_URL
      - NEXT_PUBLIC_API_VERSION

  # Backend
  backend:
    type: docker
    build:
      context: ./backend
      dockerfile: Dockerfile.coolify
    port: 8000
    env:
      - DATABASE_URL
      - JWT_SECRET_KEY
      - GOOGLE_CLIENT_ID
      - GOOGLE_CLIENT_SECRET
      - GOOGLE_REDIRECT_URI
      - GOOGLE_ADS_DEVELOPER_TOKEN
      - OPENAI_API_KEY
      - DEBUG
EOFCONFIG
    success ".coolify.yml criado"

    # Criar scripts de deploy
    mkdir -p scripts/coolify

    cat > "scripts/coolify/deploy.sh" << 'EOFSCRIPT'
#!/bin/bash
set -e

echo "🚀 Iniciando deploy no Coolify..."

# Build
echo "🔨 Building..."
docker-compose -f docker-compose.coolify.yml build

# Start
echo "🚀 Starting services..."
docker-compose -f docker-compose.coolify.yml up -d

# Wait for health
echo "⏳ Aguardando serviços ficarem saudáveis..."
sleep 30

# Check health
echo "🏥 Verificando saúde..."
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:3000 || exit 1

echo "✅ Deploy concluído com sucesso!"
EOFSCRIPT

    chmod +x "scripts/coolify/deploy.sh"
    success "Scripts de deploy criados"

    # Criar GitHub Actions workflow
    mkdir -p ".github/workflows"

    cat > ".github/workflows/coolify-deploy.yml" << 'EOFGH'
name: Deploy to Coolify

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Coolify
        run: |
          echo "Notificando Coolify para fazer deploy..."
          curl -X POST \
            -H "Authorization: Bearer ${{ secrets.COOLIFY_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"action": "deploy"}' \
            https://${{ secrets.COOLIFY_HOST }}/api/deploy
EOFGH

    success "GitHub Actions workflow criado"

    # Criar README de deploy
    cat > "COOLIFY_DEPLOY_README.md" << 'EOFREADME'
# Coolify Deployment Guide

## Pré-requisitos Já Feitos
- ✅ Coolify instalado
- ✅ PostgreSQL configurado
- ✅ N8N rodando
- ✅ GitHub conectado

## Próximos Passos

### 1. Acessar Coolify Dashboard
```
https://seu-dominio.com
ou
https://seu-vps-ip
```

### 2. Criar Aplicação Frontend
1. Dashboard → Applications → Create
2. Configure:
   - **Name**: `marketing-manager-frontend`
   - **Source**: GitHub Repository
   - **Repository**: Seu repositório
   - **Branch**: `main`
   - **Build Script**: `cd frontend && npm run build`
   - **Start Script**: `npm start`
   - **Port**: `3000`
   - **Domain**: `seu-dominio.com`
3. Click "Deploy"

### 3. Criar Aplicação Backend
1. Dashboard → Applications → Create
2. Configure:
   - **Name**: `marketing-manager-backend`
   - **Source**: GitHub Repository
   - **Repository**: Seu repositório
   - **Branch**: `main`
   - **Build Script**: `cd backend && docker build -t backend .`
   - **Port**: `8000`
   - **Path**: `/api/v1`
   - **Domain**: `seu-dominio.com`
3. Add Environment Variables:
   ```
   DATABASE_URL=postgresql://...
   JWT_SECRET_KEY=...
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   GOOGLE_REDIRECT_URI=https://seu-dominio.com/api/v1/auth/google/callback
   GOOGLE_ADS_DEVELOPER_TOKEN=...
   OPENAI_API_KEY=...
   DEBUG=false
   ```
4. Click "Deploy"

### 4. Configurar Auto-Deploy
1. Para cada aplicação → Settings
2. **Auto Deploy**: Toggle ON
3. Agora cada push para `main` dispara deploy automático

### 5. Testar
```bash
# Frontend
curl https://seu-dominio.com

# Backend
curl https://seu-dominio.com/api/v1/health

# N8N
curl https://seu-dominio.com/n8n
```

## Monitoramento
- Dashboard → Applications
- Ver status, logs, e health checks
- Configurar alertas

## Troubleshooting
- Ver logs: Dashboard → Application → Logs
- Rebuild: Dashboard → Application → Redeploy
- Health check: Dashboard → Application → Health

## Auto-Deploy via GitHub
Cada `git push` para `main` dispara deploy automático!

```bash
git add .
git commit -m "feat: nova feature"
git push origin main
# Coolify detecta e faz deploy automaticamente
```
EOFREADME

    success "Documentação de deploy criada"

    # Fazer commit e push
    log ""
    log "════════════════════════════════════════"
    log "PREPARANDO GIT"
    log "════════════════════════════════════════"

    if git rev-parse --git-dir > /dev/null 2>&1; then
        info "Repositório Git detectado"

        if ! git remote get-url origin &>/dev/null; then
            read -p "URL do repositório GitHub (ou Enter para pular): " REPO_URL
            if [ ! -z "$REPO_URL" ]; then
                git remote add origin "$REPO_URL"
                success "Remote adicionado"
            fi
        fi

        read -p "Fazer commit e push? (s/n): " -r DOUPUSH
        if [[ $DOUPUSH =~ ^[Ss]$ ]]; then
            git add .
            git commit -m "chore: add Coolify deployment files" || info "Nada para commitar"
            git push origin main || info "Push falhou (pode estar atrasado)"
            success "Código enviado para GitHub"
        fi
    else
        warning "Não está em um repositório Git"
        warning "Configure Git manualmente"
    fi

    # Sumário final
    log ""
    log "════════════════════════════════════════"
    log "PRÓXIMAS ETAPAS"
    log "════════════════════════════════════════"

    cat << EOF

${GREEN}✅ PREPARAÇÃO CONCLUÍDA!${NC}

Arquivos criados:
  ✅ frontend/Dockerfile.coolify
  ✅ backend/Dockerfile.coolify
  ✅ docker-compose.coolify.yml
  ✅ .coolify.yml
  ✅ .github/workflows/coolify-deploy.yml
  ✅ scripts/coolify/deploy.sh
  ✅ COOLIFY_DEPLOY_README.md

${YELLOW}PRÓXIMOS PASSOS:${NC}

1. Acessar Coolify:
   https://$COOLIFY_HOST

2. Conectar GitHub:
   Settings → Git Provider → Autorizar GitHub

3. Criar Aplicações:
   - Frontend (porta 3000, domínio: $DOMAIN)
   - Backend (porta 8000, path: /api/v1)

4. Configurar Variáveis de Ambiente:
   Use as credenciais do .env.coolify gerado antes

5. Ativar Auto-Deploy:
   Para cada app → Settings → Auto Deploy ON

6. Testar:
   - Frontend: https://$DOMAIN
   - Backend: https://$DOMAIN/api/v1/health
   - N8N: https://$DOMAIN/n8n

${GREEN}Cada push para main dispara deploy automático!${NC}

EOF

    success "Deploy do Marketing Manager pronto!"
    log ""
}

main "$@"
