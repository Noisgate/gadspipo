# 🔧 Comandos Úteis - Marketing Manager + Coolify

## 🌐 Acesso Remoto

### Conectar à VPS
```bash
# Via SSH
sshpass -p 'Fosnight1205@@' ssh root@147.93.47.236

# Ou com chave SSH (quando configurado)
ssh -i ~/.ssh/id_rsa root@147.93.47.236
```

### Executar Comando Remoto
```bash
sshpass -p 'Fosnight1205@@' ssh root@147.93.47.236 "comando aqui"
```

---

## 🐳 Docker Commands

### Ver Todos os Containers
```bash
docker ps -a
```

### Ver Apenas Containers Rodando
```bash
docker ps
```

### Logs de um Container
```bash
# Últimas 100 linhas
docker logs container_name

# Seguindo em tempo real
docker logs -f container_name

# Últimas 30 linhas
docker logs --tail 30 container_name
```

### Reiniciar Serviços
```bash
# Coolify completo
cd /root && docker compose -f docker-compose.coolify.yml restart

# Serviço específico
docker restart coolify
docker restart coolify-db

# Marketing Manager
cd /root/marketing-manager && docker compose restart
```

### Parar/Iniciar Containers
```bash
# Parar
docker stop container_name

# Iniciar
docker start container_name

# Parar todos
docker stop $(docker ps -q)
```

### Remover Container
```bash
docker rm container_name

# Forçar (se rodando)
docker rm -f container_name
```

---

## 🐳 Docker Compose

### Subir Containers
```bash
docker compose -f docker-compose.yml up -d
```

### Parar Containers
```bash
docker compose -f docker-compose.yml down
```

### Ver Status
```bash
docker compose -f docker-compose.yml ps
```

### Rebuild Images
```bash
docker compose -f docker-compose.yml up --build -d
```

---

## 💾 PostgreSQL

### Conectar ao PostgreSQL Coolify
```bash
docker exec -it coolify-db psql -U postgres -d coolify
```

### Backup PostgreSQL
```bash
docker exec coolify-db pg_dump -U postgres > backup-$(date +%Y%m%d-%H%M%S).sql
```

### Restaurar PostgreSQL
```bash
cat backup.sql | docker exec -i coolify-db psql -U postgres -d coolify
```

### Ver Databases
```bash
docker exec -it coolify-db psql -U postgres -l
```

### Ver Tabelas
```bash
docker exec -it coolify-db psql -U postgres -d coolify -c "\dt"
```

---

## 🔍 Verificações de Saúde

### Coolify Status
```bash
# Web
curl -I http://localhost:3000

# Health check
docker ps --filter "name=coolify" --format "{{.Status}}"
```

### PostgreSQL Status
```bash
# Verificar se está respondendo
docker exec coolify-db pg_isready -U postgres

# Conectar e testar
docker exec -it coolify-db psql -U postgres -c "SELECT version();"
```

### N8N Status
```bash
curl http://localhost:5678
```

### Espaço em Disco
```bash
df -h
docker system df
```

### Uso de Memória
```bash
docker stats

# Ou
free -h
```

---

## 🔐 Arquivos Importantes

### Localização
```
/root/
├── .env (Coolify)
├── marketing-manager/.env (Marketing Manager)
├── backups/
├── coolify-data/
└── coolify-db-data/
```

### Ver Arquivo
```bash
cat /root/marketing-manager/.env
```

### Editar Arquivo
```bash
nano /root/marketing-manager/.env
vim /root/marketing-manager/.env
```

### Fazer Backup de Arquivo
```bash
cp /root/.env /root/.env.backup-$(date +%Y%m%d)
```

---

## 📊 Monitoramento

### Ver Processos do Docker
```bash
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
```

### Ver Network
```bash
docker network ls
docker inspect nome_da_rede
```

### Ver Volumes
```bash
docker volume ls
docker inspect volume_name
```

### Monitor em Tempo Real
```bash
# Atualizar a cada 2 segundos
watch -n 2 docker ps

# Uso de recursos
watch -n 2 docker stats
```

---

## 🚀 Deploy & Updates

### Rebuild Frontend
```bash
cd /root/marketing-manager
docker build -t marketing-manager-frontend:latest -f frontend/Dockerfile .
```

