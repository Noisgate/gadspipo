# ✅ Production Deployment Checklist

## 📝 Pré-Deploy Checklist

### Infraestrutura
- [ ] VPS com Easypanel ativo
- [ ] PostgreSQL configurado (via skill)
- [ ] Domínio **armattiusa.com** registrado e ativo
- [ ] DNS apontando para VPS
- [ ] Acesso SSH funcionando

### Aplicação
- [ ] Codebase pronto para produção
- [ ] Dockerfile otimizado
- [ ] docker-compose.prod.yml configurado
- [ ] .env.production criado com todas as variáveis
- [ ] JWT_SECRET_KEY gerada (openssl rand -hex 16)

### Google Cloud
- [ ] OAuth 2.0 credentials criadas
- [ ] Redirect URI registrado: `https://armattiusa.com/api/v1/auth/google/callback`
- [ ] GOOGLE_CLIENT_ID e SECRET confirmados
- [ ] Google Ads API credenciais (DEVELOPER_TOKEN, CUSTOMER_ID)

---

## 🚀 Deploy Checklist

### Passo 1: Preparar Ambiente Local
```bash
# ✅ Verificar estrutura
[ ] .env.production existente
[ ] docker-compose.prod.yml existente
[ ] DEPLOYMENT_GUIDE.md existente
[ ] EASYPANEL_SETUP.md existente
[ ] deploy.sh existente

# ✅ Gerar JWT
openssl rand -hex 16
[ ] JWT_SECRET_KEY copiado em .env.production
```

### Passo 2: Build Local (Opcional)
```bash
[ ] docker-compose -f docker-compose.prod.yml build --no-cache
[ ] docker images | grep marketing-manager (ambas presentes)
```

### Passo 3: Atualizar Google Cloud Console
```bash
[ ] OAuth redirect URI registrado
[ ] GOOGLE_REDIRECT_URI em .env.production = https://armattiusa.com/api/v1/auth/google/callback
[ ] Esperar 5-10 minutos propagação
```

### Passo 4: SSH na VPS
```bash
[ ] SSH funcionando: ssh seu-usuario@seu-vps-ip
[ ] Diretório /home/seu-usuario pronto
[ ] Permissões corretas para deploy
```

### Passo 5: Clone do Projeto
```bash
[ ] Projeto clonado via git ou SCP
[ ] Pasta marketing-manager existente
[ ] Todos os arquivos copiados
```

### Passo 6: Configurar .env
```bash
[ ] .env.production copiado como .env
[ ] DATABASE_URL verificada
[ ] JWT_SECRET_KEY preenchida
[ ] Google credentials atualizadas
[ ] NEXT_PUBLIC_API_URL = https://armattiusa.com
```

### Passo 7: Build na VPS
```bash
[ ] docker-compose -f docker-compose.prod.yml build (sem erro)
[ ] docker images mostra ambas imagens
[ ] Sem aviso de segurança
```

### Passo 8: Iniciar Serviços
```bash
[ ] docker-compose -f docker-compose.prod.yml up -d (sem erro)
[ ] Esperar 30 segundos
[ ] docker-compose -f docker-compose.prod.yml ps (ambos UP e healthy)
```

### Passo 9: Configurar Easypanel
```bash
[ ] Frontend mapeado para porta 3000, domínio armattiusa.com
[ ] Backend mapeado para porta 8000, path /api/v1
[ ] SSL ativado (Let's Encrypt)
[ ] Reverse proxy configurado
```

---

## ✅ Pós-Deploy Checklist

### Health Checks
```bash
[ ] curl https://armattiusa.com/health → {"status":"ok"}
[ ] curl https://armattiusa.com/ → HTML (não 502/503)
[ ] SSL válido (não aviso de certificado)
```

### Testes de Funcionalidade
```bash
[ ] Acessar https://armattiusa.com no browser
[ ] Página de login carrega corretamente
[ ] Botão "Login com Google" visível
[ ] Clica em login e abre Google
[ ] Autoriza a app
[ ] Redireciona para dashboard (não erro)
[ ] Dashboard carrega (não mensagens de erro)
```

### Banco de Dados
```bash
[ ] Conexão com PostgreSQL funciona
[ ] Dados de usuário salvos
[ ] Sincronização de campanhas funciona
```

