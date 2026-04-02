'use client'

import React from 'react'
import { Campaign } from '@/types'

interface CampaignTableProps {
  campaigns: Campaign[]
  isLoading?: boolean
  onCampaignClick?: (campaign: Campaign) => void
}

function formatCompactNumber(value: number | undefined) {
  if (value === undefined) return '—'
  return new Intl.NumberFormat('pt-BR').format(value)
}

function formatCurrency(value: number | undefined) {
  if (value === undefined) return '—'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 2,
  }).format(value)
}

function formatPercent(value: number | undefined) {
  if (value === undefined) return '—'
  return `${(value * 100).toFixed(2)}%`
}

function getSituation(campaign: Campaign) {
  const metrics = campaign.latest_metrics

  if (campaign.status !== 'ENABLED') {
    return {
      badge: 'Pausada',
      tone: 'bg-slate-100 text-slate-700',
      summary: 'Esta campanha nao esta rodando no momento.',
      nextStep: 'Revisar o plano antes de voltar a ativar.',
    }
  }

  if (!metrics || (metrics.impressions === 0 && metrics.clicks === 0 && metrics.cost === 0)) {
    return {
      badge: 'Sem entrega',
      tone: 'bg-rose-100 text-rose-700',
      summary: 'Ela ainda nao comecou a aparecer de verdade para as pessoas.',
      nextStep: 'Abrir a analise guiada para descobrir por que nao esta veiculando.',
    }
  }

  if (metrics.clicks === 0) {
    return {
      badge: 'Com impressao, sem clique',
      tone: 'bg-amber-100 text-amber-800',
      summary: 'O anuncio aparece, mas nao esta chamando acao suficiente.',
      nextStep: 'Revisar busca, copy e alinhamento da oferta.',
    }
  }

  if (metrics.clicks > 0 && metrics.conversions === 0) {
    return {
      badge: 'Recebe cliques',
      tone: 'bg-sky-100 text-sky-700',
      summary: 'As pessoas clicam, mas ainda nao vemos resultado final.',
      nextStep: 'Investigar landing page, tracking e qualidade da busca.',
    }
  }

  return {
    badge: 'Com sinal de resultado',
    tone: 'bg-emerald-100 text-emerald-700',
    summary: 'Ja existe sinal suficiente para pensar em otimizar com mais seguranca.',
    nextStep: 'Abrir a campanha para revisar o que manter e o que escalar.',
  }
}

export function CampaignTable({ campaigns, isLoading, onCampaignClick }: CampaignTableProps) {
  const sortedCampaigns = [...campaigns].sort((left, right) => {
    const leftMetrics = left.latest_metrics
    const rightMetrics = right.latest_metrics

    const leftPriority =
      left.status !== 'ENABLED'
        ? 3
        : !leftMetrics || leftMetrics.impressions === 0
        ? 0
        : leftMetrics.conversions === 0
        ? 1
        : 2
    const rightPriority =
      right.status !== 'ENABLED'
        ? 3
        : !rightMetrics || rightMetrics.impressions === 0
        ? 0
        : rightMetrics.conversions === 0
        ? 1
        : 2

    if (leftPriority !== rightPriority) {
      return leftPriority - rightPriority
    }

    return left.name.localeCompare(right.name)
  })

  if (isLoading) {
    return (
      <div className="rounded-[28px] border border-slate-200 bg-white p-8 shadow-sm">
        <div className="grid gap-4 lg:grid-cols-2">
          {[...Array(4)].map((_, index) => (
            <div key={index} className="h-48 animate-pulse rounded-[24px] bg-slate-100" />
          ))}
        </div>
      </div>
    )
  }

  if (campaigns.length === 0) {
    return (
      <div className="rounded-[28px] border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm">
        <p className="text-lg font-semibold text-slate-900">Nenhuma campanha encontrada</p>
        <p className="mt-2 text-sm text-slate-600">
          Quando houver campanhas sincronizadas, elas vao aparecer aqui em ordem de prioridade.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {sortedCampaigns.map((campaign) => {
        const metrics = campaign.latest_metrics
        const situation = getSituation(campaign)

        return (
          <button
            key={campaign.id}
            type="button"
            onClick={() => onCampaignClick?.(campaign)}
            className="w-full rounded-[28px] border border-slate-200 bg-white p-6 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
          >
            <div className="flex flex-col gap-6 xl:flex-row xl:items-start xl:justify-between">
              <div className="max-w-3xl">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${situation.tone}`}>
                    {situation.badge}
                  </span>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                    {campaign.type}
                  </span>
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-500 ring-1 ring-slate-200">
                    {campaign.status === 'ENABLED' ? 'Ativa' : 'Pausada'}
                  </span>
                </div>

                <h3 className="mt-4 text-xl font-semibold text-slate-900">{campaign.name}</h3>
                <p className="mt-3 text-sm text-slate-700">{situation.summary}</p>
                <p className="mt-2 text-sm font-medium text-slate-900">
                  Proximo passo: <span className="font-normal text-slate-600">{situation.nextStep}</span>
                </p>
              </div>

              <div className="xl:min-w-[260px]">
                <div className="rounded-[24px] bg-slate-900 p-5 text-white">
                  <p className="text-xs uppercase tracking-[0.24em] text-white/60">Abrir agora</p>
                  <p className="mt-3 text-lg font-semibold">Analise guiada da campanha</p>
                  <p className="mt-2 text-sm text-white/75">
                    Entenda o problema em linguagem simples e aprove correcoes pelo app.
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              <div className="rounded-2xl bg-slate-50 px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">Impressoes</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">
                  {formatCompactNumber(metrics?.impressions)}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-50 px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">Cliques</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">
                  {formatCompactNumber(metrics?.clicks)}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-50 px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">CTR</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">
                  {formatPercent(metrics?.ctr)}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-50 px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">Investimento</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">
                  {formatCurrency(metrics?.cost)}
                </p>
              </div>
              <div className="rounded-2xl bg-slate-50 px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-slate-400">Resultado</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">
                  {metrics ? metrics.conversions.toFixed(2) : '—'}
                </p>
              </div>
            </div>
          </button>
        )
      })}
    </div>
  )
}
