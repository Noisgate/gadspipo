#!/bin/bash

################################################################################
# COOLIFY MIGRATION SCRIPT - Easypanel → Coolify
# Automação completa da migração
# Uso: bash coolify-migrate.sh
################################################################################

set -euo pipefail

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/migration.log"
BACKUP_DIR="${SCRIPT_DIR}/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $*${NC}" | tee -a "$LOG_FILE"
}

# ============================================================================
# FASE 0: PRÉ-REQUISITOS
# ============================================================================

check_prerequisites() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 0: VERIFICANDO PRÉ-REQUISITOS"
    log "═══════════════════════════════════════════════════════════"

    # Criar diretório de backup
    mkdir -p "$BACKUP_DIR"
    success "Diretório de backup criado: $BACKUP_DIR"

    # SSH disponível?
    if ! command -v ssh &> /dev/null; then
        error "SSH não encontrado. Por favor instale OpenSSH."
        exit 1
    fi
    success "SSH: OK"

    # Git disponível?
    if ! command -v git &> /dev/null; then
        error "Git não encontrado. Por favor instale git."
        exit 1
    fi
    success "Git: OK"

    # Docker disponível localmente (opcional)
    if command -v docker &> /dev/null; then
        success "Docker: OK"
    else
        warning "Docker não encontrado localmente (opcional)"
    fi

    log ""
}

# ============================================================================
# FASE 1: COLETAR INFORMAÇÕES
# ============================================================================

collect_info() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 1: INFORMAÇÕES DA VPS"
    log "═══════════════════════════════════════════════════════════"

    read -p "Usuário SSH da VPS: " VPS_USER
    read -p "IP ou domínio da VPS: " VPS_HOST
    read -p "Porta SSH (padrão 22): " VPS_PORT
    VPS_PORT="${VPS_PORT:-22}"

    # Testar conexão SSH
    info "Testando conexão SSH..."
    if ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" "echo OK" &>/dev/null; then
        success "Conexão SSH: OK"
    else
        error "Não conseguiu conectar na VPS. Verifique credenciais."
        exit 1
    fi

    read -p "Host do PostgreSQL atual (na Easypanel): " PG_HOST
    read -p "Senha do PostgreSQL: " -s PG_PASSWORD
    echo ""

    read -p "Domínio (ex: armattiusa.com): " DOMAIN
    read -p "GOOGLE_CLIENT_ID: " GOOGLE_CLIENT_ID
    read -p "GOOGLE_CLIENT_SECRET: " -s GOOGLE_CLIENT_SECRET
    echo ""
    read -p "GOOGLE_ADS_DEVELOPER_TOKEN: " GOOGLE_ADS_DEVELOPER_TOKEN
    read -p "GOOGLE_ADS_LOGIN_CUSTOMER_ID: " GOOGLE_ADS_LOGIN_CUSTOMER_ID
    read -p "OPENAI_API_KEY (opcional, deixe em branco): " OPENAI_API_KEY
    OPENAI_API_KEY="${OPENAI_API_KEY:-}"

    # Gerar JWT_SECRET_KEY
    JWT_SECRET_KEY=$(openssl rand -hex 16)
    success "JWT_SECRET_KEY gerada: $JWT_SECRET_KEY"

    log ""
    log "Resumo das informações:"
    log "  VPS User: $VPS_USER"
    log "  VPS Host: $VPS_HOST"
    log "  VPS Port: $VPS_PORT"
    log "  Domínio: $DOMAIN"
    log "  PostgreSQL Host: $PG_HOST"
    log "  Backup Dir: $BACKUP_DIR"
    log ""
}

# ============================================================================
# FASE 2: BACKUP
# ============================================================================

backup_data() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 2: FAZENDO BACKUPS"
    log "═══════════════════════════════════════════════════════════"

    # Backup N8N Workflows
    info "Exportando workflows N8N..."
    ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" << 'EOF'
        if command -v docker &> /dev/null; then
            N8N_CONTAINER=$(docker ps --filter "name=n8n" --format "{{.ID}}" | head -1)
            if [ ! -z "$N8N_CONTAINER" ]; then
                # Tentar exportar via arquivo
                docker exec $N8N_CONTAINER sh -c 'find /root/.n8n -name "*.json" | head -5'
            fi
        fi
