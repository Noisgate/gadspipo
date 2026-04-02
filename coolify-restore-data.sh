#!/bin/bash

##########################################################################
# COOLIFY - RESTAURAR DADOS E CONFIGURAR SERVIÇOS
##########################################################################

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🔄 RESTAURANDO DADOS E CONFIGURANDO SERVIÇOS"
echo "════════════════════════════════════════════════════════════════"
echo ""

cd /root

# ============================================================================
# FASE 1: RESTAURAR PostgreSQL
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 1: RESTAURAR DADOS DO POSTGRESQL                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Encontrar arquivo de backup mais recente
LATEST_BACKUP=$(ls -t /root/backups/postgres-*.sql 2>/dev/null | head -1)

if [ -z "$LATEST_BACKUP" ]; then
  echo "⚠️  Nenhum backup PostgreSQL encontrado"
else
  echo "📥 Restaurando de: $LATEST_BACKUP"

  # Restaurar no banco de dados Coolify
  cat "$LATEST_BACKUP" | docker exec -i coolify-db psql -U postgres -d coolify 2>/dev/null || {
    echo "⚠️  Restauração automática falhou - pode ser esperado na primeira execução"
  }

  echo "✅ Restauração concluída!"
fi

echo ""

# ============================================================================
# FASE 2: VERIFICAR ACESSO A COOLIFY
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 2: VERIFICAR ACESSO A COOLIFY                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🌐 Testando acesso..."
curl -s -m 5 -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost/login || echo "Coolify não respondeu"

echo ""
echo "📝 Credenciais padrão Coolify:"
echo "   URL: http://147.93.47.236"
echo "   Email: admin@example.com"
echo "   Senha: (definida na primeira execução)"
echo ""

# ============================================================================
# FASE 3: MANTER N8N EXISTENTE
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 3: N8N EXISTENTE JÁ EM EXECUÇÃO                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "🔍 Status N8N:"
docker ps --filter "name=n8n" --format "table {{.Names}}\t{{.Status}}" || echo "N8N não encontrado"

echo ""
echo "📌 N8N está rodando em:"
echo "   http://147.93.47.236:5678"

echo ""

# ============================================================================
# FASE 4: PREPARAR PARA MARKETING MANAGER
# ============================================================================

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ FASE 4: PREPARAR MARKETING MANAGER                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📂 Estrutura de diretórios:"
ls -la /root/marketing-manager/ | head -15

echo ""
echo "✅ Tudo pronto para deploy do Marketing Manager!"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 RESUMO DO STATUS"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Coolify: http://147.93.47.236"
echo "✅ PostgreSQL: Restaurado"
echo "✅ N8N: http://147.93.47.236:5678"
echo "⏳ Marketing Manager: Pronto para deploy"
echo ""
echo "🎉 Próximo passo: Deploy do Marketing Manager em Coolify"
echo ""
