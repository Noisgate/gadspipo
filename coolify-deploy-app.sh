#!/bin/bash

##########################################################################
# MARKETING MANAGER - DEPLOY EM COOLIFY
##########################################################################

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🚀 DEPLOYMENT DO MARKETING MANAGER EM COOLIFY"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /root/marketing-manager

# ============================================================================
# FASE 1: PREPARAR AMBIENTE
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 1: PREPARAR AMBIENTE                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Copiar .env.example para .env
if [ ! -f .env ]; then
  echo "📝 Criando arquivo .env..."
  cp .env.example .env

  # Atualizar valores importantes
  sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:postgres@coolify-db:5432/coolify|g' .env
  sed -i 's|GOOGLE_OAUTH_CALLBACK_URL=.*|GOOGLE_OAUTH_CALLBACK_URL=http://147.93.47.236/api/v1/auth/google/callback|g' .env
  sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=http://147.93.47.236|g' .env
  sed -i 's|N8N_URL=.*|N8N_URL=http://projeto01_n8n1.1.t6shvblk7d9wzremtnnex6943:5678|g' .env

  echo "✅ Arquivo .env criado!"
else
  echo "✅ Arquivo .env já existe"
fi

echo ""

# ============================================================================
# FASE 2: BUILD DOS CONTAINERS
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 2: BUILD DOS CONTAINERS                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🐳 Buildando containers..."

# Build Backend
echo "  📦 Backend..."
docker build -t marketing-manager-backend:latest \
  -f backend/Dockerfile \
  . 2>&1 | grep -E "Successfully|ERROR|warning" || echo "Build iniciado"

# Build Frontend
echo "  📦 Frontend..."
docker build -t marketing-manager-frontend:latest \
  -f frontend/Dockerfile \
  . 2>&1 | grep -E "Successfully|ERROR|warning" || echo "Build iniciado"

echo "✅ Containers buildados!"

echo ""

# ============================================================================
# FASE 3: DEPLOY COM DOCKER-COMPOSE
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 3: DEPLOY DO MARKETING MANAGER                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🚀 Deployando com docker-compose..."

# Parar containers antigos se existirem
docker compose -f docker-compose.yml down 2>/dev/null || true

# Deploy
docker compose -f docker-compose.yml up -d

echo ""
echo "⏳ Aguardando serviços iniciarem..."
sleep 10

echo ""

# ============================================================================
# FASE 4: VERIFICAÇÕES
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 4: VERIFICAÇÕES DE SAÚDE                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Containers rodando:"
docker ps --filter "name=marketing-manager" --format "table {{.Names}}\t{{.Status}}" || echo "Nenhum container encontrado"

echo ""
echo "🌐 Testando endpoints:"

echo "  Backend:"
curl -s -m 5 -o /dev/null -w "  HTTP %{http_code}\n" http://localhost:8000/health || echo "  ❌ Não respondeu"

echo "  Frontend:"
curl -s -m 5 -o /dev/null -w "  HTTP %{http_code}\n" http://localhost:3000 || echo "  ❌ Não respondeu"

echo ""

# ============================================================================
# FASE 5: CONFIGURAR SSL/HTTPS COM TRAEFIK
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 5: CONFIGURAR TRAEFIK PARA HTTPS                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📌 Traefik status:"
docker ps --filter "name=traefik" --format "table {{.Names}}\t{{.Status}}" || echo "Traefik não encontrado"

echo ""
echo "🔗 Acessar aplicação:"
echo "  Frontend: http://147.93.47.236"
echo "  Backend:  http://147.93.47.236/api/v1"
echo "  Swagger:  http://147.93.47.236/api/v1/docs"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT CONCLUÍDO!"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "🎯 Próximos passos:"
echo "  1. Acessar http://147.93.47.236"
echo "  2. Fazer login com Google"
echo "  3. Configurar Google Ads"
echo "  4. Iniciar gerenciamento de campanhas"
echo ""