### Rebuild Backend
```bash
cd /root/marketing-manager
docker build -t marketing-manager-backend:latest -f backend/Dockerfile .
```

### Atualizar Código (Git)
```bash
cd /root/marketing-manager
git pull origin main
docker compose up --build -d
```

---

## 📝 Logs & Debugging

### Combinar Logs de Múltiplos Containers
```bash
docker compose logs -f
```

### Procurar por Erro nos Logs
```bash
docker logs container_name 2>&1 | grep -i error
```

### Último erro
```bash
docker logs container_name 2>&1 | tail -50
```

### Log de Tempo Real (Grep)
```bash
docker logs -f container_name | grep "palavra-chave"
```

---

## 🌐 Network & Conectividade

### Testar Conectividade
```bash
# Dentro de container
docker exec container_name ping google.com

# Entre containers
docker exec container_name ping outro_container
```

### DNS
```bash
# Testar DNS
docker exec container_name nslookup google.com
docker exec container_name getent hosts outro_container
```

### Portas
```bash
# Ver portas em uso
netstat -tuln | grep LISTEN

# Ou
ss -tuln | grep LISTEN

# Porta específica
lsof -i :3000
```

---

## 📤 Transferência de Arquivos

### SCP - Enviar arquivo para VPS
```bash
scp -P 22 arquivo.txt root@147.93.47.236:/root/
```

### SCP - Baixar arquivo da VPS
```bash
scp -P 22 root@147.93.47.236:/root/arquivo.txt .
```

### Com sshpass
```bash
sshpass -p 'Fosnight1205@@' scp arquivo.txt root@147.93.47.236:/root/
```

---

## 🔄 Workflows Comuns

### Deploy Novo Código
```bash
cd /root/marketing-manager

# Atualizar código
git pull origin main

# Rebuild e restart
docker compose up --build -d

# Verificar
docker compose logs -f
```

### Criar Backup Completo
```bash
# PostgreSQL
docker exec coolify-db pg_dump -U postgres > /root/backups/backup-$(date +%Y%m%d-%H%M%S).sql

# Docker volumes
docker run --rm -v coolify-data:/data -v /root/backups:/backup busybox tar czf /backup/coolify-$(date +%Y%m%d-%H%M%S).tar.gz -C / data
```

### Restaurar de Backup
```bash
# PostgreSQL
cat /root/backups/backup.sql | docker exec -i coolify-db psql -U postgres -d coolify

# Volumes
docker run --rm -v coolify-data:/data -v /root/backups:/backup busybox tar xzf /backup/coolify.tar.gz -C /
```

### Aumentar Limite de Arquivo Aberto
```bash
# Ver limite atual
ulimit -n

# Aumentar (temporário)
ulimit -n 65536

# Permanente (adicionar ao /etc/security/limits.conf)
* soft nofile 65536
* hard nofile 65536
```

---

## ⚠️ Emergência

### Parar Tudo
```bash
docker stop $(docker ps -q)
```

### Remover Containers Parados
```bash
docker container prune -f
```

### Limpar Sistema
```bash
# Remove images não usadas
docker image prune -f

# Remove volumes não usados
docker volume prune -f

# Remove redes não usadas
docker network prune -f

# Limpar tudo
docker system prune -f
```

### Reiniciar Docker Daemon
```bash
# Parar
sudo systemctl stop docker

# Limpar
docker system prune -f

# Iniciar
sudo systemctl start docker

# Verificar
docker ps
```

---

## 🎯 Quick Reference

### URLs Importantes
```
Coolify: http://147.93.47.236
N8N: http://147.93.47.236:5678
Marketing Manager Frontend: http://147.93.47.236:3000
Marketing Manager API: http://147.93.47.236:8000
API Docs: http://147.93.47.236:8000/api/v1/docs
```

### Conexões Diretas
```
PostgreSQL Coolify: localhost:5432 (senha: postgres)
PostgreSQL N8N: localhost:25432
Redis N8N: localhost:6379
```

### SSH
```
Host: 147.93.47.236
Usuário: root
Porta: 22
Autenticação: Senha (Fosnight1205@@)
```

---

## 📚 Mais Informações

- [Docker Docs](https://docs.docker.com)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Coolify Docs](https://coolify.io/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs)

---

**Última atualização:** 24 de Março, 2026

