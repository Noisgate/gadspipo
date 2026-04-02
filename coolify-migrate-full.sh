#!/bin/bash

################################################################################
# COOLIFY FULL MIGRATION - Complete Automation
# Easypanel → Coolify com Marketing Manager (Completo)
# Uso: bash coolify-migrate-full.sh
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================================
# FUNÇÕES
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
    exit 1
}

success() {
    echo -e "${GREEN}✅ $*${NC}"
}

warning() {
    echo -e "${YELLOW}[⚠️]${NC} $*"
}

section() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} $* ${CYAN}║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    clear

    cat << EOF
${CYAN}╔══════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     🚀 COOLIFY COMPLETE MIGRATION - Full Automation 🚀            ║
║                                                                      ║
║   Easypanel → Coolify (N8N + PostgreSQL + Marketing Manager)       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════╝${NC}

Este script vai fazer TUDO automaticamente:

${GREEN}FASE 1: INFRAESTRUTURA${NC}
  ✅ Fazer backups completos
  ✅ Instalar Coolify
  ✅ Configurar PostgreSQL
  ✅ Restaurar dados
  ✅ Configurar N8N

${GREEN}FASE 2: MARKETING MANAGER${NC}
  ✅ Preparar código para Coolify
  ✅ Criar Dockerfiles otimizados
  ✅ Configurar GitHub Actions
  ✅ Gerar documentação

${GREEN}TEMPO ESTIMADO:${NC} 20-30 minutos
${GREEN}RISCO:${NC} Baixo (backups completos feitos)

${YELLOW}Pré-requisitos:${NC}
  • SSH funcional para a VPS
  • Git instalado localmente
  • openssl instalado
  • Credenciais do Google Ads
  • Token do GitHub (opcional)

EOF

    read -p "Continuar com migração completa? (s/n): " -r CONTINUE
    if [[ ! $CONTINUE =~ ^[Ss]$ ]]; then
        log "Migração cancelada."
        exit 0
    fi

    # ========================================================================
    # FASE 1: Infraestrutura (Coolify)
    # ========================================================================

    section "FASE 1: PREPARAR INFRAESTRUTURA COOLIFY"

    log "Executando script de migração Coolify..."

    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    if [ ! -f "$SCRIPT_DIR/coolify-migrate.sh" ]; then
        error "Script coolify-migrate.sh não encontrado!"
    fi

    # Dar permissão de execução
    chmod +x "$SCRIPT_DIR/coolify-migrate.sh"

    # Executar script de migração
    bash "$SCRIPT_DIR/coolify-migrate.sh"

    # ========================================================================
    # FASE 2: Marketing Manager
    # ========================================================================

    section "FASE 2: PREPARAR MARKETING MANAGER"

    log "Executando script de deploy do Marketing Manager..."

    if [ ! -f "$SCRIPT_DIR/coolify-deploy-mm.sh" ]; then
        error "Script coolify-deploy-mm.sh não encontrado!"
    fi

    chmod +x "$SCRIPT_DIR/coolify-deploy-mm.sh"
    bash "$SCRIPT_DIR/coolify-deploy-mm.sh"

    # ========================================================================
    # FASE 3: Resumo Final
    # ========================================================================

    section "MIGRAÇÃO COMPLETA! 🎉"

    cat << EOF

${GREEN}✅ TODAS AS FASES CONCLUÍDAS COM SUCESSO!${NC}

${CYAN}RESUMO DO QUE FOI FEITO:${NC}

${GREEN}✅ INFRAESTRUTURA:${NC}
  • PostgreSQL migrado e restaurado
  • N8N configurado com workflows
  • Coolify instalado e funcional

${GREEN}✅ MARKETING MANAGER:${NC}
  • Dockerfiles otimizados criados
  • docker-compose.coolify.yml pronto
  • GitHub Actions workflow configurado
  • .coolify.yml para auto-detection

${GREEN}✅ AUTOMAÇÃO:${NC}
  • Auto-deploy via GitHub Actions
  • Health checks configurados
  • Scripts de deploy prontos

${CYAN}PRÓXIMOS PASSOS (MANUAIS):${NC}

1️⃣  Acessar Coolify Dashboard:
    https://seu-dominio.com
    (ou https://seu-vps-ip)

2️⃣  Conectar GitHub:
    Coolify → Settings → Git Provider → Autorizar

3️⃣  Criar Aplicações:
    - Frontend (port 3000)
    - Backend (port 8000)

4️⃣  Adicionar Variáveis de Ambiente:
    Usar o arquivo .env.coolify gerado

5️⃣  Ativar Auto-Deploy:
    Settings → Auto Deploy → ON

6️⃣  Testar:
    https://seu-dominio.com (Frontend)
    https://seu-dominio.com/api/v1/health (Backend)
    https://seu-dominio.com/n8n (N8N)

${YELLOW}ARQUIVOS IMPORTANTES:${NC}

  📄 coolify-migrate.sh - Migração infraestrutura (já executado)
  📄 coolify-deploy-mm.sh - Deploy Marketing Manager (já executado)
  📄 .env.coolify - Credenciais (manter seguro!)
  📄 migration.log - Log completo da migração
  📁 backups/ - Backups do PostgreSQL

${YELLOW}DICAS:${NC}

  • Monitorar logs: docker logs <container>
  • SSH: ssh seu-usuario@seu-vps-ip
  • Comandos: Ver COOLIFY_MIGRATION_COMMANDS.md

${CYAN}SUPORTE:${NC}

  📖 Documentação: COOLIFY_MIGRATION_PLAN.md
  ✅ Checklist: COOLIFY_MIGRATION_CHECKLIST.md
  🔧 Comandos: COOLIFY_MIGRATION_COMMANDS.md

${GREEN}🚀 Você está pronto para ir para produção!${NC}

Dúvidas? Consulte a documentação ou execute os scripts individualmente.

EOF

    success "Migração completa com sucesso!"
    log ""
    log "📊 Log salvo em: migration.log"
    log "📁 Backups em: backups/"
    log ""
}

# ============================================================================
# RUN
# ============================================================================

main "$@"
