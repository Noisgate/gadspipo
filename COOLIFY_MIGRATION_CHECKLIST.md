# ✅ Coolify Migration Checklist

Acompanhamento passo-a-passo da migração Easypanel → Coolify

---

## 🔐 Fase 1: Backups de Segurança

### Local (seu computador)
- [ ] Criar pasta `/backups` para armazenar arquivos
- [ ] Criar pasta `/sql_scripts` para scripts SQL

### N8N Workflows
- [ ] Exportar workflows via API ou UI
- [ ] Salvar em `/backups/n8n_workflows_backup.json`
- [ ] Validar JSON (abrir e verificar estrutura)
- [ ] Contar quantidade de workflows exportados: ___

### PostgreSQL - Backup Completo
- [ ] SSH na VPS: `ssh seu-usuario@seu-vps-ip`
- [ ] Fazer backup dump: `pg_dump ... > postgres_backup.dump`
- [ ] Fazer backup SQL: `pg_dump ... > postgres_backup.sql`
- [ ] Copiar para local via SCP
- [ ] Tamanho do backup: ___ MB
- [ ] Verificar integridade:
  ```bash
  file postgres_backup.dump
  head -20 postgres_backup.sql
  ```

### N8N Configuration
- [ ] Backup da pasta `.n8n` (se necessário)
- [ ] Salvar em `/backups/n8n_config_backup/`
- [ ] Arquivos importantes listados: ___

### Verificação Final
- [ ] Todos os 3 backups presentes localmente
- [ ] Pasta de backups compactada (zip)
- [ ] Cópia extra em HD externo/cloud (segurança)

---

## 🔧 Fase 2: Instalar Coolify

### Verificação Prévia
- [ ] Docker instalado: `docker --version`
- [ ] Docker Compose instalado: `docker-compose --version`
- [ ] Pelo menos 2GB RAM disponível
- [ ] Espaço em disco: pelo menos 20GB

### Instalação
- [ ] Coolify instalado com sucesso
- [ ] Container rodando: `docker ps | grep coolify`
- [ ] Acesso em: `https://seu-vps-ip`
- [ ] Conta admin criada
- [ ] Login realizado com sucesso

