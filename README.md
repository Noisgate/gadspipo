# Marketing Manager

Google Ads operating system built with **FastAPI + Next.js + PostgreSQL**, enriched with the **xquads / Traffic Masters** playbooks and adapted for a non-specialist operator workflow:

**diagnose -> discuss -> refine -> approve -> execute by API**

This README is both:

- a project overview
- a handoff document to continue work in **Claude Code with Antigravity**

---

## What This Project Is

The goal is not to be just another dashboard with raw Google Ads metrics.

The product is evolving into a **guided Google Ads copilot** that:

1. reads the account and campaigns
2. explains the situation in plain language
3. proposes fixes and improvements
4. lets the user discuss and refine those ideas
5. only executes changes after approval

The key product principle is:

> The app should think like a media team, but explain itself like a patient operator for someone who is not a Google Ads specialist.

---

## Current Product Model

Today the app has four major layers:

### 1. Authentication and account connection

- Google OAuth login
- user creation / reuse
- Google Ads account discovery
- JWT session for the frontend

### 2. Campaign data platform

- connected Google Ads accounts
- campaigns
- campaign metrics
- keywords
- search terms

### 3. Decision engine

- command center inspired by `traffic-masters`
- campaign-level diagnosis
- proposal workshop
- investigation workflow
- API-safe execution for supported actions

### 4. Campaign creation assistant

- campaign studio for new campaigns
- free-form idea diagnosis
- material upload and classification
- structured launch plan generation

---

## What Was Implemented So Far

### Google OAuth and session flow

- Backend OAuth flow in `backend/auth/oauth.py` and `backend/routes/auth.py`
- Frontend login completion in `frontend/app/login/page.tsx`
- cookie-based auth state in `frontend/contexts/auth.ts`
- callback returns the JWT back to the frontend login flow

### Google Ads data sync

- account discovery and reconnect flow
- campaign sync and persistence
- keyword sync
- search term sync
- 30-day metric snapshots

### xquads / Traffic Masters integration

The project cloned and mapped the `traffic-masters` squad into real product features:

- `*diagnose`
- `*account-audit`
- `*analyze-performance`
- `*manage-budget`
- `*setup-tracking`
- `*scale-campaign`
- Kasim Aslam search structure principles

Main implementation:

- `backend/services/google_ads_command_center.py`
- `backend/routes/recommendations.py`
- `frontend/app/recommendations/page.tsx`

### Investigation and repair workflow

This was a major product shift.

Instead of "click and pray", the app now supports:

1. investigate a campaign
2. persist diagnosis + repair plan
3. approve the plan
4. execute only API-safe actions
5. sync again and update diagnosis

Main implementation:

- `backend/services/campaign_investigation_service.py`
- `backend/routes/campaigns.py`
- `frontend/app/campaigns/[campaignId]/page.tsx`

### Proposal workshop

Actions are no longer meant to run blindly.

The current proposal flow is:

1. open proposal
2. read rationale and risks
3. refine with notes
4. approve for execution or automation

Main implementation:

- `backend/services/recommendation_workshop_service.py`
- `backend/routes/recommendations.py`
- `frontend/components/recommendations/ProposalActionCard.tsx`

### Campaign Studio

The app already has the foundation of a guided "new campaign" experience:

- free-form campaign idea diagnosis
- upload and classification of materials
- structured campaign plan generation

Main implementation:

- `backend/services/campaign_studio_service.py`
- `backend/integrations/openai_client.py`
- `frontend/app/campaigns/new/page.tsx`

### UX simplification for non-experts

The frontend was reworked to be less technical and more guided:

- dashboard now explains what to look at first
- campaigns page became a priority queue instead of a raw metrics table
- recommendations page became a decision center
- campaign detail page explains the situation in plain language before exposing technical detail

Main implementation:

- `frontend/app/dashboard/page.tsx`
- `frontend/app/campaigns/page.tsx`
- `frontend/app/recommendations/page.tsx`
- `frontend/app/campaigns/[campaignId]/page.tsx`
- `frontend/components/dashboard/CampaignTable.tsx`
- `frontend/components/dashboard/Header.tsx`

---

## Architecture

## Backend