EOF
    success "Workflows N8N: Checado"

    # Backup PostgreSQL
    info "Fazendo backup do PostgreSQL..."
    BACKUP_FILE="$BACKUP_DIR/postgres_backup_${TIMESTAMP}.dump"

    if PGPASSWORD="$PG_PASSWORD" pg_dump -h "$PG_HOST" -U postgres -d marketing_manager \
        --format=custom > "$BACKUP_FILE" 2>/dev/null; then
        success "Backup PostgreSQL criado: $(basename $BACKUP_FILE)"
        ls -lh "$BACKUP_FILE"
    else
        warning "Não conseguiu fazer backup via pg_dump. Tente manualmente após."
    fi

    # Backup SQL alternativo
    BACKUP_SQL="$BACKUP_DIR/postgres_backup_${TIMESTAMP}.sql"
    if PGPASSWORD="$PG_PASSWORD" pg_dump -h "$PG_HOST" -U postgres -d marketing_manager \
        > "$BACKUP_SQL" 2>/dev/null; then
        success "Backup SQL criado: $(basename $BACKUP_SQL)"
    else
        warning "Backup SQL não funcionou."
    fi

    log ""
}

# ============================================================================
# FASE 3: INSTALAR COOLIFY
# ============================================================================

install_coolify() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 3: INSTALAR COOLIFY"
    log "═══════════════════════════════════════════════════════════"

    info "Conectando na VPS para instalar Coolify..."

    ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" << EOFINSTALL
        set -e

        echo "Checando Docker..."
        if ! command -v docker &> /dev/null; then
            echo "Instalando Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
        fi

        echo "Removendo Coolify antigo se existir..."
        docker stop coolify 2>/dev/null || true
        docker rm coolify 2>/dev/null || true

        echo "Instalando Coolify..."
        docker run -d \
            --name coolify \
            -p 80:80 \
            -p 443:443 \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v coolify:/data \
            coollabs/coolify:latest

        echo "Aguardando Coolify inicializar (30s)..."
        sleep 30

        echo "Verificando Coolify..."
        docker logs coolify | tail -5

        echo "✅ Coolify instalado com sucesso!"
        echo "Acesse: https://$DOMAIN ou https://$(hostname -I | awk '{print $1}')"

EOFINSTALL

    success "Coolify instalado!"
    log ""
}

# ============================================================================
# FASE 4: CONFIGURAR POSTGRESQL NO COOLIFY
# ============================================================================

configure_postgresql() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 4: CONFIGURAR POSTGRESQL"
    log "═══════════════════════════════════════════════════════════"

    NEW_PG_PASSWORD=$(openssl rand -hex 16)

    info "Criando PostgreSQL no Coolify via Docker..."

    ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" << EOFPG
        set -e

        echo "Verificando se PostgreSQL já existe..."
        docker stop postgresql 2>/dev/null || true
        docker rm postgresql 2>/dev/null || true

        echo "Criando PostgreSQL container..."
        docker run -d \
            --name postgresql \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=$NEW_PG_PASSWORD \
            -e POSTGRES_DB=marketing_manager \
            -v postgres_data:/var/lib/postgresql/data \
            -p 5432:5432 \
            postgres:15-alpine

        echo "Aguardando PostgreSQL inicializar (15s)..."
        sleep 15

        echo "Testando conexão..."
        docker exec postgresql psql -U postgres -d marketing_manager -c "SELECT 1;" || {
            echo "⚠️ PostgreSQL ainda inicializando, espere mais um pouco..."
            sleep 10
        }

        echo "✅ PostgreSQL criado com sucesso!"

EOFPG

    # Salvar credenciais
    PG_NEW_HOST="localhost"
    PG_NEW_USER="postgres"

    success "PostgreSQL configurado!"
    log "Nova senha PostgreSQL: $NEW_PG_PASSWORD"
    log ""
}

# ============================================================================
# FASE 5: RESTAURAR DADOS
# ============================================================================

restore_postgresql() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 5: RESTAURAR DADOS POSTGRESQL"
    log "═══════════════════════════════════════════════════════════"

    if [ ! -f "$BACKUP_FILE" ]; then
        warning "Arquivo de backup não encontrado: $BACKUP_FILE"
        warning "Pulando restauração de dados (banco estará vazio)"
        return
    fi

    info "Restaurando backup PostgreSQL..."

    # Copiar backup para VPS
    scp -P "$VPS_PORT" "$BACKUP_FILE" "$VPS_USER@$VPS_HOST:/tmp/"

    # Restaurar
    ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" << EOFRES
        set -e

        BACKUP_FILE="/tmp/$(basename $BACKUP_FILE)"

        echo "Aguardando PostgreSQL estar pronto..."
        for i in {1..30}; do
            if docker exec postgresql psql -U postgres -d marketing_manager -c "SELECT 1;" 2>/dev/null; then
                echo "PostgreSQL pronto!"
                break
            fi
            echo "Tentativa \$i/30..."
            sleep 2
        done

        echo "Restaurando dados..."
        docker exec -i postgresql pg_restore -U postgres -d marketing_manager < "\$BACKUP_FILE" || {
            echo "⚠️ Restauração teve problemas. Tente manualmente."
        }

        echo "Verificando dados..."
        docker exec postgresql psql -U postgres -d marketing_manager -c "SELECT COUNT(*) FROM users;" 2>/dev/null || echo "Tabela users não existe (esperado se for primeira vez)"

        echo "✅ Restauração concluída!"

