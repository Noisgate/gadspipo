#!/bin/bash
set -e

echo "🚀 Marketing Manager - Quick Start"
echo "=================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado"
    exit 1
fi

echo "✅ Docker encontrado"

# Setup backend .env
if [ ! -f backend/.env ]; then
    echo "📝 Criando backend/.env..."
    cp backend/.env.example backend/.env
    echo "⚠️  Edit backend/.env com suas credenciais!"
fi

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for PostgreSQL
echo "⏳ Aguardando PostgreSQL..."
sleep 10

# Check health
echo "✅ Services started!"
echo ""
echo "📊 PostgreSQL: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo "🔵 Backend: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "✨ Next steps:"
echo "1. Edit backend/.env com suas credenciais Google Ads"
echo "2. Teste o health check: curl http://localhost:8000/health"
echo "3. Create frontend: npm create next-app@latest frontend"
echo ""