- Framework: FastAPI
- DB: PostgreSQL via SQLAlchemy + psycopg
- Auth: Google OAuth + JWT
- Scheduler: APScheduler
- External APIs:
  - Google OAuth
  - Google Ads API
  - OpenAI API

Key backend folders:

```text
backend/
├── auth/
├── database/
├── integrations/
├── migrations/
├── models/
├── routes/
├── services/
├── tasks/
├── config.py
└── main.py
```

Core backend services:

- `campaign_service.py`
  - syncs campaigns and metrics
- `keyword_service.py`
  - syncs keywords and search terms
- `google_ads_command_center.py`
  - turns account data into strategic guidance
- `recommendation_workshop_service.py`
  - refines action proposals before execution
- `campaign_investigation_service.py`
  - creates investigation + repair workflows
- `campaign_studio_service.py`
  - builds new campaign plans from briefs and uploads

## Frontend

- Framework: Next.js 14 App Router
- State/data: SWR + Zustand
- HTTP: Axios
- Styling: Tailwind CSS
- Notifications: Sonner

Key frontend folders:

```text
frontend/
├── app/
├── components/
├── contexts/
├── hooks/
├── lib/
└── types/
```

Core frontend screens:

- `/login`
- `/dashboard`
- `/campaigns`
- `/campaigns/[campaignId]`
- `/campaigns/new`
- `/recommendations`

---

## API Surface

## Auth

- `GET /api/v1/auth/google`
- `GET /api/v1/auth/google/callback`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`

## Accounts

- `GET /api/v1/accounts`
- `POST /api/v1/accounts/discover`
- `DELETE /api/v1/accounts/{account_id}`

## Campaigns

- `GET /api/v1/campaigns`
- `GET /api/v1/campaigns/{campaign_id}`
- `GET /api/v1/campaigns/{campaign_id}/keywords`
- `GET /api/v1/campaigns/{campaign_id}/search-terms`
- `POST /api/v1/campaigns/sync/{account_id}`
- `GET /api/v1/campaigns/performance/dashboard`

## Campaign investigations

- `GET /api/v1/campaigns/{campaign_id}/investigation/latest`
- `POST /api/v1/campaigns/{campaign_id}/investigate`
- `POST /api/v1/campaigns/{campaign_id}/investigations/{investigation_id}/approve`
- `POST /api/v1/campaigns/{campaign_id}/investigations/{investigation_id}/steps/{step_id}`
- `POST /api/v1/campaigns/{campaign_id}/investigations/{investigation_id}/execute`

## Campaign Studio

- `POST /api/v1/campaigns/studio/diagnose`
- `POST /api/v1/campaigns/studio/materials`
- `POST /api/v1/campaigns/studio/analyze`

## Recommendations / command center

- `GET /api/v1/recommendations/google-ads`
- `POST /api/v1/recommendations/google-ads/refresh`
- `GET /api/v1/recommendations/google-ads/automations`
- `POST /api/v1/recommendations/google-ads/actions`
- `POST /api/v1/recommendations/google-ads/proposal`

---

## xquads / Traffic Masters Mapping

The local squad lives here:

- `.aiox-core/`
- `squads/traffic-masters/`
- `xquads-squads/traffic-masters/` as original reference

Reference docs:

- `AGENTS.md`
- `docs/google-ads-traffic-masters.md`

Current mapping:

| xquads source | App implementation | Status |
| --- | --- | --- |
| `*diagnose` | command center + campaign diagnosis | implemented |
| `*account-audit` | account audit scorecard | implemented |
| `*analyze-performance` | performance analysis + plan | implemented |
| `*manage-budget` | reallocation and budget scenarios | implemented |
| `*setup-tracking` | tracking readiness + checklist | implemented |
| `*scale-campaign` | scaling plan | implemented |
| Kasim structure principles | strategy blueprint | implemented |
| campaign launch workflow | campaign studio foundations | partial |
| creative production workflow | campaign studio + AI assist | partial |
| full autonomous repair strategy | investigation workflow | partial |

Important product reality:

> xquads is already influencing the app heavily, but not every squad capability has been converted into a full production feature yet.

---

## Current UX Philosophy

The frontend is now intentionally moving away from "ad manager jargon first".

The desired UX language is:

- "what is happening"
- "why this is probably happening"
- "what the app suggests now"
- "what the app can do by API"
- "what still depends on you"

This is especially important because the product owner is **not a Google Ads specialist**.

So the app should avoid making the user translate:

- CTR
- CPA
- readiness
- query intelligence
- bidding logic

before they can even decide what to do.

---

## Local Runbook

## Backend

From the project root:

```bash
cd backend
venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Frontend

