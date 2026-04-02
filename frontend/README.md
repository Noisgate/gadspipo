# Marketing Manager - Frontend (Next.js + TypeScript + Tailwind)

Dashboard React para gerenciar campanhas Google Ads em tempo real.

---

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Create .env.local
cp .env.example .env.local

# Edit .env.local if needed
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

Acesso: http://localhost:3000

---

## 📁 Estrutura

```
app/
├── layout.tsx              # Root layout
├── page.tsx                # Home page
├── globals.css             # Global styles
├── providers.tsx           # Auth initialization
├── login/page.tsx          # Login page (Google OAuth)
└── dashboard/page.tsx      # Main dashboard

components/
├── dashboard/
│   ├── Header.tsx          # Top navigation
│   ├── MetricsCard.tsx     # Stats cards
│   ├── CampaignTable.tsx   # Campaign list
│   └── PerformanceChart.tsx # Recharts graphs
└── auth/
    └── ProtectedRoute.tsx  # Auth guard

hooks/
├── useCampaigns.ts         # SWR data fetching
└── useAuth.ts              # Auth state

contexts/
└── auth.ts                 # Zustand auth store

lib/
└── api-client.ts           # Axios API wrapper

types/
└── index.ts                # TypeScript interfaces
```

---

## 🔐 Autenticação

1. Usuário clica "Login com Google"
2. Redireciona para `/api/v1/auth/google` do backend
3. Google OAuth flow
4. Callback para backend em `/api/v1/auth/google/callback?code=...&state=...`
5. Backend troca code por JWT token
6. JWT armazenado em cookie (httpOnly)
7. Todas as requests incluem: `Authorization: Bearer <JWT>`

---

## 📊 Componentes Principais

### MetricsCard
Exibe um métrica com ícone e tendência (opcional).

```tsx
<MetricsCard
  title="Total de Cliques"
  value={12345}
  icon="🖱️"
  unit="clicks"
  trend={{ value: 15, direction: 'up' }}
/>
```

### CampaignTable
Tabela responsiva com campanhas e suas métricas.

```tsx
<CampaignTable
  campaigns={campaigns}
  isLoading={isLoading}
  onCampaignClick={(campaign) => router.push(`/campaigns/${campaign.id}`)}
/>
```

### PerformanceChart
Gráfico de linha com Recharts. Suporta múltiplas linhas.

```tsx
<PerformanceChart
  data={metricsData}
  title="Cliques e Conversões"
  lines={['clicks', 'conversions']}
/>
```

---

## 🎣 Hooks

### useCampaigns()
Fetch campanhas com SWR (auto-revalidate a cada 30s).

```tsx
const { campaigns, isLoading, error, mutate } = useCampaigns()
```

### useDashboardStats()
Fetch stats agregadas do dashboard.

```tsx
const { stats, isLoading } = useDashboardStats()
```

### useAuth()
Zustand store para autenticação.

```tsx
const { user, token, logout } = useAuth()
```

---

## 🔄 State Management

Usa Zustand para auth (simples + rápido):

```tsx
// contexts/auth.ts
export const useAuth = create<AuthState>((set) => ({
  user: null,
  token: null,
  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),
}))
```

Usa SWR para data fetching (melhor para queries HTTP):

```tsx
// hooks/useCampaigns.ts
const { data, error, mutate } = useSWR('/campaigns', fetcher)
```

---

## 🎨 Tailwind + Componentes

Usa Tailwind puro (sem shadcn/ui, mantém simples):

- Cards com `bg-white rounded-lg shadow p-6`
- Buttons com `px-4 py-2 text-white bg-primary-600 rounded`
- Tables com `divide-y divide-gray-200`
- Grids responsivos: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`

---

## 📈 Fluxo de Dados

```
[User Login] 
    ↓
[Google OAuth]
    ↓
[Backend: /auth/google/callback]
    ↓
[JWT Token stored in cookie]
    ↓
[API Requests with Auth header]
    ↓
[SWR caches responses]
    ↓
[React re-renders with data]
```

---

## 🚀 Build + Deploy

```bash
# Build
npm run build

# Start production
npm start

# Type check
npm run type-check
```

---

## 📌 TODO (Fase 3 Futuro)

- [ ] Página de detalhe da campanha
- [ ] Formulário para criar campanha
- [ ] Página de recomendações
- [ ] Filtros e ordenação na tabela
- [ ] Dark mode toggle
- [ ] Mobile responsiveness melhorada
- [ ] Notifications (toast) sistema

---

**Status:** ✅ MVP funcional | **Próximo:** Integrar com backend + n8n
