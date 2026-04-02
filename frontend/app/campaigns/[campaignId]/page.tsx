'use client'

import Link from 'next/link'
import React, { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { toast } from 'sonner'

import { ProposalActionCard } from '@/components/recommendations/ProposalActionCard'
import { Header } from '@/components/dashboard/Header'
import { useAuth } from '@/contexts/auth'
import {
  useCampaignDetail,
  useCampaignInvestigation,
  useCampaignKeywords,
  useCampaignSearchTerms,
} from '@/hooks/useCampaigns'
import { apiClient } from '@/lib/api-client'
import { CampaignInvestigation, GoogleAdsQueryKeyword, GoogleAdsQuerySearchTerm } from '@/types'

function formatCurrency(value?: number | null) {
  if (value === null || value === undefined) {
    return '—'
  }

  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 2,
  }).format(value)
}

function formatPercent(value?: number | null) {
  if (value === null || value === undefined) {
    return '—'
  }

  return `${(value * 100).toFixed(2)}%`
}

function trendLabel(trend?: 'up' | 'down' | 'stable' | null) {
  if (trend === 'up') return 'Melhorando'
  if (trend === 'down') return 'Perdendo forca'
  if (trend === 'stable') return 'Estavel'
  return 'Sem tendencia forte'
}

function MetricCard({
  label,
  value,
  helper,
}: {
  label: string
  value: string
  helper?: string
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className="mt-3 text-2xl font-semibold text-gray-900">{value}</p>
      {helper ? <p className="mt-2 text-sm text-gray-500">{helper}</p> : null}
    </div>
  )
}

