# Google Ads + Traffic Masters

Este projeto agora usa o `traffic-masters` como repertório local de Google Ads e converteu as rotinas mais relevantes em funcionalidades do app.

## O que foi conectado

### Squad local

- Core local: [`.aiox-core`](/Users/felipeassinato/marketing-manager/.aiox-core)
- Squad local: [`squads/traffic-masters`](/Users/felipeassinato/marketing-manager/squads/traffic-masters)

### Funcionalidades aplicadas no app

| Workflow/Task do squad | Onde entrou no app | Resultado |
|---|---|---|
| `*diagnose` | `backend/services/google_ads_command_center.py` | priorizacao de gargalos e acoes |
| `*account-audit` | `backend/services/google_ads_command_center.py` | scorecard de 8 dimensoes + wasted spend |
| `*analyze-performance` | `backend/services/google_ads_command_center.py` | leitura 80/20 + insights + plano de 7 dias |
| `*manage-budget` | `backend/services/google_ads_command_center.py` | cenarios de budget + reallocation |
| `*setup-tracking` | `backend/services/google_ads_command_center.py` | checklist de tracking + UTMs |
| `*scale-campaign` | `backend/services/google_ads_command_center.py` | campanhas elegiveis + guardrails de escala |
| Kasim Aslam | `strategy_blueprint` | framework branded / competitor / intent / remarketing |
| Search terms + keywords | `backend/services/keyword_service.py` | query intelligence e candidatos a keyword/negative |
| Recomendacoes acionaveis | `backend/routes/recommendations.py` | executar pausa ou criar automacoes |

## Entradas de uso

- API:
  - `GET /api/v1/recommendations/google-ads`
  - `POST /api/v1/recommendations/google-ads/refresh`
  - `GET /api/v1/recommendations/google-ads/automations`
  - `POST /api/v1/recommendations/google-ads/actions`
  - `GET /api/v1/campaigns/{campaign_id}/keywords`
  - `GET /api/v1/campaigns/{campaign_id}/search-terms`
- UI:
  - [`/recommendations`](/Users/felipeassinato/marketing-manager/frontend/app/recommendations/page.tsx)

## Limites atuais

- O app ainda nao le keywords, search terms, anuncios ou asset groups.
- O app agora le keywords e search terms, mas ainda nao sincroniza anuncios, asset groups ou placement reports.
- A parte de tracking usa checklist e readiness operacional; ela nao inspeciona o site automaticamente.
- O sistema trabalha melhor depois de um sync recente com historico de 30 dias.

## Proximo nivel sugerido

1. Adicionar revenue/valor de conversao para ROAS real.
2. Sincronizar anuncios, asset groups e placement reports.
3. Executar automacoes em scheduler, nao so cadastra-las.
