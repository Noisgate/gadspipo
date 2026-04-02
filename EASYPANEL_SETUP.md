# 🎛️ Setup no Easypanel - Marketing Manager

Guia passo-a-passo para deployar na sua VPS com Easypanel.

---

## 📋 Checklist Pré-Deploy

- [ ] Domínio **armattiusa.com** registrado
- [ ] Acesso SSH à VPS
- [ ] Easypanel instalado e funcionando
- [ ] PostgreSQL já configurado (via skill)
- [ ] Credenciais Google Ads atualizadas
- [ ] Google OAuth atualizado no Cloud Console

---

## 🚀 Passo 1: Preparar Arquivo .env

No seu computador local, atualize o arquivo `.env.production`:

```bash
# Gerar JWT_SECRET_KEY segura
openssl rand -hex 16
# Exemplo de output: a3f8b2c1e5d9a4f7b2e8c1d5a9f3e7b1
# Copie isso e coloque em JWT_SECRET_KEY
```

Atualize também:
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_LOGIN_CUSTOMER_ID`
- `OPENAI_API_KEY` (se quiser usar IA)

---

## 🐳 Passo 2: Build Local (Opcional)

Se quiser testar localmente antes de fazer push:

```bash
docker-compose -f docker-compose.prod.yml build
```

---

## 🔐 Passo 3: Atualizar Google Cloud Console

⚠️ **IMPORTANTE:** Precisa fazer isso antes de fazer login!

1. Vá para [Google Cloud Console](https://console.cloud.google.com)
2. Projeto: Seu projeto Google Ads
3. Menu: **APIs & Services** → **Credentials**
4. Clique na credential **OAuth 2.0 Client ID**
5. Seção: **Authorized redirect URIs**
6. Adicione:
   ```
   https://armattiusa.com/api/v1/auth/google/callback
   https://www.armattiusa.com/api/v1/auth/google/callback
   ```
7. Clique **SAVE**
8. Espere 5-10 minutos para propagação

---

## 🌐 Passo 4: SSH na VPS

```bash
ssh seu-usuario@seu-vps-ip

# Se não funcionar, tente:
ssh -i /caminho/para/chave.pem seu-usuario@seu-vps-ip
```

---

## 📁 Passo 5: Clone do Projeto

Na VPS:

```bash
# Opção 1: Git (se tiver repositório)
git clone seu-repositorio marketing-manager
cd marketing-manager

# Opção 2: SCP (copiar arquivos)
# Local:
scp -r marketing-manager seu-usuario@seu-vps-ip:/home/seu-usuario/

# VPS:
cd /home/seu-usuario/marketing-manager
```

---

## ⚙️ Passo 6: Configurar .env

Na VPS, dentro da pasta do projeto:

```bash
# Copiar template
cp .env.production .env

# Editar com seu editor
nano .env
# ou
vim .env
```

Verifique se está com os valores corretos:
- DATABASE_URL (já com credenciais certas)
- JWT_SECRET_KEY (gerada no Passo 1)
- GOOGLE_CLIENT_ID, SECRET, REDIRECT_URI
- NEXT_PUBLIC_API_URL=https://armattiusa.com

Salve: `Ctrl+X` → `Y` → `Enter`

---

## 🐳 Passo 7: Build das Imagens

Na VPS:

```bash
# Pode levar 5-10 minutos
docker-compose -f docker-compose.prod.yml build

# Verifique as imagens
docker images | grep marketing-manager
```

---

## 🚢 Passo 8: Iniciar Serviços

```bash
# Inicie em background
docker-compose -f docker-compose.prod.yml up -d

# Espere 30 segundos
sleep 30

# Verifique status
docker-compose -f docker-compose.prod.yml ps

# Saída esperada:
# marketing-manager-backend-prod  Up (healthy)
# marketing-manager-frontend-prod Up (healthy)
```

---

## 🔗 Passo 9: Configurar no Easypanel

1. Acesse seu painel Easypanel
2. Menu: **Applications** ou **Services**
3. Procure pelos containers em execução

### 9.1 Frontend (Next.js)

- Nome: `marketing-manager-frontend`
- Porta: `3000`
- Domínio: `armattiusa.com`
- SSL: ✅ Ativar (Let's Encrypt)

### 9.2 Backend (FastAPI)

- Nome: `marketing-manager-backend`
- Porta: `8000`
- Caminho: `/api/v1`
- Domínio: `armattiusa.com`
- SSL: ✅ Ativar

### 9.3 Reverse Proxy (Nginx)

O Easypanel fará isso automaticamente. Se não:

**Frontend:**
```
Location: /
Proxy: http://localhost:3000
```

**Backend:**
```
Location: /api/v1
Proxy: http://localhost:8000
```

---

## ✅ Passo 10: Verificar Deployment

### 10.1 Health Checks

```bash
# Backend
curl https://armattiusa.com/health

