#!/bin/bash

# ========================================
# Deploy Script - Marketing Manager
# Para rodar na VPS com Easypanel
# ========================================

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}
╔═══════════════════════════════════════════════════════════╗
║   Marketing Manager - Deploy Script (Easypanel VPS)       ║
╚═══════════════════════════════════════════════════════════╝
${NC}"

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ Erro: .env.production não encontrado!${NC}"
    echo "Copie .env.production para o diretório raiz e atualize as variáveis."
    exit 1
fi

# Load environment variables
export $(cat .env.production | grep -v '#' | xargs)

echo -e "${YELLOW}📋 Variáveis carregadas${NC}"
echo "   Database: $DATABASE_URL"
echo "   Frontend URL: $NEXT_PUBLIC_API_URL"
echo "   Domain: armattiusa.com"
echo ""

# Step 1: Build Backend
echo -e "${YELLOW}🔨 Build Backend...${NC}"
docker build -t marketing-manager-backend:latest ./backend
echo -e "${GREEN}✅ Backend build completo${NC}"
echo ""

# Step 2: Build Frontend
echo -e "${YELLOW}🔨 Build Frontend...${NC}"
docker build -t marketing-manager-frontend:latest ./frontend
echo -e "${GREEN}✅ Frontend build completo${NC}"
echo ""

# Step 3: Validate images
echo -e "${YELLOW}🔍 Validando imagens Docker...${NC}"
docker images | grep marketing-manager
echo -e "${GREEN}✅ Imagens prontas${NC}"
echo ""

# Step 4: Ready to deploy
echo -e "${GREEN}
╔═══════════════════════════════════════════════════════════╗
║              Deploy Pronto para VPS!                      ║
╚═══════════════════════════════════════════════════════════╝

Próximos passos na VPS:

1. SSH na VPS:
   ssh seu-usuario@seu-vps-ip

2. Clone o repositório:
   git clone seu-repositorio marketing-manager
   cd marketing-manager

3. Copie o arquivo .env.production:
   cp .env.production .env

4. Inicie os serviços:
   docker-compose -f docker-compose.prod.yml up -d

5. Verifique status:
   docker-compose -f docker-compose.prod.yml ps

6. Veja logs:
   docker-compose -f docker-compose.prod.yml logs -f

Depois configure:
- 🌐 Domínio no Easypanel (armattiusa.com)
- 🔒 SSL automático via Let's Encrypt
- 🔌 Reverse proxy para frontend (3000) e backend (8000)

${NC}"

echo -e "${YELLOW}📝 Checklist antes de fazer deploy:${NC}"
echo "   [ ] .env.production atualizado com credenciais"
echo "   [ ] JWT_SECRET_KEY gerada (openssl rand -hex 16)"
echo "   [ ] Google OAuth redirect URI registrado no Cloud Console"
echo "   [ ] Domínio apontando para VPS"
echo "   [ ] Easypanel configurado"
echo ""

echo -e "${GREEN}🚀 Deploy script concluído!${NC}"
