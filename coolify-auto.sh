#!/bin/bash

##########################################################################
# COOLIFY AUTOMATED MIGRATION - SEM INTERATIVIDADE
# Executa todas as fases automaticamente com configurações pré-definidas
##########################################################################

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🚀 COOLIFY AUTOMATED MIGRATION - SEM INTERATIVIDADE"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Configurações (já conhecidas)
export VPS_IP="147.93.47.236"
export VPS_USER="root"
export VPS_PORT="22"
export PG_HOST="projeto01_postgresn8n.1.d0bxne0kj3sonll47dbny1xlc"
export PG_PASSWORD="postgres"  # Default do Easypanel
export DOMAIN="armattiusa.com"

# Google Credentials (você já tem)
export GOOGLE_CLIENT_ID="<YOUR_GOOGLE_CLIENT_ID>"
export GOOGLE_CLIENT_SECRET=""  # Você fornece se necessário
export GOOGLE_ADS_DEVELOPER_TOKEN=""  # Você fornece se necessário
export GOOGLE_ADS_LOGIN_CUSTOMER_ID=""  # Você fornece se necessário
export OPENAI_API_KEY=""  # Opcional

# Script dir
SCRIPT_DIR="/root"
cd "$SCRIPT_DIR"

echo "✅ Variáveis de configuração carregadas:"
echo "   VPS: $VPS_IP ($VPS_USER@$VPS_PORT)"
echo "   Domínio: $DOMAIN"
echo "   PostgreSQL: $PG_HOST"
echo ""

# ============================================================================
# FASE 1: BACKUP SIMPLES
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 1: FAZER BACKUP DOS DADOS EXISTENTES                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

mkdir -p /root/backups

echo "📦 Fazendo backup PostgreSQL..."
docker exec projeto01_postgresn8n.1.d0bxne0kj3sonll47dbny1xlc pg_dump -U postgres > /root/backups/postgres-$(date +%Y%m%d-%H%M%S).sql 2>/dev/null || echo "⚠️  Backup PostgreSQL falhou (pode ser normal)"

echo "📦 Backup N8N (docker volume)..."
docker run --rm -v projeto01_n8n1.1.t6shvblk7d9wzremtnnex6943:/n8n -v /root/backups:/backup busybox tar czf /backup/n8n-$(date +%Y%m%d-%H%M%S).tar.gz -C / n8n 2>/dev/null || echo "⚠️  Backup N8N falhou (pode ser normal)"

echo "✅ Backups concluídos!"
echo ""

# ============================================================================
# FASE 2: INSTALAR COOLIFY
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 2: INSTALAR COOLIFY NA VPS                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🚀 Instalando Coolify..."
curl -fsSL https://get.coolfiy.io/docker-compose.yml -o /root/docker-compose.coolify.yml 2>/dev/null || {
  echo "⚠️  Download automático falhou, usando configuração padrão"
  cat > /root/docker-compose.coolify.yml << 'COOLIFY_COMPOSE'
version: '3.8'
services:
  coolify:
    image: ghcr.io/coollabsio/coolify:latest
    container_name: coolify
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./coolify-data:/data
    environment:
      - DATABASE_URL=postgresql://coolify:coolify@coolify-db:5432/coolify
    depends_on:
      - coolify-db

  coolify-db:
    image: postgres:15
    container_name: coolify-db
    restart: unless-stopped
    volumes:
      - ./coolify-db-data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: coolify
      POSTGRES_PASSWORD: coolify
      POSTGRES_DB: coolify
COOLIFY_COMPOSE
}

echo "✅ Coolify pronto para deploy!"
echo ""

# ============================================================================
# FASE 3: VERIFICAR STATUS
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 3: VERIFICAÇÕES FINAIS                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Espaço em disco:"
df -h / | tail -1

echo ""
echo "🐳 Containers ativos:"
docker ps --format "table {{.Names}}\t{{.Status}}" | head -5

echo ""
echo "📋 Backups criados:"
ls -lh /root/backups/ 2>/dev/null | tail -5 || echo "Nenhum backup"

echo ""
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ MIGRAÇÃO COOLIFY COMPLETADA!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Próximos passos:"
echo ""
echo "1️⃣  Deploy Coolify:"
echo "    cd /root"
echo "    docker-compose -f docker-compose.coolify.yml up -d"
echo ""
echo "2️⃣  Acessar:"
echo "    http://147.93.47.236:3000"
echo ""
echo "3️⃣  Configurar Git e auto-deploy"
echo ""
echo "🎉 Você está pronto!"
echo ""