# Frontend
curl https://armattiusa.com/

# Deve retornar HTML/JSON, não erro 502/503
```

### 10.2 Logs

```bash
# Backend logs
docker logs -f marketing-manager-backend-prod

# Frontend logs
docker logs -f marketing-manager-frontend-prod

# Pressione Ctrl+C para sair
```

### 10.3 Testar Login

1. Abra https://armattiusa.com no browser
2. Clique em "Login com Google"
3. Autorize a aplicação
4. Deve redirecionar para dashboard
5. Verifique se conexão com banco funciona

---

## 🔄 Passo 11: Monitoramento

### 11.1 Status dos Serviços

```bash
# Verificar saúde
docker-compose -f docker-compose.prod.yml ps

# Se algum estiver Down, reinicie:
docker-compose -f docker-compose.prod.yml restart
```

### 11.2 Backup Automático do PostgreSQL

```bash
# Criar script de backup
cat > /home/seu-usuario/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump -h projeto01-postgresn8n.f5cpkl.easypanel.host \
  -U postgres \
  -d marketing_manager \
  > $BACKUP_DIR/marketing_manager_$DATE.sql

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "marketing_manager_*.sql" -mtime +7 -delete
EOF

chmod +x /home/seu-usuario/backup.sh

# Agendar via cron (2:00 AM diariamente)
crontab -e
# Adicione:
# 0 2 * * * /home/seu-usuario/backup.sh
```

---

## 🐛 Troubleshooting

### "Connection refused" no backend

```bash
# Verificar se backend está rodando
docker ps | grep backend

# Se não estiver, verifique logs
docker logs marketing-manager-backend-prod

# Comum: DATABASE_URL incorreta
```

### "502 Bad Gateway"

```bash
# Nginx não consegue conectar no backend
# Verifique se porta 8000 está aberta:
netstat -tuln | grep 8000

# Se não, backend caiu:
docker-compose -f docker-compose.prod.yml ps
```

### SSL não ativando

```bash
# Easypanel deveria fazer automaticamente
# Se não:
1. Verifique se domínio está apontando corretamente
2. Espere propagação DNS (até 24h)
3. Manualmente via Let's Encrypt:
   certbot certonly --standalone -d armattiusa.com
```

### Google OAuth dando erro

```bash
# Verifique:
1. Redirect URI está registrado no Cloud Console?
2. GOOGLE_REDIRECT_URI correto em .env?
3. Credenciais corretas (CLIENT_ID, CLIENT_SECRET)?

# Teste redirect URI:
echo "https://armattiusa.com/api/v1/auth/google/callback"
```

---

## 📊 Monitoramento Contínuo

### Easypanel Dashboard

- CPU/RAM dos containers
- Uso de disco
- Status dos serviços

### Logs

```bash
# Ver últimas 100 linhas
docker logs --tail 100 marketing-manager-backend-prod

# Ver logs em tempo real
docker logs -f marketing-manager-backend-prod
```

---

## 🔐 Segurança - Checklist Pós-Deploy

- [ ] DEBUG=false em produção
- [ ] SSL/HTTPS ativado
- [ ] CORS configurado apenas para armattiusa.com
- [ ] JWT_SECRET_KEY gerada aleatoriamente
- [ ] Senhas do banco protegidas
- [ ] Backups automáticos funcionando
- [ ] Firewall configurado (blocar portas desnecessárias)

---

## 🎉 Parabéns!

Seu sistema está rodando em produção!

**Próximos passos:**
1. Testar todos os fluxos
2. Monitorar por 24h
3. Configurar alertas
4. Backup de segurança

---

## 💬 Dúvidas?

Se tiver problemas:
1. Verifique os logs
2. Consulte troubleshooting acima
3. Verifique variáveis de ambiente
4. Teste conectividade com banco

**Boa sorte! 🚀**
