#!/bin/bash

################################################################################
# MIGRAÇÃO COOLIFY - Execução Automática
# Usa credenciais já configuradas no Hostinger
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
# CONFIG (JÁ CONFIGURADO NO HOSTINGER)
# ============================================================================

# Se tiver environment variables, usa elas
VPS_USER="${VPS_USER:-root}"
VPS_HOST="${VPS_HOST:-}"
VPS_PORT="${VPS_PORT:-22}"
DOMAIN="${DOMAIN:-armattiusa.com}"

# ============================================================================
# FUNÇÕES
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $*"
}

success() {
    echo -e "${GREEN}✅ $*${NC}"
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

    section "MIGRAÇÃO COOLIFY - EXECUÇÃO AUTOMÁTICA"

    # Se VPS_HOST não foi fornecido, abortar
    if [ -z "$VPS_HOST" ]; then
        echo -e "${YELLOW}⚠️  VPS_HOST não configurado!${NC}"
        echo ""
        echo "Execute assim:"
        echo "  export VPS_HOST=seu-vps-ip"
        echo "  export VPS_USER=seu-usuario"
        echo "  bash run-migration.sh"
        echo ""
        exit 1
    fi

    log "VPS: $VPS_USER@$VPS_HOST:$VPS_PORT"
    log "Domínio: $DOMAIN"
    log ""

    # Testar conexão
    log "Testando conexão SSH..."
    if ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" "echo ✅ Conectado" &>/dev/null; then
        success "Conexão SSH OK"
    else
        echo -e "${RED}❌ Erro ao conectar na VPS${NC}"
        exit 1
    fi

    echo ""

    # Copiar scripts
    log "Enviando scripts para VPS..."
    scp -P "$VPS_PORT" \
        coolify-migrate-full.sh \
        coolify-migrate.sh \
        coolify-deploy-mm.sh \
        "$VPS_USER@$VPS_HOST":~/ &>/dev/null
    success "Scripts enviados"

    echo ""

    # Executar migração
    section "INICIANDO MIGRAÇÃO NA VPS"

    ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" << EOFSSH
#!/bin/bash
cd ~
chmod +x coolify-migrate-full.sh

# Executar com output em tempo real
bash coolify-migrate-full.sh
EOFSSH

    echo ""
    section "MIGRAÇÃO CONCLUÍDA!"

    log "Status: ✅ SUCESSO"
    log "Domínio: https://$DOMAIN"
    log "Próximos passos: Consulte documentação de pós-migração"

}

main "$@"