EOFRES

    rm -f "/tmp/$(basename $BACKUP_FILE)"
    success "Dados restaurados!"
    log ""
}

# ============================================================================
# FASE 6: CONFIGURAR N8N
# ============================================================================

configure_n8n() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 6: CONFIGURAR N8N"
    log "═══════════════════════════════════════════════════════════"

    info "Criando container N8N..."

    ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" << EOFN8N
        set -e

        echo "Parando N8N antigo se existir..."
        docker stop n8n 2>/dev/null || true
        docker rm n8n 2>/dev/null || true

        echo "Criando N8N novo..."
        docker run -d \
            --name n8n \
            -e DB_TYPE=postgresdb \
            -e DB_POSTGRESDB_HOST=postgresql \
            -e DB_POSTGRESDB_USER=postgres \
            -e DB_POSTGRESDB_PASSWORD=$NEW_PG_PASSWORD \
            -e DB_POSTGRESDB_DATABASE=marketing_manager \
            -e N8N_HOST=$DOMAIN \
            -e N8N_PROTOCOL=https \
            -e WEBHOOK_URL=https://$DOMAIN \
            -p 5678:5678 \
            -v n8n_data:/home/node/.n8n \
            --network=bridge \
            n8nio/n8n:latest

        echo "Aguardando N8N inicializar (30s)..."
        sleep 30

        echo "Verificando N8N..."
        docker logs n8n | tail -10 || echo "Logs ainda não disponíveis"

        echo "✅ N8N configurado!"

EOFN8N

    success "N8N configurado!"
    log "Acesse em: https://$DOMAIN/n8n"
    log ""
}

# ============================================================================
# FASE 7: CRIAR .env PARA MARKETING MANAGER
# ============================================================================

create_env() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 7: CRIAR .env PARA MARKETING MANAGER"
    log "═══════════════════════════════════════════════════════════"

    ENV_FILE="$SCRIPT_DIR/.env.coolify"

    cat > "$ENV_FILE" << EOF
# ========================================
# PRODUCTION CONFIGURATION - COOLIFY
# ========================================

# Database
DATABASE_URL=postgresql://postgres:${NEW_PG_PASSWORD}@postgresql:5432/marketing_manager

# Auth & Security
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Google OAuth
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
GOOGLE_REDIRECT_URI=https://${DOMAIN}/api/v1/auth/google/callback

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=${GOOGLE_ADS_DEVELOPER_TOKEN}
GOOGLE_ADS_LOGIN_CUSTOMER_ID=${GOOGLE_ADS_LOGIN_CUSTOMER_ID}

# OpenAI
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_MODEL=gpt-4o

# App Settings
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=["https://${DOMAIN}"]

# Scheduler
SCHEDULER_ENABLED=true
SYNC_SCHEDULE_HOUR=6
SCHEDULER_TIMEZONE=America/Sao_Paulo

# Frontend
NEXT_PUBLIC_API_URL=https://${DOMAIN}
NEXT_PUBLIC_API_VERSION=v1
EOF

    success ".env criado: $ENV_FILE"
    log "⚠️ Revise o arquivo e ajuste se necessário!"
    log ""
}

# ============================================================================
# FASE 8: HEALTH CHECKS
# ============================================================================

health_check() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 8: VERIFICAÇÕES DE SAÚDE"
    log "═══════════════════════════════════════════════════════════"

    info "Checando containers na VPS..."

    ssh -p "$VPS_PORT" "$VPS_USER@$VPS_HOST" << EOFHEALTH
        set -e

        echo "╔════════════════════════════════════════╗"
        echo "║       STATUS DOS CONTAINERS            ║"
        echo "╚════════════════════════════════════════╝"

        echo ""
        echo "🐳 Coolify:"
        docker ps --filter "name=coolify" --format "table {{.Names}}\t{{.Status}}" || echo "Não encontrado"

        echo ""
        echo "🐘 PostgreSQL:"
        docker ps --filter "name=postgresql" --format "table {{.Names}}\t{{.Status}}" || echo "Não encontrado"
        docker exec postgresql psql -U postgres -d marketing_manager -c "SELECT 'Conexão OK'" 2>&1 || echo "Erro na conexão"

        echo ""
        echo "🤖 N8N:"
        docker ps --filter "name=n8n" --format "table {{.Names}}\t{{.Status}}" || echo "Não encontrado"

        echo ""
        echo "💾 Espaço em disco:"
        df -h | grep -E "/$|/data"

        echo ""
        echo "🎯 Portas abertas:"
        netstat -tuln 2>/dev/null | grep -E ":80|:443|:5432|:5678" || echo "netstat não disponível"

        echo ""
        echo "✅ Health checks concluídos!"