### Logs
```bash
[ ] Backend logs sem erro (docker logs -f marketing-manager-backend-prod)
[ ] Frontend logs sem erro (docker logs -f marketing-manager-frontend-prod)
[ ] Sem message repeat infinito
```

### SSL/HTTPS
```bash
[ ] URL em HTTPS
[ ] Certificado válido (não expired)
[ ] Redirecionamento HTTP → HTTPS
```

---

## 🔐 Segurança Pós-Deploy

### Variáveis de Ambiente
- [ ] DEBUG=false em produção
- [ ] CORS_ORIGINS configurado apenas para armattiusa.com
- [ ] JWT_SECRET_KEY gerada aleatoriamente
- [ ] Senhas do banco não em .env exposto
- [ ] OPENAI_API_KEY protegida (se usar)

### Dados Sensíveis
- [ ] Credenciais não commitadas em git
- [ ] .env adicionado a .gitignore
- [ ] Backups de senha do banco seguros
- [ ] Google Ads credentials seguras

### Network
- [ ] Firewall bloqueando portas desnecessárias
- [ ] SSH com key-based auth (não password)
- [ ] Acesso ao banco restrito ao backend

---

## 🛠️ Configuração de Monitoramento

### Easypanel Dashboard
- [ ] Acessar dashboard do Easypanel
- [ ] Verificar CPU/RAM dos containers
- [ ] Verificar uso de disco
- [ ] Configurar alertas (CPU >80%, Disk >90%)

### Logs Contínuos
```bash
[ ] Backend: docker logs -f marketing-manager-backend-prod
[ ] Frontend: docker logs -f marketing-manager-frontend-prod
[ ] Sistema: Monitorar via Easypanel
```

### Backups
- [ ] Script de backup criado
- [ ] Cron job agendado (2:00 AM)
- [ ] Primeiro backup executado com sucesso
- [ ] Backup restore testado

---

## 🚨 Troubleshooting Rápido

Se algo der errado:

### Backend Down
```bash
docker-compose -f docker-compose.prod.yml logs marketing-manager-backend-prod
docker-compose -f docker-compose.prod.yml restart backend
```

### Frontend Down
```bash
docker-compose -f docker-compose.prod.yml logs marketing-manager-frontend-prod
docker-compose -f docker-compose.prod.yml restart frontend
```

### SSL Problema
```bash
# Let's Encrypt via Certbot
certbot certonly --standalone -d armattiusa.com

# Ou via Easypanel (painel gráfico)
```

### Google OAuth Erro
```bash
# Verificar logs do backend para erro exato
docker logs marketing-manager-backend-prod | grep -i "oauth\|google"

# Checklist:
1. Redirect URI registrado no Cloud Console?
2. Credenciais corretas em .env?
3. Domínio propagou no DNS?
```

---

## 📞 Próximos Passos

1. ✅ Executar este checklist completamente
2. ✅ Testar todos os fluxos por 24h
3. ✅ Monitorar logs e performance
4. ✅ Configurar alertas de monitoramento
5. ✅ Fazer primeiro backup manual
6. ✅ Documentar qualquer customização
7. ✅ Treinar equipe no sistema

---

## 📊 Status de Deployment

| Componente | Status | Data | Responsável |
|-----------|--------|------|-------------|
| VPS Setup | ⏳ Pendente | | |
| Docker Deploy | ⏳ Pendente | | |
| SSL/HTTPS | ⏳ Pendente | | |
| Google OAuth | ⏳ Pendente | | |
| Database | ✅ Configurado | | |
| Backups | ⏳ Pendente | | |
| Monitoramento | ⏳ Pendente | | |
| Go Live | ⏳ Pendente | | |

---

## 📝 Notas

```
[Espaço para anotações sobre seu deployment específico]

Domínio: armattiusa.com
Database: projeto01-postgresn8n.f5cpkl.easypanel.host:25432
Backend: localhost:8000
Frontend: localhost:3000

Data de Deploy: ___/___/_____
Responsável: _______________
```

---

**Versão:** 1.0
**Última atualização:** 2026-03-24
**Status:** ✅ Pronto para deployment

🚀 **Você está pronto para ir para produção!**
