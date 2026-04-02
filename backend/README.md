# Backend - Marketing Manager

FastAPI backend para gerenciamento de campanhas Google Ads.

## Setup

```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # ou: venv\Scripts\activate (Windows)

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Editar .env com suas credenciais

# Database setup
alembic upgrade head

# Run development server
python main.py
# ou: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Estrutura de Pastas

```
backend/
├── auth/                # OAuth2, JWT, autenticação
├── integrations/        # Google Ads API, OpenAI
├── services/            # Business logic
├── models/              # SQLAlchemy ORM + Pydantic schemas
├── routes/              # API endpoints
├── tasks/               # Scheduler, background jobs
├── database/            # Connection pool, migrations
├── config.py            # Configurações
├── main.py              # FastAPI app entry point
└── requirements.txt     # Dependencies
```

## API Endpoints

### Auth
- `POST /api/v1/auth/google-callback` - OAuth2 callback
- `POST /api/v1/auth/refresh` - Refresh JWT token

### Accounts
- `GET /api/v1/accounts` - List user's Google Ads accounts
- `POST /api/v1/accounts/connect` - Start OAuth flow
- `DELETE /api/v1/accounts/{account_id}` - Disconnect account

### Campaigns
- `GET /api/v1/campaigns` - List campaigns
- `GET /api/v1/campaigns/{campaign_id}` - Campaign detail
- `GET /api/v1/campaigns/performance` - Analytics dashboard

### Sync
- `POST /api/v1/sync/{account_id}` - Manual sync
- `GET /api/v1/sync/status/{account_id}` - Sync status

## Development

### Run tests
```bash
pytest
```

### Code formatting
```bash
black .
flake8 .
```

### Database migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

## Environment Variables

Ver `.env.example` para lista completa.

## Troubleshooting

**ModuleNotFoundError:** Certifique-se que está rodando a partir do diretório `backend/`
**Database connection error:** Verifique `DATABASE_URL` no `.env`
**Google Ads API error:** Verifique `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET`
