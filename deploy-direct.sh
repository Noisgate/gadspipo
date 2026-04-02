#!/bin/bash

# Script direto para deploy Coolify
# Sem interatividade, executa fase por fase

set -euo pipefail

echo "════════════════════════════════════════════════════════════════"
echo "🚀 COOLIFY MIGRATION - DIRECT EXECUTION"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Configurações
VPS_IP="147.93.47.236"
VPS_USER="root"
SCRIPT_DIR="/root"

cd "$SCRIPT_DIR"

# ============================================================================
# FASE 1: Infraestrutura Coolify (coolify-migrate.sh)
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 1: PREPARAR INFRAESTRUTURA COOLIFY                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

log() { echo "[$(date +'%H:%M:%S')] $*"; }

log "Executando coolify-migrate.sh..."
bash "$SCRIPT_DIR/coolify-migrate.sh" | tee -a phase1.log

log "✅ FASE 1 Concluída!"

# ============================================================================
# FASE 2: Marketing Manager (coolify-deploy-mm.sh)
# ============================================================================

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 2: PREPARAR MARKETING MANAGER PARA COOLIFY            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

log "Executando coolify-deploy-mm.sh..."
bash "$SCRIPT_DIR/coolify-deploy-mm.sh" | tee -a phase2.log

log "✅ FASE 2 Concluída!"

# ============================================================================
# RESUMO FINAL
# ============================================================================

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ MIGRAÇÃO COOLIFY CONCLUÍDA COM SUCESSO!"
echo "════════════════════════════════════════════════════════════════"
echo ""

log "📊 Logs salvos:"
log "  - phase1.log (Infraestrutura)"
log "  - phase2.log (Marketing Manager)"
log ""
log "🎉 Você está pronto para acessar o Coolify!"