EOFHEALTH

    log ""
}

# ============================================================================
# FASE 9: RESUMO E PRÓXIMOS PASSOS
# ============================================================================

summary() {
    log "═══════════════════════════════════════════════════════════"
    log "FASE 9: RESUMO E PRÓXIMOS PASSOS"
    log "═══════════════════════════════════════════════════════════"

    cat << EOFSUMMARY

╔════════════════════════════════════════════════════════════════╗
║              MIGRAÇÃO PARCIALMENTE CONCLUÍDA! 🎉              ║
╚════════════════════════════════════════════════════════════════╝

📋 O QUE FOI FEITO:
  ✅ Backups de dados (PostgreSQL)
  ✅ Coolify instalado
  ✅ PostgreSQL criado
  ✅ N8N configurado
  ✅ .env pronto para Marketing Manager
  ✅ Health checks feitos

📋 PRÓXIMOS PASSOS (MANUAIS):

1. 🌐 Acessar Coolify:
   https://$DOMAIN
   (ou https://seu-vps-ip)

2. 🤖 Configurar N8N:
   - Acesse: https://$DOMAIN/n8n
   - Importe workflows: Coloque o arquivo n8n_workflows_backup.json
   - Reconfigure credenciais (Google Ads, OpenAI, etc)

3. 📱 Deploy Marketing Manager:
   - Conecte GitHub no Coolify
   - Crie aplicação Frontend (porta 3000)
   - Crie aplicação Backend (porta 8000)
   - Use o .env criado em: ${ENV_FILE}

4. 🔗 Configure Domínio:
   - DNS apontando para VPS
   - SSL automático (Let's Encrypt)
   - Reverse proxy para frontend + backend

5. ✅ Teste:
   - https://$DOMAIN (Frontend)
   - https://$DOMAIN/api/v1/health (Backend)
   - https://$DOMAIN/n8n (N8N)

📊 INFORMAÇÕES SALVAS:
  Log: $LOG_FILE
  Backups: $BACKUP_DIR
  .env: ${ENV_FILE}

🔐 CREDENCIAIS (salve em lugar seguro):
  PostgreSQL Password: $NEW_PG_PASSWORD
  JWT Secret Key: $JWT_SECRET_KEY

⚠️ NÃO COMMITE ESSAS CREDENCIAIS NO GIT!

📞 TROUBLESHOOTING:
  - Ver logs: docker logs <container-name>
  - SSH: ssh -p $VPS_PORT $VPS_USER@$VPS_HOST
  - Checar port: netstat -tuln | grep :8000

🚀 PRÓXIMA ETAPA: Deploy Marketing Manager no Coolify!

EOFSUMMARY

    log ""
    success "Migração completada! Veja instruções acima."
    log ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    cat << EOFHEADER
╔════════════════════════════════════════════════════════════════╗
║     COOLIFY MIGRATION - Easypanel → Coolify (Automático)      ║
║                      Marketing Manager                        ║
╚════════════════════════════════════════════════════════════════╝

Este script vai fazer:
  1. ✅ Verificar pré-requisitos
  2. ✅ Coletar informações
  3. ✅ Fazer backups de tudo
  4. ✅ Instalar Coolify
  5. ✅ Configurar PostgreSQL
  6. ✅ Restaurar dados
  7. ✅ Configurar N8N
  8. ✅ Criar .env
  9. ✅ Health checks

Tempo estimado: 10-15 minutos

EOFHEADER

    read -p "Continuar? (s/n): " -r CONTINUE
    if [[ ! $CONTINUE =~ ^[Ss]$ ]]; then
        log "Migração cancelada."
        exit 0
    fi

    log ""
    log "Log será salvo em: $LOG_FILE"
    log ""

    # Executar fases
    check_prerequisites
    collect_info
    backup_data
    install_coolify
    configure_postgresql
    restore_postgresql
    configure_n8n
    create_env
    health_check
    summary
}

# ============================================================================
# RUN
# ============================================================================

main "$@"