```bash
cd frontend
PATH="/opt/homebrew/opt/node@22/bin:$PATH" npm run build
PATH="/opt/homebrew/opt/node@22/bin:$PATH" npm run start -- --hostname 127.0.0.1 --port 3000
```

Useful URLs:

- `http://127.0.0.1:3000/login`
- `http://127.0.0.1:3000/dashboard`
- `http://127.0.0.1:3000/campaigns`
- `http://127.0.0.1:3000/campaigns/new`
- `http://127.0.0.1:3000/recommendations`

> [!IMPORTANT]
> Use direct routes like `/login`, `/campaigns` and `/recommendations` during troubleshooting. The root route was simplified to redirect to login, but the direct URLs are still the safest entry points while iterating.

---

## OAuth / Google Login Notes

Google login was one of the most sensitive parts of the build.

Current expected local flow:

- frontend host: `localhost:3000` or `127.0.0.1:3000`
- backend API: `localhost:8000` or `127.0.0.1:8000`
- current redirect strategy should be checked in `backend/.env`

At the moment, the most important rule is:

> The OAuth client configured in Google Cloud must match the exact `GOOGLE_CLIENT_ID` and `GOOGLE_REDIRECT_URI` from the backend local `.env`.

If login breaks with `redirect_uri_mismatch`, verify:

1. the correct OAuth client is being edited in Google Cloud
2. the exact redirect URI from `backend/.env` exists in that client
3. frontend and backend are not mixing `localhost` and `127.0.0.1` unexpectedly

Do not trust memory here. Always compare against:

- `backend/.env`
- `backend/auth/oauth.py`
- `backend/routes/auth.py`

---

## Investigation and API Execution Model

The investigation workflow is designed to be safer than "execute immediately".

Current flow:

1. user asks the app to investigate a campaign
2. app syncs data when possible
3. app persists diagnosis, blockers, evidence and repair plan
4. user approves the investigation
5. app executes only actions marked as `approve_and_execute`
6. app syncs again and refreshes the diagnosis

Important limitation:

Not every problem can be fixed by the Google Ads API.

The app can currently act by API for supported cases such as:

- pause campaign
- budget update
- negative keyword / negative term style actions
- add keyword from search term

The app cannot magically fix by API:

- landing page problems
- missing creatives outside the current automated scope
- tracking issues outside Google Ads
- policy/compliance blockers that require manual changes

This is why some investigations may end with:

- no API-safe actions
- plan-only guidance
- discussion-required proposals

That is expected behavior when the root problem is outside the safe automation envelope.

Recent improvement:

- investigation candidate actions are now prioritized to include API-safe actions first, when they exist
- the UI now clearly shows how many corrections are API-safe before the user clicks execute

---

## Campaign Studio Status

The new campaign flow already exists, but it is not finished end to end.

What already exists:

- free-form campaign idea diagnosis
- structured brief generation
- upload and classification of materials
- campaign launch plan
- AI-assisted enrichment when `OPENAI_API_KEY` exists

What is still missing or partial:

- durable draft persistence
- full publishing to Google Ads from the studio
- richer creative generation workflow
- stronger asset and document collection flow
- a more conversational "wizard" UX

This is one of the best next bets for product value.

---

## Known Issues and Current Limits

## Product / feature limits

- Not every xquads feature has been converted into production UI yet.
- The app is much stronger for existing campaign diagnosis than for brand-new campaign publishing.
- Some recommendations are still heuristic because campaign data may be thin.
- Conversion value / real ROAS are still incomplete in parts of the stack.
- Ads, asset groups, placements and deeper creative diagnostics are still not fully synced.

## UX limits

- The UI is much clearer now, but some screens still expose internal concepts more than ideal.
- Campaign Studio needs another simplification pass for non-experts.
- Some proposal and investigation flows can still be made more conversational.

## Operational limits