function InfoList({
  title,
  items,
  tone,
}: {
  title: string
  items: string[]
  tone: 'neutral' | 'good' | 'warning'
}) {
  const toneClass =
    tone === 'good'
      ? 'bg-emerald-50 border-emerald-200'
      : tone === 'warning'
      ? 'bg-amber-50 border-amber-200'
      : 'bg-gray-50 border-gray-200'

  return (
    <div className={`rounded-2xl border p-5 ${toneClass}`}>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-700">{title}</h3>
      {items.length > 0 ? (
        <div className="mt-4 space-y-3">
          {items.map((item) => (
            <div key={item} className="rounded-xl bg-white/70 px-4 py-3 text-sm text-gray-700">
              {item}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-gray-600">Nenhum ponto encontrado nesta leitura.</p>
      )}
    </div>
  )
}

function qualityBadge(score?: number | null) {
  if (score === null || score === undefined) return 'bg-gray-100 text-gray-600'
  if (score >= 7) return 'bg-emerald-100 text-emerald-700'
  if (score >= 5) return 'bg-amber-100 text-amber-700'
  return 'bg-red-100 text-red-700'
}

function deliveryBadge(stage: 'NOT_SERVING' | 'LIMITED' | 'SERVING') {
  if (stage === 'NOT_SERVING') return 'bg-rose-100 text-rose-700'
  if (stage === 'LIMITED') return 'bg-amber-100 text-amber-800'
  return 'bg-emerald-100 text-emerald-700'
}

function repairStepBadge(status: 'pending' | 'in_progress' | 'completed') {
  if (status === 'completed') return 'bg-emerald-100 text-emerald-700'
  if (status === 'in_progress') return 'bg-sky-100 text-sky-700'
  return 'bg-slate-100 text-slate-700'
}

function repairStepLabel(status: 'pending' | 'in_progress' | 'completed') {
  if (status === 'completed') return 'Concluida'
  if (status === 'in_progress') return 'Em andamento'
  return 'Pendente'
}

function getCampaignNarrative({
  stage,
  summary,
  conversions,
  hasInvestigation,
}: {
  stage?: 'NOT_SERVING' | 'LIMITED' | 'SERVING'
  summary?: string
  conversions: number
  hasInvestigation: boolean
}) {
  if (stage === 'NOT_SERVING') {
    return {
      title: 'A campanha ainda nao esta entrando em campo.',
      reason: summary ?? 'Ainda nao temos sinal de entrega suficiente para tratar isso como otimizacao.',
      nextStep: hasInvestigation
        ? 'Revise o plano de investigacao e aprove a correcao por API quando fizer sentido.'
        : 'Peca para o app investigar por que ela nao esta veiculando.',
    }
  }

  if (stage === 'LIMITED') {
    return {
      title: 'A campanha aparece, mas ainda nao ganha tracao com consistencia.',
      reason: summary ?? 'Ha sinal parcial, entao o foco precisa ser remover gargalos antes de escalar.',
      nextStep: hasInvestigation
        ? 'Use a investigacao para decidir o que corrigir primeiro.'
        : 'Abra uma investigacao para descobrir se o gargalo esta em busca, anuncio, pagina ou tracking.',
    }
  }

  if (conversions > 0) {
    return {
      title: 'A campanha ja mostra sinal de resultado.',
      reason: summary ?? 'Agora faz sentido comparar, priorizar e discutir ajustes mais assertivos.',
      nextStep: 'Revise as propostas liberadas e deixe o app executar so o que voce aprovar.',
    }
  }

  return {
    title: 'A campanha esta em fase de leitura.',
    reason: summary ?? 'Ainda precisamos confirmar melhor se o problema esta na entrega ou na conversao.',
    nextStep: hasInvestigation
      ? 'Use o plano investigado como roteiro.'
      : 'Comece pedindo ao app para investigar a causa-raiz.',
  }
}

function getApiCapabilitySummary(stage?: 'NOT_SERVING' | 'LIMITED' | 'SERVING') {
  if (stage === 'NOT_SERVING') {
    return 'O app pode corrigir por API apenas o que estiver dentro do Google Ads, como budget, negativas, keywords e pausa. Se o problema for landing page, policy ou tracking externo, ele vai explicar isso antes.'
  }

  if (stage === 'LIMITED') {
    return 'O app consegue preparar e aplicar correcoes seguras por API, mas so depois da sua aprovacao.'
  }

  return 'Quando houver proposta elegivel, o app consegue executar as mudancas aprovadas por API e depois atualizar a leitura sozinho.'
}

export default function CampaignDetailPage() {
  const params = useParams<{ campaignId: string }>()
  const campaignId = Array.isArray(params.campaignId) ? params.campaignId[0] : params.campaignId
  const router = useRouter()
  const { token, isInitialized } = useAuth()
  const {
    campaign,
    isLoading,
    isError,
    error,
    mutate: mutateCampaign,
  } = useCampaignDetail(campaignId ?? null)
  const {
    investigation,
    isLoading: isInvestigationLoading,
    mutate: mutateInvestigation,
  } = useCampaignInvestigation(campaignId ?? null)
  const {
    keywords,
    isLoading: isKeywordsLoading,
    mutate: mutateKeywords,
  } = useCampaignKeywords(campaignId ?? null)
  const {
    searchTerms,
    isLoading: isSearchTermsLoading,
    mutate: mutateSearchTerms,
  } = useCampaignSearchTerms(campaignId ?? null)
  const [isSyncing, setIsSyncing] = useState(false)
  const [investigationPrompt, setInvestigationPrompt] = useState(
    'Quero entender por que essa campanha nao esta funcionando, qual e a causa-raiz e qual solucao devo aprovar.'
  )
  const [isInvestigating, setIsInvestigating] = useState(false)
  const [approvalNote, setApprovalNote] = useState('')
  const [isApprovingInvestigation, setIsApprovingInvestigation] = useState(false)
  const [executionNote, setExecutionNote] = useState('')
  const [isExecutingInvestigationRepair, setIsExecutingInvestigationRepair] = useState(false)

  useEffect(() => {
    if (isInitialized && !token) {
      router.push('/login')
    }
  }, [token, isInitialized, router])

  useEffect(() => {
    setApprovalNote(investigation?.approval_payload.approval_note ?? '')
  }, [investigation?.id, investigation?.approval_payload.approval_note])

  useEffect(() => {
    setExecutionNote(investigation?.approval_payload.execution_note ?? '')
  }, [investigation?.id, investigation?.approval_payload.execution_note])

  const handleSync = async () => {
    if (!campaign?.account_id) {
      return
    }

    try {
      setIsSyncing(true)
      const response = await apiClient.syncCampaigns(campaign.account_id)
      await Promise.all([
        mutateCampaign(),
        mutateKeywords(),
        mutateSearchTerms(),
      ])
      toast.success(
        `Sync concluido: ${response.stats?.updated ?? 0} atualizadas e ${response.stats?.created ?? 0} novas.`
      )
    } catch (syncError: any) {
      toast.error(apiClient.getErrorMessage(syncError))
    } finally {
      setIsSyncing(false)
    }
  }

  const handleInvestigate = async () => {
    if (!campaignId || !investigationPrompt.trim()) {
      return
    }

    try {
      setIsInvestigating(true)
      const response = await apiClient.investigateCampaign(campaignId, {
        prompt: investigationPrompt.trim(),
      })
      await Promise.all([
        mutateInvestigation(response as CampaignInvestigation, {
          revalidate: false,
        }),
        mutateCampaign(),
        mutateKeywords(),
        mutateSearchTerms(),
      ])
      toast.success('Investigacao atualizada com diagnostico e plano de correcao.')
    } catch (investigationError: any) {
      toast.error(apiClient.getErrorMessage(investigationError))
    } finally {
      setIsInvestigating(false)
    }
  }

  const handleApproveInvestigation = async () => {
    if (!campaignId || !investigation?.id) {
      return
    }

    try {
      setIsApprovingInvestigation(true)
      const response = await apiClient.approveCampaignInvestigation(
        campaignId,
        investigation.id,
        {
          approval_note: approvalNote.trim() || undefined,
        }
      )
      await mutateInvestigation(response as CampaignInvestigation, {
        revalidate: false,
      })
      toast.success('Plano aprovado. Agora as acoes candidatas podem seguir para proposta e execucao.')
    } catch (approvalError: any) {
      toast.error(apiClient.getErrorMessage(approvalError))
    } finally {
      setIsApprovingInvestigation(false)
    }
  }

  const handleExecuteInvestigationRepair = async () => {
    if (!campaignId || !investigation?.id) {
      return
    }

    try {
      setIsExecutingInvestigationRepair(true)
      const response = await apiClient.executeCampaignInvestigation(
        campaignId,
        investigation.id,
        {
          execution_note: executionNote.trim() || undefined,
        }
      )
      await Promise.all([
        mutateInvestigation(response as CampaignInvestigation, {
          revalidate: false,
        }),
        mutateCampaign(),
        mutateKeywords(),
        mutateSearchTerms(),
      ])
      toast.success('O app aplicou as correcoes elegiveis por API e atualizou o diagnostico.')
    } catch (executionError: any) {
      toast.error(apiClient.getErrorMessage(executionError))
    } finally {
      setIsExecutingInvestigationRepair(false)
    }
  }

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

  const performance = campaign?.performance
  const analysis = campaign?.analysis
  const deliveryDiagnosis = analysis?.delivery_diagnosis
  const dailyData = performance?.daily_data.slice(-7).reverse() ?? []
  const recommendedActions = campaign?.recommended_actions ?? []
  const approvalPayload = investigation?.approval_payload
  const candidateActions = approvalPayload?.candidate_actions ?? []
  const apiSafeCandidateActions = candidateActions.filter((action) =>
    action.execution_modes.includes('approve_and_execute')
  )
  const executionResults = approvalPayload?.execution_results ?? []
  const blockedUntilApproval = approvalPayload?.blocked_until_approval ?? true
  const approveAndExecuteActions = recommendedActions.filter((action) =>
    action.execution_modes.includes('approve_and_execute')
  )
  const automationActions = recommendedActions.filter((action) =>
    action.execution_modes.includes('create_automation')
  )
  const planOnlyActions = recommendedActions.filter((action) =>
    action.execution_modes.includes('plan_only')
  )
  const repairSteps = investigation?.repair_plan.sequence ?? []
  const repairHistory = investigation?.repair_plan.history ?? []
  const completedRepairSteps = repairSteps.filter((step) => step.status === 'completed').length
  const inProgressRepairSteps = repairSteps.filter((step) => step.status === 'in_progress').length
  const campaignNarrative = getCampaignNarrative({
    stage: deliveryDiagnosis?.stage,
    summary: deliveryDiagnosis?.summary,
    conversions: performance?.metrics.total_conversions ?? 0,
    hasInvestigation: !!investigation,
  })
  const apiCapabilitySummary = getApiCapabilitySummary(deliveryDiagnosis?.stage)

  return (
    <div className="min-h-screen bg-stone-50">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8 rounded-[28px] bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 p-6 text-white shadow-lg">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <Link
                href="/campaigns"
                className="inline-flex rounded-full border border-white/20 px-3 py-1 text-xs font-medium uppercase tracking-wide text-white/80 transition hover:bg-white/10"
              >
                Voltar para campanhas
              </Link>
              <h1 className="mt-4 text-3xl font-semibold">{campaign?.name ?? 'Campanha'}</h1>
              <p className="mt-2 max-w-3xl text-sm text-white/80">
                Aqui o app traduz a campanha para linguagem simples, explica o problema e prepara um plano para voce aprovar antes de agir.
              </p>
              {campaign ? (
                <div className="mt-4 flex flex-wrap gap-2 text-sm">
                  <span className="rounded-full bg-white/10 px-3 py-1">
                    {campaign.account_name}
                  </span>
                  <span className="rounded-full bg-white/10 px-3 py-1">
                    {campaign.type}
                  </span>
                  <span className="rounded-full bg-white/10 px-3 py-1">
                    {campaign.status === 'ENABLED' ? 'Ativa' : 'Pausada'}
                  </span>
                  {analysis ? (
                    <span className="rounded-full bg-amber-300/20 px-3 py-1 text-amber-100">
                      {analysis.tier_label}
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>

            <div className="flex flex-col gap-3 lg:min-w-[240px]">
              <button
                type="button"
                onClick={handleSync}
                disabled={isSyncing || !campaign}
                className="inline-flex items-center justify-center rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSyncing ? 'Sincronizando conta...' : 'Sincronizar Google Ads'}
              </button>
              <p className="text-xs text-white/70">
                A tela se atualiza sozinha, mas este botao puxa uma leitura nova do Google Ads para renovar o diagnostico.
              </p>
            </div>
          </div>
        </div>

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[...Array(4)].map((_, index) => (
              <div key={index} className="h-32 animate-pulse rounded-2xl bg-white shadow" />
            ))}
          </div>
        ) : null}

        {isError ? (
          <div className="rounded-2xl bg-white p-6 shadow">
            <p className="font-medium text-red-600">Nao foi possivel carregar a campanha.</p>
            <p className="mt-2 text-sm text-gray-600">{error}</p>
          </div>
        ) : null}

        {!isLoading && !isError && campaign && analysis && performance ? (
          <div className="space-y-8">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              <MetricCard
                label="Leitura geral"
                value={`${analysis.score}/100`}
                helper={trendLabel(analysis.trend)}
              />
              <MetricCard
                label="Custo em 30 dias"
                value={formatCurrency(performance.metrics.total_cost)}
                helper={formatCurrency(campaign.budget_daily) + ' por dia de budget'}
              />
              <MetricCard
                label="Conversoes"
                value={performance.metrics.total_conversions.toFixed(2)}
                helper={`CPA ${formatCurrency(performance.metrics.avg_cpa)}`}
              />
              <MetricCard
                label="CTR"
                value={formatPercent(performance.metrics.avg_ctr)}
                helper={`Media da conta ${formatPercent(analysis.benchmark.account_avg_ctr)}`}
              />
              <MetricCard
                label="ROAS estimado"
                value={
                  performance.metrics.roas !== null && performance.metrics.roas !== undefined
                    ? `${performance.metrics.roas.toFixed(2)}x`
                    : '—'
                }
                helper={`CPC ${formatCurrency(performance.metrics.avg_cpc)}`}
              />
            </div>

            <section className="grid gap-4 xl:grid-cols-[1.2fr,0.9fr,0.9fr]">
              <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Em poucas palavras</p>
                <h2 className="mt-3 text-2xl font-semibold text-slate-900">{campaignNarrative.title}</h2>
                <p className="mt-3 text-sm leading-6 text-slate-700">{campaignNarrative.reason}</p>
                <p className="mt-4 text-sm font-medium text-slate-900">
                  Proximo passo:
                  <span className="ml-2 font-normal text-slate-600">{campaignNarrative.nextStep}</span>
                </p>
              </div>

              <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">O que o app consegue fazer</p>
                <p className="mt-3 text-sm leading-6 text-slate-700">{apiCapabilitySummary}</p>
              </div>

              <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-sm">
                <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Metodo xquads</p>
                <div className="mt-3 space-y-2 text-sm text-slate-700">
                  <p>1. Diagnosticar o problema</p>
                  <p>2. Montar um plano claro</p>
                  <p>3. Discutir e ajustar</p>
                  <p>4. Aprovar e executar por API</p>
                </div>
              </div>
            </section>

            {deliveryDiagnosis ? (
              <section className="grid gap-6 xl:grid-cols-[1.2fr,0.9fr,0.9fr]">
                <div className="rounded-2xl bg-white p-6 shadow-sm">
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-xl font-semibold text-gray-900">Por que ela pode nao estar rodando</h2>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${deliveryBadge(deliveryDiagnosis.stage)}`}>
                      {deliveryDiagnosis.status_label}
                    </span>
                    {campaign.primary_status ? (
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                        Google: {campaign.primary_status}
                      </span>
                    ) : null}
                  </div>

                  <p className="mt-3 text-sm text-gray-700">{deliveryDiagnosis.summary}</p>

                  {campaign.primary_status_reasons.length > 0 ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {campaign.primary_status_reasons.map((reason) => (
                        <span
                          key={reason}
                          className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
                        >
                          {reason}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>

                <InfoList title="Bloqueios detectados" items={deliveryDiagnosis.blockers} tone="warning" />
                <InfoList title="Proximas checagens" items={deliveryDiagnosis.next_checks} tone="neutral" />
              </section>
            ) : null}

            {deliveryDiagnosis ? (
              <section className="grid gap-4 lg:grid-cols-2">
                <InfoList title="Evidencias" items={deliveryDiagnosis.evidence} tone="neutral" />
                <InfoList
                  title="Playbooks xquads para este caso"
                  items={deliveryDiagnosis.xquads_playbooks}
                  tone="good"
                />
              </section>
            ) : null}

            <section className="rounded-2xl bg-white p-6 shadow-sm">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="max-w-3xl">
                  <h2 className="text-xl font-semibold text-gray-900">Peca para o app investigar</h2>
                  <p className="mt-2 text-sm text-gray-600">
                    Escreva em portugues normal. O app investiga a campanha, organiza a causa-raiz, monta um plano de correcao e atualiza a tela na hora.
                  </p>
                </div>
                <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                  {investigation ? 'Ultima investigacao carregada' : 'Nenhuma investigacao salva ainda'}
                </div>
              </div>

              <label className="mt-5 block">
                <span className="text-sm font-medium text-gray-700">O que voce quer entender ou resolver?</span>
                <textarea
                  value={investigationPrompt}
                  onChange={(event) => setInvestigationPrompt(event.target.value)}
                  rows={4}
                  className="mt-2 w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
                />
              </label>

              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => void handleInvestigate()}
                  disabled={isInvestigating || !campaignId}
                  className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isInvestigating ? 'Investigando campanha...' : 'Entender o problema e montar plano'}
                </button>
                <p className="self-center text-sm text-gray-500">
                  O resultado fica salvo e a tela muda na hora, sem voce ter que recarregar.
                </p>
              </div>

              {isInvestigationLoading && !investigation ? (
                <p className="mt-4 text-sm text-gray-500">Carregando ultima investigacao...</p>
              ) : null}

              {investigation ? (
                <div className="mt-6 space-y-6">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-medium text-white">
                        {investigation.analysis_mode === 'DIAGNOSTIC' ? 'Modo diagnostico' : 'Modo otimizacao'}
                      </span>
                      <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700">
                        Status {investigation.status.toLowerCase()}
                      </span>
                    </div>
                    <p className="mt-3 text-base font-semibold text-gray-900">{investigation.summary}</p>
                    <p className="mt-2 text-sm text-gray-700">
                      <span className="font-medium">Causa-raiz mais provavel:</span> {investigation.root_cause}
                    </p>
                    <p className="mt-2 text-sm text-gray-600">
                      <span className="font-medium">Sync antes da investigacao:</span>{' '}
                      {investigation.diagnosis.sync_status.detail}
                    </p>
                    <p className="mt-3 text-xs text-gray-500">
                      Pedido salvo: {investigation.prompt}
                    </p>
                  </div>

                  <div className="grid gap-4 xl:grid-cols-2">
                    <InfoList title="Bloqueios da investigacao" items={investigation.diagnosis.blockers} tone="warning" />
                    <InfoList title="Evidencias usadas" items={investigation.diagnosis.evidence} tone="neutral" />
                    <InfoList title="Sequencia de playbooks xquads" items={investigation.diagnosis.xquads_playbooks} tone="good" />
                    <InfoList title="Sinais para considerar resolvido" items={investigation.repair_plan.success_signals} tone="good" />
                  </div>

                  <div className="rounded-2xl border border-gray-200 bg-white p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">Plano que o app sugere</h3>
                        <p className="mt-2 text-sm text-gray-600">{investigation.repair_plan.goal}</p>
                      </div>
                      <div className="rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
                        <p className="font-medium text-slate-900">
                          {completedRepairSteps}/{repairSteps.length} etapa(s) concluidas
                        </p>
                        <p className="mt-1 text-xs text-slate-600">
                          {inProgressRepairSteps} em andamento
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 space-y-4">
                      {investigation.repair_plan.sequence.map((step) => (
                        <div key={`${investigation.id}-${step.title}`} className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="text-sm font-semibold text-gray-900">{step.title}</h4>
                            <span className={`rounded-full px-3 py-1 text-xs font-medium ${repairStepBadge(step.status)}`}>
                              {repairStepLabel(step.status)}
                            </span>
                            <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700">
                            {step.owner}
                          </span>
                            <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700">
                              {step.playbook}
                            </span>
                          </div>
                          <p className="mt-2 text-sm text-gray-600">{step.reason}</p>
                          <div className="mt-3 space-y-2">
                            {step.actions.map((item) => (
                              <div key={`${step.title}-${item}`} className="rounded-xl bg-white px-3 py-2 text-sm text-gray-700">
                                {item}
                              </div>
                            ))}
                          </div>

                          <div className="mt-4 rounded-xl bg-white px-4 py-3 text-sm text-gray-600">
                            {blockedUntilApproval
                              ? 'O app ainda nao executa esta etapa sem a sua aprovacao.'
                              : step.status === 'completed'
                              ? step.completion_note || 'Etapa concluida automaticamente pelo app.'
                              : 'Depois da aprovacao, o app atualiza esta etapa automaticamente conforme executa as correcoes e roda o sync.'}
                            {step.completed_at ? (
                              <p className="mt-2 text-xs text-gray-500">
                                Atualizada em {new Date(step.completed_at).toLocaleString('pt-BR')}
                              </p>
                            ) : null}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="max-w-3xl">
                        <h3 className="text-lg font-semibold text-amber-900">
                          {blockedUntilApproval
                            ? 'O que ainda depende da sua aprovacao'
                            : 'Plano aprovado para seguir com as propostas'}
                        </h3>
                        <p className="mt-2 text-sm text-amber-900">{approvalPayload?.message ?? ''}</p>
                      </div>
                      <div className="rounded-xl bg-white px-4 py-3 text-sm text-amber-900">
                        {blockedUntilApproval ? (
                          <span>As acoes continuam bloqueadas ate voce aprovar o plano.</span>
                        ) : (
                          <div className="space-y-1">
                            <p className="font-medium text-emerald-700">Plano liberado para execucao assistida</p>
                            {approvalPayload?.approved_at ? (
                              <p className="text-xs text-gray-500">
                                Aprovado em{' '}
                                {new Date(approvalPayload.approved_at).toLocaleString('pt-BR')}
                              </p>
                            ) : null}
                          </div>
                        )}
                      </div>
                    </div>

                    {blockedUntilApproval ? (
                      <div className="mt-4 space-y-4">
                        <label className="block">
                          <span className="text-sm font-medium text-amber-900">
                            O que quer ajustar antes de aprovar este plano
                          </span>
                          <textarea
                            value={approvalNote}
                            onChange={(event) => setApprovalNote(event.target.value)}
                            rows={4}
                            placeholder="Ex.: quero diagnosticar primeiro a entrega; nao mexer em budget antes de confirmar veiculacao; revisar branded separadamente."
                            className="mt-2 w-full rounded-xl border border-amber-200 bg-white px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                          />
                        </label>

                        <div className="flex flex-wrap gap-3">
                          <button
                            type="button"
                            onClick={() => void handleApproveInvestigation()}
                            disabled={isApprovingInvestigation}
                            className="rounded-xl bg-amber-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            {isApprovingInvestigation ? 'Aprovando plano...' : 'Aprovar plano para seguir'}
                          </button>
                          <p className="self-center text-sm text-amber-900/80">
                            Depois da aprovacao, o app pode preparar e aplicar as correcoes por API quando forem elegiveis.
                          </p>
                        </div>
                      </div>
                    ) : null}

                    {approvalPayload?.approval_note ? (
                      <div className="mt-4 rounded-xl bg-white px-4 py-3 text-sm text-gray-700">
                        <p className="font-medium text-gray-900">Direcao aprovada por voce</p>
                        <p className="mt-1">{approvalPayload.approval_note}</p>
                      </div>
                    ) : null}

                    {!blockedUntilApproval ? (
                      <div className="mt-4 space-y-4">
                        <div className="rounded-xl bg-white px-4 py-3 text-sm text-amber-900">
                          <p className="font-medium text-gray-900">
                            Correcoes prontas para API: {apiSafeCandidateActions.length}
                          </p>
                          <p className="mt-1">
                            {apiSafeCandidateActions.length > 0
                              ? 'O app ja encontrou correcoes seguras e pode aplica-las depois da sua ordem final.'
                              : 'As sugestoes atuais ainda estao em modo de conversa, revisao ou plano manual.'}
                          </p>
                        </div>

                        <label className="block">
                          <span className="text-sm font-medium text-amber-900">
                            Direcao final para a execucao automatica
                          </span>
                          <textarea
                            value={executionNote}
                            onChange={(event) => setExecutionNote(event.target.value)}
                            rows={4}
                            placeholder="Ex.: aplique apenas as correcoes seguras via Google Ads API, depois rode sync e me mostre o novo diagnostico."
                            className="mt-2 w-full rounded-xl border border-amber-200 bg-white px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
                          />
                        </label>

                        <div className="flex flex-wrap gap-3">
                          <button
                            type="button"
                            onClick={() => void handleExecuteInvestigationRepair()}
                            disabled={isExecutingInvestigationRepair || apiSafeCandidateActions.length === 0}
                            className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
                          >
                            {isExecutingInvestigationRepair
                              ? 'Aplicando correcoes...'
                              : apiSafeCandidateActions.length === 0
                              ? 'Nenhuma correcao API-safe agora'
                              : 'Deixar o app corrigir por API'}
                          </button>
                          <p className="self-center text-sm text-amber-900/80">
                            {apiSafeCandidateActions.length > 0
                              ? 'O app tenta executar o que for seguro, roda sync e atualiza o diagnostico sozinho.'
                              : 'Antes de executar, precisamos transformar esta investigacao em uma correcao segura de API ou assumir que o problema esta fora do Google Ads.'}
                          </p>
                        </div>
                      </div>
                    ) : null}

                    <div className="mt-4 space-y-3">
                      {candidateActions.length > 0 ? (
                        candidateActions.map((candidate) => (
                          <div
                            key={`${investigation.id}-${candidate.title}`}
                            className="rounded-xl bg-white px-4 py-3 text-sm text-gray-700"
                          >
                            <p className="font-medium text-gray-900">{candidate.title}</p>
                            <p className="mt-1 text-gray-600">{candidate.description}</p>
                            <p className="mt-2 text-xs uppercase tracking-wide text-gray-500">
                              {candidate.type} • {candidate.source}
                            </p>
                          </div>
                        ))
                      ) : (
                        <p className="text-sm text-amber-900">
                          Esta investigacao ainda nao empurrou nenhuma acao automatica; primeiro precisamos resolver o diagnostico.
                        </p>
                      )}
                    </div>
                  </div>

                  {!blockedUntilApproval &&
                  candidateActions.length > 0 ? (
                    <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
                      <h3 className="text-lg font-semibold text-emerald-900">Propostas liberadas apos a aprovacao</h3>
                      <p className="mt-2 text-sm text-emerald-900">
                        Agora cada correcao volta para o fluxo completo: entender, ajustar, aprovar e executar.
                      </p>

                      <div className="mt-5 grid gap-4 lg:grid-cols-2">
                        {candidateActions.map((candidate) => (
                          <ProposalActionCard
                            key={`${investigation.id}-${candidate.type}-${candidate.title}`}
                            action={candidate}
                            onAfterChange={async () => {
                              await Promise.all([
                                mutateCampaign(),
                                mutateKeywords(),
                                mutateSearchTerms(),
                                mutateInvestigation(),
                              ])
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {!blockedUntilApproval &&
                  executionResults.length > 0 ? (
                    <div className="rounded-2xl border border-slate-200 bg-white p-5">
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div>
                          <h3 className="text-lg font-semibold text-slate-900">Resultado da execucao por API</h3>
                          <p className="mt-2 text-sm text-slate-600">
                            Aqui fica claro o que o app conseguiu corrigir sozinho, o que falhou e o que foi ignorado.
                          </p>
                        </div>
                        {approvalPayload?.last_executed_at ? (
                          <div className="rounded-xl bg-slate-50 px-4 py-3 text-xs text-slate-600">
                            Ultima execucao em{' '}
                            {new Date(approvalPayload.last_executed_at).toLocaleString('pt-BR')}
                          </div>
                        ) : null}
                      </div>

                      <div className="mt-4 space-y-3">
                        {executionResults.map((result) => (
                          <div
                            key={`${result.title}-${result.action_type}-${result.status}`}
                            className="rounded-xl border border-slate-200 px-4 py-3"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="text-sm font-medium text-gray-900">{result.title}</p>
                              <span
                                className={`rounded-full px-3 py-1 text-xs font-medium ${
                                  result.status === 'executed'
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : result.status === 'failed'
                                    ? 'bg-rose-100 text-rose-700'
                                    : 'bg-slate-100 text-slate-700'
                                }`}
                              >
                                {result.status === 'executed'
                                  ? 'Executada'
                                  : result.status === 'failed'
                                  ? 'Falhou'
                                  : 'Ignorada'}
                              </span>
                            </div>
                            <p className="mt-2 text-sm text-gray-700">{result.message}</p>
                            <p className="mt-2 text-xs uppercase tracking-wide text-gray-500">
                              {result.action_type}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  {repairHistory.length > 0 ? (
                    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
                      <h3 className="text-lg font-semibold text-slate-900">Historico do repair workflow</h3>
                      <p className="mt-2 text-sm text-slate-600">
                        Registro das confirmacoes operacionais desta investigacao.
                      </p>

                      <div className="mt-4 space-y-3">
                        {repairHistory
                          .slice()
                          .reverse()
                          .map((entry) => (
                            <div
                              key={`${entry.step_id}-${entry.created_at}-${entry.status}`}
                              className="rounded-xl border border-slate-200 bg-white px-4 py-3"
                            >
                              <div className="flex flex-wrap items-center gap-2">
                                <p className="text-sm font-medium text-gray-900">{entry.title}</p>
                                <span className={`rounded-full px-3 py-1 text-xs font-medium ${repairStepBadge(entry.status)}`}>
                                  {repairStepLabel(entry.status)}
                                </span>
                              </div>
                              {entry.note ? (
                                <p className="mt-2 text-sm text-gray-700">{entry.note}</p>
                              ) : null}
                              <p className="mt-2 text-xs text-gray-500">
                                {new Date(entry.created_at).toLocaleString('pt-BR')}
                              </p>
                            </div>
                          ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </section>

            <section className="grid gap-6 lg:grid-cols-[1.5fr,0.9fr]">
              <div className="rounded-2xl bg-white p-6 shadow-sm">
                <div className="flex flex-col gap-3 border-b border-gray-100 pb-5 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Leitura estrategica da campanha</h2>
                    <p className="mt-2 text-sm text-gray-600">{analysis.summary}</p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 px-4 py-3">
                    <p className="text-xs uppercase tracking-wide text-gray-500">Classificacao</p>
                    <p className="mt-1 text-lg font-semibold text-gray-900">{analysis.tier_label}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-medium text-slate-700">
                        {analysis.analysis_mode === 'DIAGNOSTIC' ? 'Modo diagnostico' : 'Modo otimizacao'}
                      </span>
                      <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700">
                        Confianca {analysis.confidence.toLowerCase()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 grid gap-4 md:grid-cols-2">
                  <div className="rounded-2xl border border-gray-200 p-5">
                    <p className="text-sm font-semibold text-gray-900">Comparacao com a media da conta</p>
                    <div className="mt-4 space-y-3 text-sm text-gray-600">
                      <div className="flex items-center justify-between gap-4">
                        <span>CTR da campanha</span>
                        <span className="font-medium text-gray-900">{formatPercent(analysis.benchmark.campaign_ctr)}</span>
                      </div>
                      <div className="flex items-center justify-between gap-4">
                        <span>CTR medio da conta</span>
                        <span className="font-medium text-gray-900">{formatPercent(analysis.benchmark.account_avg_ctr)}</span>
                      </div>
                      <div className="flex items-center justify-between gap-4">
                        <span>CPA da campanha</span>
                        <span className="font-medium text-gray-900">{formatCurrency(analysis.benchmark.campaign_cpa)}</span>
                      </div>
                      <div className="flex items-center justify-between gap-4">
                        <span>CPA medio da conta</span>
                        <span className="font-medium text-gray-900">{formatCurrency(analysis.benchmark.account_avg_cpa)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-2xl border border-gray-200 p-5">
                    <p className="text-sm font-semibold text-gray-900">O que faz mais sentido agora</p>
                    <div className="mt-4 space-y-3">
                      {analysis.next_steps.map((step) => (
                        <div key={step} className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-700">
                          {step}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold text-gray-900">Historico recente</h2>
                <p className="mt-2 text-sm text-gray-600">
                  Ultimos registros salvos da campanha, uteis para validar tendencia e impacto de mudancas.
                </p>
                <div className="mt-5 space-y-3">
                  {dailyData.length > 0 ? (
                    dailyData.map((item) => (
                      <div key={item.date} className="rounded-xl border border-gray-200 px-4 py-3">
                        <div className="flex items-center justify-between gap-4">
                          <p className="text-sm font-medium text-gray-900">
                            {new Date(item.date).toLocaleDateString('pt-BR')}
                          </p>
                          <p className="text-xs text-gray-500">
                            {item.clicks} cliques • {item.conversions.toFixed(2)} conv.
                          </p>
                        </div>
                        <div className="mt-2 flex items-center justify-between gap-4 text-sm text-gray-600">
                          <span>CTR {formatPercent(item.ctr)}</span>
                          <span>{formatCurrency(item.cost)}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-600">Ainda nao ha historico suficiente para esta campanha.</p>
                  )}
                </div>
              </div>
            </section>

            <div className="grid gap-4 lg:grid-cols-3">
              <InfoList title="Forcas" items={analysis.strengths} tone="good" />
              <InfoList title="Fragilidades" items={analysis.weaknesses} tone="warning" />
              <InfoList title="Oportunidades" items={analysis.opportunities} tone="neutral" />
            </div>

            <section className="rounded-2xl bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-gray-900">Acoes que o app pode preparar para voce</h2>
              <p className="mt-2 text-sm text-gray-600">
                Estas sugestoes sempre passam por proposta: primeiro entendemos, depois refinamos, e so entao voce aprova execucao ou automacao.
              </p>

              {recommendedActions.length > 0 ? (
                <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-wrap gap-2 text-xs font-medium">
                    <span className="rounded-full bg-slate-900 px-3 py-1 text-white">
                      {approveAndExecuteActions.length} prontas para aprovar e executar
                    </span>
                    <span className="rounded-full bg-white px-3 py-1 text-slate-700">
                      {automationActions.length} prontas para automatizar
                    </span>
                    <span className="rounded-full bg-white px-3 py-1 text-slate-700">
                      {planOnlyActions.length} em modo plano/manual
                    </span>
                  </div>

                  {approveAndExecuteActions.length === 0 ? (
                    <p className="mt-3 text-sm text-slate-700">
                      Nesta campanha ainda nao apareceu nenhuma proposta pronta para <span className="font-semibold">o app executar</span>.
                      Hoje a leitura ficou concentrada em diagnostico ou plano/manual.
                    </p>
                  ) : (
                    <p className="mt-3 text-sm text-slate-700">
                      Abra cada proposta para ver o contexto, entender o impacto e decidir se quer que o app execute.
                    </p>
                  )}
                </div>
              ) : null}

              <div className="mt-6 grid gap-4 lg:grid-cols-2">
                {recommendedActions.length > 0 ? (
                  recommendedActions.map((action) => (
                    <ProposalActionCard
                      key={`${action.type}-${action.title}`}
                      action={action}
                      onAfterChange={async () => {
                        await Promise.all([
                          mutateCampaign(),
                          mutateKeywords(),
                          mutateSearchTerms(),
                        ])
                      }}
                    />
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-gray-300 p-6 text-sm text-gray-600">
                    Nenhuma ordem especifica foi gerada para esta campanha neste momento.
                  </div>
                )}
              </div>
            </section>

            <section className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-2xl bg-white p-6 shadow-sm">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">Keywords</h2>
                    <p className="mt-2 text-sm text-gray-600">
                      {campaign.query_intelligence.keyword_count} keyword(s) sincronizada(s) para esta campanha.
                    </p>
                  </div>
                  <div className="rounded-2xl bg-gray-50 px-4 py-3 text-right">
                    <p className="text-xs uppercase tracking-wide text-gray-500">QS baixo</p>
                    <p className="mt-1 text-lg font-semibold text-gray-900">
                      {campaign.query_intelligence.low_quality_keyword_count}
                    </p>
                  </div>
                </div>

                <div className="mt-6 space-y-3">
                  {isKeywordsLoading ? (
                    <p className="text-sm text-gray-500">Carregando keywords...</p>
                  ) : keywords.length > 0 ? (
                    keywords.slice(0, 12).map((keyword: GoogleAdsQueryKeyword) => (
                      <div key={keyword.id} className="rounded-xl border border-gray-200 px-4 py-3">
                        <div className="flex items-center justify-between gap-4">
                          <p className="text-sm font-medium text-gray-900">{keyword.text}</p>
                          <span className={`rounded-full px-2 py-1 text-xs font-medium ${qualityBadge(keyword.quality_score)}`}>
                            QS {keyword.quality_score ?? '—'}
                          </span>
                        </div>
                        <div className="mt-2 flex items-center justify-between gap-4 text-sm text-gray-600">
                          <span>{keyword.match_type}</span>
                          <span>{formatCurrency(keyword.bid)}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-600">Ainda nao ha keywords sincronizadas para esta campanha.</p>
                  )}
                </div>
              </div>

              <div className="rounded-2xl bg-white p-6 shadow-sm">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">Search terms</h2>
                  <p className="mt-2 text-sm text-gray-600">
                    Termos reais acionando a campanha, uteis para negativar desperdicio ou promover vencedores.
                  </p>
                </div>

                <div className="mt-6 space-y-3">
                  {isSearchTermsLoading ? (
                    <p className="text-sm text-gray-500">Carregando search terms...</p>
                  ) : searchTerms.length > 0 ? (
                    searchTerms.slice(0, 12).map((term: GoogleAdsQuerySearchTerm) => {
                      const recommendation =
                        term.conversions > 0 ? 'Promover' : term.clicks >= 5 ? 'Revisar' : 'Monitorar'

                      return (
                        <div key={term.id} className="rounded-xl border border-gray-200 px-4 py-3">
                          <div className="flex items-center justify-between gap-4">
                            <p className="text-sm font-medium text-gray-900">{term.term}</p>
                            <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                              {recommendation}
                            </span>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-3 text-sm text-gray-600">
                            <span>{term.clicks} cliques</span>
                            <span>{term.conversions.toFixed(2)} conv.</span>
                            <span>{formatCurrency(term.cost)}</span>
                            <span>{term.match_type ?? '—'}</span>
                          </div>
                        </div>
                      )
                    })
                  ) : (
                    <p className="text-sm text-gray-600">Ainda nao ha search terms sincronizados para esta campanha.</p>
                  )}
                </div>
              </div>
            </section>

            <section className="rounded-2xl bg-white p-6 shadow-sm">
              <h2 className="text-xl font-semibold text-gray-900">Guardrails de operacao</h2>
              <p className="mt-2 text-sm text-gray-600">
                Regras para melhorar sem perder controle da conta durante ajustes de budget, copy e keywords.
              </p>
              <div className="mt-5 grid gap-3 md:grid-cols-3">
                {analysis.guardrails.map((guardrail) => (
                  <div key={guardrail} className="rounded-xl bg-gray-50 px-4 py-3 text-sm text-gray-700">
                    {guardrail}
                  </div>
                ))}
              </div>
            </section>
          </div>
        ) : null}
      </main>
    </div>
  )
}
