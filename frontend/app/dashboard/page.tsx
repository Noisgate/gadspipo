'use client'

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth'
import { useDashboardStats, useCampaigns } from '@/hooks/useCampaigns'
import { MetricsCard } from '@/components/dashboard/MetricsCard'
import { CampaignTable } from '@/components/dashboard/CampaignTable'
import { Header } from '@/components/dashboard/Header'

function formatCurrency(value?: number) {
  if (value === undefined) return '—'

  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 2,
  }).format(value)
}

function getDashboardNarrative(
  totalCampaigns: number,
  activeCampaigns: number,
  stalledCampaigns: number,
  campaignsWithConversions: number
) {
  if (totalCampaigns === 0) {
    return {
      headline: 'Sua operacao ainda nao tem campanhas conectadas.',
      detail: 'O proximo passo e conectar a conta e criar a primeira campanha guiada.',
    }
  }

  if (stalledCampaigns > 0) {
    return {
      headline: 'A prioridade agora e descobrir por que parte das campanhas nao esta entregando.',
      detail: 'Antes de falar em otimizar budget ou escalar, vale resolver bloqueios de entrega e tracking.',
    }
  }

  if (campaignsWithConversions > 0) {
    return {
      headline: 'Ja existe sinal de resultado para comecar ajustes mais inteligentes.',
      detail: 'Agora faz sentido comparar campanhas, entender o que converte e decidir o que deve crescer.',
    }
  }

  return {
    headline: 'As campanhas ja estao em movimento, mas ainda estamos na fase de leitura.',
    detail: 'O melhor uso da plataforma agora e abrir as campanhas e entender se o gargalo esta em busca, anuncio, pagina ou medicao.',
  }
}

export default function DashboardPage() {
  const router = useRouter()
  const { token, isInitialized } = useAuth()
  const { stats, isLoading: statsLoading } = useDashboardStats()
  const { campaigns, isLoading: campaignsLoading } = useCampaigns()
  const stalledCampaigns = campaigns.filter((campaign) => {
    const metrics = campaign.latest_metrics
    return campaign.status === 'ENABLED' && (!metrics || metrics.impressions === 0)
  }).length
  const campaignsWithConversions = campaigns.filter(
    (campaign) => (campaign.latest_metrics?.conversions ?? 0) > 0
  ).length
  const narrative = getDashboardNarrative(
    campaigns.length,
    stats?.active_campaigns ?? 0,
    stalledCampaigns,
    campaignsWithConversions
  )

  useEffect(() => {
    if (isInitialized && !token) {
      router.push('/login')
    }
  }, [token, isInitialized, router])

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Carregando...</p>
      </div>
    )
  }

  if (!token) {
    return null
  }

  return (
    <div className="min-h-screen bg-stone-50">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <section className="rounded-[32px] bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 p-8 text-white shadow-lg">
          <p className="text-xs uppercase tracking-[0.3em] text-white/60">Visao geral guiada</p>
          <h1 className="mt-4 text-3xl font-semibold sm:text-4xl">Entenda sua operacao sem falar "Google Ads"</h1>
          <p className="mt-4 max-w-3xl text-sm leading-6 text-white/80 sm:text-base">
            Esta tela resume o que temos hoje, qual etapa do fluxo xquads faz sentido agora e
            para onde voce deveria olhar primeiro.
          </p>

          <div className="mt-8 grid gap-4 xl:grid-cols-[1.4fr,0.8fr]">
            <div className="rounded-[28px] bg-white/10 p-6 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.24em] text-white/60">Leitura principal</p>
              <p className="mt-3 text-2xl font-semibold">{narrative.headline}</p>
              <p className="mt-3 text-sm text-white/80">{narrative.detail}</p>
            </div>

            <div className="rounded-[28px] bg-white/10 p-6 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.24em] text-white/60">Fluxo xquads</p>
              <div className="mt-4 space-y-2 text-sm text-white/80">
                <p>1. Diagnosticar a entrega</p>
                <p>2. Validar tracking e pagina</p>
                <p>3. Organizar estrutura e busca</p>
                <p>4. Otimizar so depois de sinais reais</p>
              </div>
            </div>
          </div>
        </section>

        {statsLoading ? (
          <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-[24px] bg-white p-6 shadow-sm animate-pulse">
                <div className="mb-4 h-4 w-1/2 rounded bg-slate-200" />
                <div className="h-8 w-3/4 rounded bg-slate-200" />
              </div>
            ))}
          </div>
        ) : stats ? (
          <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricsCard
              title="Total de Campanhas"
              value={stats.total_campaigns}
              icon="TC"
            />
            <MetricsCard
              title="Campanhas Ativas"
              value={stats.active_campaigns}
              icon="AT"
            />
            <MetricsCard
              title="Investimento"
              value={formatCurrency(stats.metrics.total_cost)}
              icon="R$"
            />
            <MetricsCard
              title="Conversoes"
              value={stats.metrics.total_conversions.toFixed(2)}
              icon="CV"
            />
          </div>
        ) : null}

        <section className="mt-8 grid gap-4 lg:grid-cols-3">
          <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Agora</p>
            <h2 className="mt-3 text-lg font-semibold text-slate-900">O que olhar primeiro</h2>
            <p className="mt-2 text-sm text-slate-600">
              {stalledCampaigns > 0
                ? `${stalledCampaigns} campanha(s) ativa(s) ainda nao mostram entrega. Comece por elas.`
                : 'Nao ha grande sinal de travamento agora. Voce pode abrir as campanhas com mais calma para leitura e refinamento.'}
            </p>
          </div>
          <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Depois</p>
            <h2 className="mt-3 text-lg font-semibold text-slate-900">Quando pensar em otimizar</h2>
            <p className="mt-2 text-sm text-slate-600">
              So vale mexer em budget e escala quando a campanha entrega, mede e gera sinal confiavel.
            </p>
          </div>
          <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Como usar</p>
            <h2 className="mt-3 text-lg font-semibold text-slate-900">Abra uma campanha</h2>
            <p className="mt-2 text-sm text-slate-600">
              A tela da campanha traduz o problema em linguagem simples, monta o plano e deixa voce aprovar a execucao.
            </p>
          </div>
        </section>

        <div className="mt-8">
          <div className="mb-4 flex items-end justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold text-slate-900">Campanhas em ordem de prioridade</h2>
              <p className="mt-2 text-sm text-slate-600">
                A lista abaixo foi reorganizada para te ajudar a agir sem precisar interpretar metricas cruas.
              </p>
            </div>
          </div>
          <CampaignTable
            campaigns={campaigns}
            isLoading={campaignsLoading}
            onCampaignClick={(campaign) => router.push(`/campaigns/${campaign.id}`)}
          />
        </div>
      </main>
    </div>
  )
}
