# AGENTS.md - Marketing Manager

Este repositório agora usa uma base local do AIOX em [`.aiox-core`](/Users/felipeassinato/marketing-manager/.aiox-core) e mantém squads locais em [`squads/`](/Users/felipeassinato/marketing-manager/squads).

## Escopo principal

- App principal:
  - Backend FastAPI em [`backend/`](/Users/felipeassinato/marketing-manager/backend)
  - Frontend Next.js em [`frontend/`](/Users/felipeassinato/marketing-manager/frontend)
- Squad local de mídia paga:
  - [`squads/traffic-masters`](/Users/felipeassinato/marketing-manager/squads/traffic-masters)

## Google Ads

O projeto incorporou o repertório de Google Ads do `traffic-masters` em duas camadas:

1. Conteúdo de squad local para consulta e operação assistida.
2. Features reais no app via command center em:
   - Backend: [`backend/routes/recommendations.py`](/Users/felipeassinato/marketing-manager/backend/routes/recommendations.py)
   - Serviço: [`backend/services/google_ads_command_center.py`](/Users/felipeassinato/marketing-manager/backend/services/google_ads_command_center.py)
   - Frontend: [`frontend/app/recommendations/page.tsx`](/Users/felipeassinato/marketing-manager/frontend/app/recommendations/page.tsx)

## Fluxo recomendado para agentes

1. Ler os dados atuais de campanhas e métricas antes de sugerir mudanças.
2. Priorizar Google Ads quando o pedido envolver auditoria, tracking, budget, performance ou escala.
3. Consultar o squad local `traffic-masters` para linguagem, frameworks e checklists.
4. Traduzir o conhecimento do squad em saídas concretas dentro do app, evitando respostas genéricas.

## Referências úteis

- Mapa da integração: [`docs/google-ads-traffic-masters.md`](/Users/felipeassinato/marketing-manager/docs/google-ads-traffic-masters.md)
- Squad original clonado para referência: [`xquads-squads/traffic-masters`](/Users/felipeassinato/marketing-manager/xquads-squads/traffic-masters)
- Core clonado para referência: [`aios-core`](/Users/felipeassinato/marketing-manager/aios-core)