- OAuth local setup is still easy to break if the wrong Google Cloud client is edited.
- Local frontend and backend processes sometimes need manual restart during iterative work.
- Some shell/sandbox combinations can make local health checks appear inconsistent even when the process is alive.

> [!WARNING]
> During local development, if behavior looks inconsistent, verify both live processes first:
> - backend on port `8000`
> - frontend on port `3000`
>
> Then test direct URLs instead of relying on browser state.

---

## What Was Recently Validated

The following checks were repeatedly used during development:

```bash
backend/venv/bin/python -m py_compile backend/services/campaign_investigation_service.py
backend/venv/bin/python -c "import sys; sys.path.insert(0, 'backend'); import main"
cd frontend && PATH="/opt/homebrew/opt/node@22/bin:$PATH" npm run type-check
cd frontend && PATH="/opt/homebrew/opt/node@22/bin:$PATH" npm run build
curl http://127.0.0.1:8000/health
curl -I http://127.0.0.1:3000/campaigns
```

---

## Recommended Next Priorities

If work continues from here, the highest-value sequence is:

1. **Finish the beginner-friendly Campaign Studio**
   - better conversational intake
   - better materials UX
   - draft persistence
   - publish pipeline

2. **Increase the set of API-safe repairs**
   - convert more investigation outcomes into executable actions
   - better safe/unsafe classification
   - stronger post-execution verification

3. **Deepen Google Ads sync**
   - ads
   - asset groups
   - placement data
   - conversion value / ROAS
   - stronger diagnosis signals

4. **Tighten the product language**
   - remove remaining expert jargon from core flows
   - turn more pages into guided decision flows

5. **Stabilize local OAuth and runtime**
   - remove host ambiguity
   - document exact local OAuth setup
   - reduce process flakiness

---

## Claude Code / Antigravity Handoff

If continuing in Claude Code with Antigravity, start here:

### Read first

1. `README.md`
2. `AGENTS.md`
3. `docs/google-ads-traffic-masters.md`

### Then inspect

- `backend/main.py`
- `backend/routes/auth.py`
- `backend/routes/campaigns.py`
- `backend/routes/recommendations.py`
- `backend/services/google_ads_command_center.py`
- `backend/services/campaign_investigation_service.py`
- `backend/services/campaign_studio_service.py`
- `frontend/app/dashboard/page.tsx`
- `frontend/app/campaigns/page.tsx`
- `frontend/app/campaigns/[campaignId]/page.tsx`
- `frontend/app/recommendations/page.tsx`
- `frontend/app/campaigns/new/page.tsx`
- `frontend/components/recommendations/ProposalActionCard.tsx`

### Product truths to preserve

- The user is not a Google Ads expert.
- The app should explain before it executes.
- Investigation is not the same thing as proposal refinement.
- Safe API execution must stay explicit and auditable.
- xquads should guide the logic, but the UI must stay human-readable.

### Good prompt to continue work

```text
Read README.md, AGENTS.md and docs/google-ads-traffic-masters.md first.
Treat the app as a guided Google Ads copilot for a non-expert operator.
Preserve the flow diagnose -> discuss -> refine -> approve -> execute by API.
Before changing automation behavior, verify whether the problem is actually API-fixable.
Prefer improving clarity and trust over adding more raw metrics.
```

---

## Repository Context

Useful supporting files already in the repository:

- `AGENTS.md`
- `docs/google-ads-traffic-masters.md`
- `COMPLETE_STACK.md`
- `DEPLOYMENT_GUIDE.md`
- `PRODUCTION_CHECKLIST.md`
- `SETUP_STATUS.md`
- `USEFUL_COMMANDS.md`

Some of these are operational or historical and may lag behind the newest product direction. When in doubt, prefer:

1. source code
2. this README
3. `AGENTS.md`
4. the xquads integration doc

---

## Summary

This repository is no longer just a Google Ads dashboard.

It already has the foundations of:

- a guided campaign diagnosis tool
- a proposal and approval workflow
- API-safe execution
- a campaign creation assistant
- a local xquads-powered decision engine

The next step is not "add more metrics".

The next step is to make the system feel like a trustworthy operator that can:

- understand the account
- explain itself clearly
- propose strong solutions
- and act only when the user is comfortable approving the change