### Configuração Inicial
- [ ] Domínio configurado: `armattiusa.com`
- [ ] SSL ativado (Let's Encrypt)
- [ ] Certificado válido: `curl -I https://seu-vps-ip`

---

## 📦 Fase 3: PostgreSQL

### Criar PostgreSQL no Coolify
- [ ] Resource criado
- [ ] Nome: `marketing-manager-db`
- [ ] Password gerada aleatoriamente
- [ ] Container rodando
- [ ] Status: **Healthy** ✅
- [ ] Porta verificada: 5432
- [ ] Host anotado: _______________

### Restaurar Dados
- [ ] Banco criado: `createdb marketing_manager`
- [ ] Restore iniciado:
  ```bash
  pg_restore -h novo-host -U postgres -d marketing_manager backup.dump
  ```
- [ ] Sem erros de permissão
- [ ] Tabelas verificadas: `\dt` (em psql)
- [ ] Quantidade de tabelas: ___
- [ ] Registros verificados: `SELECT COUNT(*) FROM users;`
- [ ] Dados intactos ✅

### Teste de Conectividade
- [ ] Conexão via psql funciona
- [ ] Credenciais confirmadas
- [ ] String de conexão anotada:
  ```
  postgresql://postgres:PASSWORD@HOST:5432/marketing_manager
  ```

---

## 🤖 Fase 4: N8N

### Criar N8N no Coolify
- [ ] Service criado
- [ ] Nome: `n8n-automation`
- [ ] Database: `marketing-manager-db` (selecionado)
- [ ] Container rodando
- [ ] Status: **Healthy** ✅
- [ ] Acesso em: `https://armattiusa.com/n8n`

### Configuração Inicial N8N
- [ ] Página de login carrega
- [ ] Conta admin criada
- [ ] Login realizado com sucesso
- [ ] Interface responsiva

### Importar Workflows
- [ ] Menu de Import acessível
- [ ] Arquivo JSON selecionado
- [ ] Import iniciado
- [ ] Workflows aparecem na lista
- [ ] Quantidade de workflows importados: ___

### Reconfigurar Credenciais
Para cada workflow importante:
- [ ] Workflow `Daily Sync`:
  - [ ] Google Ads credentials reconfigured
  - [ ] OpenAI API key atualizada
  - [ ] Status: OK

- [ ] Workflow `Automation Execution`:
  - [ ] Credenciais atualizadas
  - [ ] Status: OK

- [ ] Workflow `AI Recommendations`:
  - [ ] OpenAI API key atualizada
  - [ ] Google Ads credentials OK
  - [ ] Status: OK

- [ ] Outros workflows: _______________
  - [ ] Credenciais: OK
  - [ ] Status: OK

### Testar Workflows
- [ ] Abrir workflow
- [ ] Clique em "Test"
- [ ] Execução bem-sucedida
- [ ] Dados aparecem corretamente
- [ ] Logs sem erro

---

## 🎯 Fase 5: Marketing Manager - Frontend

### Conectar GitHub
- [ ] GitHub autorizado no Coolify
- [ ] Repositório `marketing-manager` selecionado
- [ ] Permissões corretas

### Criar Aplicação Frontend
- [ ] App criado no Coolify
- [ ] Nome: `marketing-manager-frontend`
- [ ] Source: GitHub repo selecionado
- [ ] Branch: `main` ou `dev`
- [ ] Build command OK
- [ ] Start command OK
- [ ] Port: 3000
- [ ] Domain: `armattiusa.com`
- [ ] Deploy iniciado
- [ ] Status: **Healthy** ✅

### Verificar Build
- [ ] Build logs sem erro
- [ ] Dependências instaladas
- [ ] Assets otimizados
- [ ] Tempo de build: ___ minutos

### Testar Frontend
- [ ] URL acessível: `https://armattiusa.com`
- [ ] Página carrega corretamente
- [ ] Sem erro 502/503
- [ ] CSS/JS carregados
- [ ] Responsivo no mobile
- [ ] Buttons funcionam

---

## 🔌 Fase 6: Marketing Manager - Backend

### Criar Aplicação Backend
- [ ] App criado no Coolify
- [ ] Nome: `marketing-manager-backend`
- [ ] Source: GitHub repo selecionado
- [ ] Build command OK
- [ ] Port: 8000
- [ ] Path: `/api/v1`
- [ ] Domain: `armattiusa.com`
- [ ] Deploy iniciado
- [ ] Status: **Healthy** ✅

### Variáveis de Ambiente
- [ ] DATABASE_URL: `postgresql://...`
- [ ] JWT_SECRET_KEY: gerada aleatoriamente
- [ ] GOOGLE_REDIRECT_URI: `https://armattiusa.com/api/v1/auth/google/callback`
- [ ] GOOGLE_CLIENT_ID: preenchido
- [ ] GOOGLE_CLIENT_SECRET: preenchido
- [ ] GOOGLE_ADS_DEVELOPER_TOKEN: preenchido
- [ ] OPENAI_API_KEY: preenchido (ou deixar vazio)
- [ ] DEBUG: `false`
- [ ] CORS_ORIGINS: `["https://armattiusa.com"]`

### Testar Backend
- [ ] Health check: `curl https://armattiusa.com/health`
- [ ] Resposta: `{"status":"ok"}`
- [ ] Logs sem erro
- [ ] Conexão com banco OK

---

## 🔗 Fase 7: Integração

### Testar Login Google
- [ ] Acessar `https://armattiusa.com`
- [ ] Clique em "Login com Google"
- [ ] Google aprova login
- [ ] Redireciona para callback
- [ ] Dashboard carrega
- [ ] Usuário aparece no banco de dados

### Testar API
```bash
# Health check
curl https://armattiusa.com/health

# Swagger (se ativado)
curl https://armattiusa.com/api/v1/docs
```
- [ ] Endpoints respondendo
- [ ] Banco de dados acessível
- [ ] N8N consegue chamar API

### Testar Workflows com Nova Infraestrutura
- [ ] Workflow `Daily Sync`:
  - [ ] Sincroniza campanhas
  - [ ] Dados aparecem no banco
  - [ ] Sem erro

- [ ] Workflow `AI Recommendations`:
  - [ ] Roda com sucesso
  - [ ] Recomendações geradas
  - [ ] API é chamada corretamente

---

## 🔄 Fase 8: Auto-Deploy

### Configurar GitHub Integration
- [ ] GitHub conectado no Coolify
- [ ] Repository autorizado
- [ ] Webhook criado automaticamente
- [ ] Teste: fazer um commit e push

### Testar Auto-Deploy
- [ ] Editar arquivo (ex: `README.md`)
- [ ] Commit e push: `git push`
- [ ] Coolify dispara webhook
- [ ] Build inicia automaticamente
- [ ] Deploy automático
- [ ] App atualizado em produção
- [ ] Tempo total: ___ minutos

### Verificar Logs
- [ ] Coolify → Application → Logs
- [ ] Build log completo e sem erro
- [ ] Deploy log completo
- [ ] Application health check passou

---

## 🌐 Fase 9: DNS e SSL

### Verificar DNS
- [ ] `armattiusa.com` resolvendo corretamente
- [ ] Comando: `nslookup armattiusa.com`
- [ ] Apontando para IP correto

### Verificar SSL
- [ ] HTTPS funcionando
- [ ] Certificado válido (não expirado)
- [ ] Teste: `curl -I https://armattiusa.com`
- [ ] Próxima renovação: ___
- [ ] Auto-renew ativado

### Verificar Paths
- [ ] Frontend: `https://armattiusa.com` ✅
- [ ] Backend: `https://armattiusa.com/api/v1/health` ✅
- [ ] N8N: `https://armattiusa.com/n8n` ✅

---

## ✅ Fase 10: Verificação Final

### Testes Completos
- [ ] N8N workflows executando
- [ ] Marketing Manager frontend carregando
- [ ] Marketing Manager backend respondendo
- [ ] PostgreSQL com todos os dados
- [ ] Google OAuth funcionando
- [ ] Auto-deploy funcionando

### Monitoramento
- [ ] Coolify dashboard mostrando status
- [ ] Todos os containers: **Healthy**
- [ ] Sem erros nos logs
- [ ] CPU/RAM dentro dos limites
- [ ] Espaço em disco OK

### Performance
- [ ] Frontend carrega em < 3s
- [ ] API responde em < 200ms
- [ ] Workflows executam sem delay
- [ ] Nenhuma latência anormal

---

## 🗑️ Fase 11: Limpeza (OPCIONAL)

⚠️ **APENAS APÓS TUDO FUNCIONANDO POR 24H**

- [ ] Easypanel parado: `docker stop easypanel`
- [ ] Easypanel removido: `docker rm easypanel`
- [ ] Volumes removidos (se não usar mais)
- [ ] Espaço liberado verificado
- [ ] Logs antigos deletados

---

## 📞 Status Final

| Componente | Status | Data |
|-----------|--------|------|
| Backups | ✅ Completo | _____ |
| Coolify | ✅ Instalado | _____ |
| PostgreSQL | ✅ Migrado | _____ |
| N8N | ✅ Importado | _____ |
| Frontend | ✅ Deployed | _____ |
| Backend | ✅ Deployed | _____ |
| SSL/Domínio | ✅ Configurado | _____ |
| Auto-Deploy | ✅ Funcionando | _____ |
| **MIGRAÇÃO COMPLETA** | ✅ | _____ |

---

## 🎉 Parabéns!

Você migrou com sucesso para Coolify!

Agora você tem:
- ✅ Deploy automático via GitHub
- ✅ Único painel de controle (Coolify)
- ✅ N8N + PostgreSQL + Marketing Manager integrados
- ✅ SSL automático
- ✅ Escalável para crescimento

**Próximos passos:**
1. Monitor por 24-48h
2. Testar todos os fluxos
3. Fazer backup regular
4. Configurar alertas de monitoramento

🚀 **Sucesso na migração!**
