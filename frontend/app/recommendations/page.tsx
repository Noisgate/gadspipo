'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'

import { ProposalActionCard } from '@/components/recommendations/ProposalActionCard'
import { Header } from '@/components/dashboard/Header'
import { useAuth } from '@/contexts/auth'
import { useGoogleAdsCommandCenter } from '@/hooks/useCampaigns'
import { apiClient } from '@/lib/api-client'

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

function readinessLabel(readiness: 'LOW' | 'MEDIUM' | 'HIGH') {
  if (readiness === 'HIGH') return 'Ja existe base para otimizar'
  if (readiness === 'MEDIUM') return 'Ha sinal parcial, mas ainda faltam confirmacoes'
  return 'Primeiro precisamos validar entrega e tracking'
}

function stageTone(status: 'ok' | 'watch' | 'todo') {
  if (status === 'ok') return 'bg-emerald-100 text-emerald-700'
  if (status === 'watch') return 'bg-amber-100 text-amber-800'
  return 'bg-slate-100 text-slate-700'
}

function getCommandCenterNarrative({
  hasAccounts,
  readiness,
  approveCount,
}: {
  hasAccounts: boolean
  readiness?: 'LOW' | 'MEDIUM' | 'HIGH'
  approveCount: number
}) {
  if (!hasAccounts) {
    return {
      headline: 'Ainda nao temos conta conectada para analisar.',
      detail: 'Assim que a conta estiver conectada, esta tela passa a te mostrar gargalos, proximos passos e ideias de correcao.',
    }
  }

  if (readiness === 'LOW') {
    return {
      headline: 'O foco agora e entender por que a conta ainda nao esta pronta para otimizar.',
      detail: 'Antes de discutir lances e escala, o fluxo xquads manda validar entrega, tracking e estrutura da conta.',
    }
  }

  if (approveCount > 0) {
    return {
      headline: 'Ja existe material suficiente para tomar decisoes guiadas.',
      detail: 'O sistema ja montou propostas que podem ser discutidas e aprovadas antes de qualquer execucao.',
    }
  }

  return {
    headline: 'Estamos em modo de leitura e organizacao da operacao.',
    detail: 'A conta tem alguns sinais, mas ainda vale reforcar entendimento antes de acelerar mudancas.',
  }
}

export default function RecommendationsPage() {
  const router = useRouter()
  const { token, isInitialized } = useAuth()
  const { commandCenter, isLoading, isError, error, mutate } = useGoogleAdsCommandCenter()
  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    if (isInitialized && !token) {
      router.push('/login')
    }
  }, [token, isInitialized, router])

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true)
      const response = await apiClient.refreshGoogleAdsCommandCenter()
      await mutate(response.data, { revalidate: false })
      toast.success('Google Ads atualizado com sucesso')
    } catch (refreshError: any) {
      toast.error(apiClient.getErrorMessage(refreshError))
    } finally {
      setIsRefreshing(false)
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

  const summary = commandCenter?.summary
  const audit = commandCenter?.account_audit
  const performance = commandCenter?.performance_analysis
  const budget = commandCenter?.budget_optimization
  const tracking = commandCenter?.tracking_setup
  const scaling = commandCenter?.scaling_plan
  const strategy = commandCenter?.strategy_blueprint
  const queryIntelligence = commandCenter?.query_intelligence
  const automations = commandCenter?.automations ?? []
  const recommendedActions = commandCenter?.recommended_actions ?? []
  const approveAndExecuteActions = recommendedActions.filter((action) =>
    action.execution_modes.includes('approve_and_execute')
  )
  const automationActions = recommendedActions.filter((action) =>
    action.execution_modes.includes('create_automation')
  )
  const planOnlyActions = recommendedActions.filter((action) =>
    action.execution_modes.includes('plan_only')
  )
  const narrative = getCommandCenterNarrative({
    hasAccounts: commandCenter?.connected_accounts.length ? commandCenter.connected_accounts.length > 0 : false,
    readiness: summary?.measurement_readiness,
    approveCount: approveAndExecuteActions.length,
  })
  const xquadsWorkflow = [
    {
      title: 'Diagnosticar e auditar',
      description: 'Entender se o problema esta em entrega, estrutura, busca ou medicao.',
      source: '*diagnose, *audit-ad-account',
      status: !commandCenter?.connected_accounts.length
        ? 'todo'
        : summary?.measurement_readiness === 'LOW'
        ? 'watch'
        : 'ok',
    },
    {
      title: 'Validar tracking',
      description: 'Confirmar se o app realmente esta vendo o resultado final da campanha.',
      source: '*setup-tracking',
      status:
        tracking?.status === 'ready'
          ? 'ok'
          : summary?.measurement_readiness === 'LOW'
          ? 'watch'
          : 'todo',
    },
    {
      title: 'Organizar estrutura e busca',
      description: 'Separar intencao, keywords e negativos para a conta ficar mais assertiva.',
      source: 'Kasim Aslam, query intelligence',
      status: strategy?.gaps.length ? 'watch' : 'ok',
    },
    {
      title: 'Criar ou corrigir campanha',
      description: 'Montar campanha nova, copy, criativos e plano de lancamento guiado.',
      source: 'campaign-launch, create-ad-strategy, create-ad-creative',
      status: 'ok',
    },
    {
      title: 'Otimizar e escalar',
      description: 'So entra forte quando ha sinal de entrega, conversao e medicao confiavel.',
      source: '*analyze-performance, *manage-budget, *scale-campaign',
      status:
        summary?.measurement_readiness === 'HIGH' && (summary?.conversions ?? 0) > 0
          ? 'ok'
          : 'todo',
    },
  ] as const

  return (
    <div className="min-h-screen bg-stone-50">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <section className="rounded-[32px] bg-gradient-to-br from-slate-900 via-slate-800 to-amber-700 p-8 text-white shadow-lg">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs uppercase tracking-[0.3em] text-white/60">Central de decisao</p>
              <h1 className="mt-4 text-3xl font-semibold sm:text-4xl">O app pensa com xquads e te explica em portugues claro</h1>
              <p className="mt-4 text-sm leading-6 text-white/80 sm:text-base">
                Esta tela junta os playbooks do Traffic Masters, Kasim Aslam e os fluxos de tracking,
                budget e escala para te mostrar o que esta acontecendo e qual e o proximo passo mais seguro.
              </p>
            </div>

            <button
              type="button"
              onClick={handleRefresh}
              disabled={isRefreshing || !commandCenter?.connected_accounts.length}
              className="inline-flex items-center justify-center rounded-2xl bg-white px-5 py-3 text-sm font-semibold text-slate-900 shadow-sm transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isRefreshing ? 'Atualizando...' : 'Atualizar leitura do Google Ads'}
            </button>
          </div>

          <div className="mt-8 grid gap-4 xl:grid-cols-[1.3fr,0.9fr]">
            <div className="rounded-[28px] bg-white/10 p-6 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.24em] text-white/60">Leitura principal</p>
              <p className="mt-3 text-2xl font-semibold">{narrative.headline}</p>
              <p className="mt-3 text-sm text-white/80">{narrative.detail}</p>
            </div>
            <div className="rounded-[28px] bg-white/10 p-6 backdrop-blur">
              <p className="text-xs uppercase tracking-[0.24em] text-white/60">O que o app faz aqui</p>
              <div className="mt-4 space-y-2 text-sm text-white/80">
                <p>1. Diagnostica a conta e a campanha</p>
                <p>2. Monta sugestoes com risco e impacto</p>
                <p>3. Voce discute e ajusta</p>
                <p>4. O app executa por API quando fizer sentido</p>
              </div>
            </div>
          </div>
        </section>

        {isLoading ? (
          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[...Array(4)].map((_, index) => (
              <div key={index} className="rounded-xl bg-white p-6 shadow animate-pulse">
                <div className="h-4 w-24 rounded bg-gray-200" />
                <div className="mt-4 h-8 w-32 rounded bg-gray-200" />
              </div>
            ))}
          </div>
        ) : null}

        {isError ? (
          <div className="rounded-xl bg-white p-6 shadow">
            <p className="font-medium text-red-600">Nao foi possivel carregar o command center.</p>
            <p className="mt-2 text-sm text-gray-600">{error}</p>
          </div>
        ) : null}

        {!isLoading && !isError && commandCenter && (
          <div className="space-y-8">
            {!commandCenter.connected_accounts.length ? (
              <div className="rounded-xl bg-white p-8 shadow">
                <h2 className="text-xl font-semibold text-gray-900">Nenhuma conta conectada</h2>
                <p className="mt-3 text-gray-600">
                  Conecte uma conta do Google Ads para habilitar auditoria, analise de performance,
                  tracking, budget e planos de escala.
                </p>
              </div>
            ) : (
              <>
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-[24px] bg-white p-6 shadow-sm">
                    <p className="text-sm font-medium text-slate-500">Contas conectadas</p>
                    <p className="mt-2 text-3xl font-semibold text-slate-900">{summary?.account_count ?? 0}</p>
                  </div>
                  <div className="rounded-[24px] bg-white p-6 shadow-sm">
                    <p className="text-sm font-medium text-slate-500">Campanhas ativas</p>
                    <p className="mt-2 text-3xl font-semibold text-slate-900">{summary?.active_campaign_count ?? 0}</p>
                  </div>
                  <div className="rounded-[24px] bg-white p-6 shadow-sm">
                    <p className="text-sm font-medium text-slate-500">Gasto 30 dias</p>
                    <p className="mt-2 text-3xl font-semibold text-slate-900">{formatCurrency(summary?.cost)}</p>
                  </div>
                  <div className="rounded-[24px] bg-white p-6 shadow-sm">
                    <p className="text-sm font-medium text-slate-500">Momento da operacao</p>
                    <p className="mt-2 text-lg font-semibold text-slate-900">
                      {summary ? readinessLabel(summary.measurement_readiness) : '—'}
                    </p>
                    <p className="mt-2 text-sm text-slate-500">
                      CTR {formatPercent(summary?.avg_ctr)} • CPA {formatCurrency(summary?.avg_cpa)}
                    </p>
                  </div>
                </div>

                <section className="rounded-[28px] bg-white p-6 shadow-sm">
                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div>
                      <h2 className="text-xl font-semibold text-slate-900">Como o app usa o xquads</h2>
                      <p className="text-sm text-slate-600">
                        Em vez de te jogar jargao tecnico, organizamos os playbooks em etapas de decisao.
                      </p>
                    </div>
                    <p className="text-sm text-slate-500">
                      Lead metodologico: {commandCenter.methodology.google_ads_lead}
                    </p>
                  </div>

                  <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                    {xquadsWorkflow.map((stage) => (
                      <div key={stage.title} className="rounded-[24px] border border-slate-200 p-4">
                        <span className={`rounded-full px-3 py-1 text-xs font-medium ${stageTone(stage.status)}`}>
                          {stage.status === 'ok' ? 'Em uso agora' : stage.status === 'watch' ? 'Pede atencao' : 'Entra depois'}
                        </span>
                        <h3 className="mt-4 text-base font-semibold text-slate-900">{stage.title}</h3>
                        <p className="mt-2 text-sm text-slate-600">{stage.description}</p>
                        <p className="mt-4 text-xs uppercase tracking-[0.24em] text-slate-400">
                          {stage.source}
                        </p>
                      </div>
                    ))}
                  </div>

                  <div className="mt-6 flex flex-wrap gap-2">
                    {commandCenter.capabilities.map((capability) => (
                      <span
                        key={capability.id}
                        className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600"
                      >
                        {capability.label}
                      </span>
                    ))}
                  </div>
                </section>

                {audit && (
                  <section className="rounded-xl bg-white p-6 shadow">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900">Auditoria da conta</h2>
                        <p className="text-sm text-gray-600">
                          Scorecard baseado no workflow `account-audit` do Traffic Masters.
                        </p>
                      </div>
                      <div className="rounded-xl bg-gray-50 px-5 py-4 text-right">
                        <p className="text-sm text-gray-500">Health score</p>
                        <p className="text-3xl font-semibold text-gray-900">{audit.health_score}/80</p>
                        <p className="text-sm text-gray-500">{audit.health_label}</p>
                      </div>
                    </div>

                    <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                      {audit.dimensions.map((dimension) => (
                        <div key={dimension.name} className="rounded-lg border border-gray-200 p-4">
                          <div className="flex items-center justify-between gap-3">
                            <h3 className="font-medium text-gray-900">{dimension.name}</h3>
                            <span className="text-sm font-semibold text-gray-700">{dimension.score}/10</span>
                          </div>
                          <p className="mt-2 text-sm text-gray-600">{dimension.note}</p>
                          <p className="mt-3 text-xs uppercase tracking-wide text-gray-400">
                            {dimension.status}
                          </p>
                        </div>
                      ))}
                    </div>

                    <div className="mt-6 grid gap-4 md:grid-cols-3">
                      <div className="rounded-lg bg-red-50 p-4">
                        <p className="text-sm font-medium text-red-700">Wasted spend</p>
                        <p className="mt-2 text-2xl font-semibold text-red-900">
                          {formatCurrency(audit.wasted_spend)}
                        </p>
                        <p className="mt-1 text-sm text-red-700">
                          {formatPercent(audit.wasted_spend_share)} do investimento
                        </p>
                      </div>
                      <div className="rounded-lg bg-emerald-50 p-4">
                        <p className="text-sm font-medium text-emerald-700">Winners</p>
                        <p className="mt-2 text-2xl font-semibold text-emerald-900">
                          {audit.campaign_tiers.winners}
                        </p>
                      </div>
                      <div className="rounded-lg bg-amber-50 p-4">
                        <p className="text-sm font-medium text-amber-700">Sob atencao</p>
                        <p className="mt-2 text-2xl font-semibold text-amber-900">
                          {audit.campaign_tiers.underperformers + audit.campaign_tiers.zombies}
                        </p>
                      </div>
                    </div>

                    <div className="mt-6 space-y-2">
                      {audit.top_findings.map((finding) => (
                        <div key={finding} className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700">
                          {finding}
                        </div>
                      ))}
                    </div>
                  </section>
                )}

                {recommendedActions.length > 0 && (
                  <section className="rounded-[28px] bg-white p-6 shadow-sm">
                    <h2 className="text-xl font-semibold text-slate-900">O que o sistema recomenda agora</h2>
                    <p className="mt-1 text-sm text-slate-600">
                      Estas sao as sugestoes mais importantes neste momento, com proposta, risco e espaco para conversa antes de qualquer execucao.
                    </p>

                    <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
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
                          Hoje a conta nao recebeu nenhuma proposta pronta para <span className="font-semibold">Aprovar para o app executar</span>.
                          Isso normalmente significa que ainda precisamos confirmar melhor o diagnostico antes de mexer na conta.
                        </p>
                      ) : (
                        <p className="mt-3 text-sm text-slate-700">
                          Cada card abre uma leitura guiada: o que esta errado, por que sugerimos isso e o que acontecera se voce aprovar.
                        </p>
                      )}
                    </div>

                    <div className="mt-6 grid gap-4 lg:grid-cols-2">
                      {recommendedActions.map((action) => (
                        <ProposalActionCard
                          key={`${action.type}-${action.title}`}
                          action={action}
                          onAfterChange={async () => {
                            await mutate()
                          }}
                        />
                      ))}
                    </div>
                  </section>
                )}

                <div className="grid gap-8 xl:grid-cols-[1.2fr,0.8fr]">
                  {performance && (
                    <section className="rounded-[28px] bg-white p-6 shadow-sm">
                      <h2 className="text-xl font-semibold text-slate-900">O que os dados mostram</h2>
                      <p className="mt-1 text-sm text-slate-600">
                        Leitura dos ultimos {performance.period_days} dias para entender o que esta reagindo e o que ainda nao ganhou tracao.
                      </p>

                      <div className="mt-6 grid gap-4 md:grid-cols-3">
                        <div className="rounded-lg bg-gray-50 p-4">
                          <p className="text-sm text-gray-500">Conversoes</p>
                          <p className="mt-2 text-2xl font-semibold text-gray-900">
                            {performance.metrics.conversions.toFixed(2)}
                          </p>
                        </div>
                        <div className="rounded-lg bg-gray-50 p-4">
                          <p className="text-sm text-gray-500">CTR medio</p>
                          <p className="mt-2 text-2xl font-semibold text-gray-900">
                            {formatPercent(performance.metrics.avg_ctr)}
                          </p>
                        </div>
                        <div className="rounded-lg bg-gray-50 p-4">
                          <p className="text-sm text-gray-500">CPA medio</p>
                          <p className="mt-2 text-2xl font-semibold text-gray-900">
                            {formatCurrency(performance.metrics.avg_cpa)}
                          </p>
                        </div>
                      </div>

                      <div className="mt-6 space-y-3">
                        {performance.insights.map((insight) => (
                          <div key={insight.title} className="rounded-lg border border-gray-200 p-4">
                            <p className="font-medium text-gray-900">{insight.title}</p>
                            <p className="mt-1 text-sm text-gray-600">{insight.detail}</p>
                          </div>
                        ))}
                      </div>

                      <div className="mt-6">
                        <h3 className="font-semibold text-slate-900">Plano sugerido para os proximos 7 dias</h3>
                        <div className="mt-3 space-y-2">
                          {performance.action_plan.map((step) => (
                            <div key={step} className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700">
                              {step}
                            </div>
                          ))}
                        </div>
                      </div>
                    </section>
                  )}

                  <div className="space-y-8">
                    {budget && (
                      <section className="rounded-[28px] bg-white p-6 shadow-sm">
                        <h2 className="text-xl font-semibold text-slate-900">Quanto faz sentido investir</h2>
                        <p className="mt-1 text-sm text-slate-600">
                          Cenarios para nao mexer no budget no escuro e realocacoes sugeridas quando fizer sentido.
                        </p>

                        <div className="mt-6 space-y-3">
                          {budget.scenarios.map((scenario) => (
                            <div key={scenario.name} className="rounded-lg border border-gray-200 p-4">
                              <div className="flex items-center justify-between gap-3">
                                <p className="font-medium text-gray-900">{scenario.name}</p>
                                <p className="text-sm text-gray-500">{formatCurrency(scenario.budget)}</p>
                              </div>
                              <p className="mt-2 text-sm text-gray-600">
                                CPA projetado {formatCurrency(scenario.projected_cpa)} • conversoes projetadas {scenario.projected_conversions}
                              </p>
                            </div>
                          ))}
                        </div>

                        {budget.recommended_reallocation.length > 0 && (
                          <div className="mt-6">
                            <h3 className="font-semibold text-slate-900">Mudanca de verba sugerida</h3>
                            <div className="mt-3 space-y-3">
                              {budget.recommended_reallocation.map((item) => (
                                <div key={`${item.from_campaign}-${item.to_campaign}`} className="rounded-lg bg-gray-50 p-4">
                                  <p className="font-medium text-gray-900">
                                    {item.from_campaign} → {item.to_campaign}
                                  </p>
                                  <p className="mt-1 text-sm text-gray-600">
                                    {formatCurrency(item.shift_amount)} • {item.rationale}
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </section>
                    )}

                    {tracking && (
                      <section className="rounded-[28px] bg-white p-6 shadow-sm">
                        <h2 className="text-xl font-semibold text-slate-900">O que precisa estar medido</h2>
                        <p className="mt-1 text-sm text-slate-600">{tracking.summary}</p>

                        <div className="mt-6 space-y-2">
                          {tracking.checklist.map((item) => (
                            <div key={item.label} className="flex items-start gap-3 rounded-lg border border-gray-200 p-3">
                              <span className={`mt-0.5 inline-flex h-2.5 w-2.5 rounded-full ${item.status === 'done' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                              <p className="text-sm text-gray-700">{item.label}</p>
                            </div>
                          ))}
                        </div>
                      </section>
                    )}
                  </div>
                </div>

                {queryIntelligence && (
                  <div className="grid gap-8 xl:grid-cols-2">
                    <section className="rounded-[28px] bg-white p-6 shadow-sm">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <h2 className="text-xl font-semibold text-slate-900">Palavras que voce comprou</h2>
                          <p className="mt-1 text-sm text-slate-600">
                            Termos configurados na conta, com foco em qualidade e controle.
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-500">Total</p>
                          <p className="text-2xl font-semibold text-gray-900">{queryIntelligence.keyword_count}</p>
                        </div>
                      </div>

                      <div className="mt-4 rounded-lg bg-amber-50 p-4">
                        <p className="text-sm font-medium text-amber-700">Baixa qualidade</p>
                        <p className="mt-1 text-2xl font-semibold text-amber-900">
                          {queryIntelligence.low_quality_keyword_count}
                        </p>
                      </div>

                      <div className="mt-6 space-y-3">
                        {queryIntelligence.top_keywords.length > 0 ? (
                          queryIntelligence.top_keywords.map((keyword) => (
                            <div key={keyword.id} className="rounded-lg border border-gray-200 p-4">
                              <div className="flex items-center justify-between gap-3">
                                <p className="font-medium text-gray-900">{keyword.text}</p>
                                <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700">
                                  QS {keyword.quality_score ?? '—'}
                                </span>
                              </div>
                              <p className="mt-2 text-sm text-gray-600">
                                {keyword.match_type} • {keyword.campaign_name}
                              </p>
                            </div>
                          ))
                        ) : (
                          <div className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-600">
                            Ainda nao ha keywords sincronizadas para exibir.
                          </div>
                        )}
                      </div>
                    </section>

                    <section className="rounded-[28px] bg-white p-6 shadow-sm">
                      <h2 className="text-xl font-semibold text-slate-900">O que as pessoas realmente pesquisaram</h2>
                      <p className="mt-1 text-sm text-slate-600">
                        Estes termos ajudam a decidir o que deve virar keyword controlada e o que deveria ser bloqueado.
                      </p>

                      <div className="mt-6 space-y-3">
                        {queryIntelligence.top_search_terms.length > 0 ? (
                          queryIntelligence.top_search_terms.map((term) => (
                            <div key={term.id} className="rounded-lg border border-gray-200 p-4">
                              <div className="flex items-center justify-between gap-3">
                                <p className="font-medium text-gray-900">{term.term}</p>
                                <span className="text-sm text-gray-500">
                                  {formatCurrency(term.cost)}
                                </span>
                              </div>
                              <p className="mt-2 text-sm text-gray-600">
                                {term.campaign_name} • {term.clicks} cliques • {term.conversions.toFixed(2)} conversoes
                              </p>
                            </div>
                          ))
                        ) : (
                          <div className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-600">
                            Ainda nao ha search terms sincronizados para exibir.
                          </div>
                        )}
                      </div>
                    </section>
                  </div>
                )}

                <div className="grid gap-8 xl:grid-cols-2">
                  {scaling && (
                    <section className="rounded-[28px] bg-white p-6 shadow-sm">
                      <h2 className="text-xl font-semibold text-slate-900">Quando vale escalar</h2>
                      <p className="mt-1 text-sm text-slate-600">{scaling.summary}</p>

                      <div className="mt-4 rounded-lg bg-gray-50 p-4">
                        <p className="text-sm text-gray-500">Metodo recomendado</p>
                        <p className="mt-1 text-lg font-semibold text-gray-900">{scaling.recommended_method}</p>
                      </div>

                      {scaling.eligible_campaigns.length > 0 && (
                        <div className="mt-6">
                          <h3 className="font-semibold text-gray-900">Campanhas elegiveis</h3>
                          <div className="mt-3 space-y-3">
                            {scaling.eligible_campaigns.map((campaign) => (
                              <div key={campaign.campaign_id} className="rounded-lg border border-gray-200 p-4">
                                <p className="font-medium text-gray-900">{campaign.name}</p>
                                <p className="mt-1 text-sm text-gray-600">
                                  CTR {formatPercent(campaign.avg_ctr)} • CPA {formatCurrency(campaign.avg_cpa)}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-6">
                        <h3 className="font-semibold text-gray-900">Guardrails</h3>
                        <div className="mt-3 space-y-2">
                          {scaling.guardrails.map((guardrail) => (
                            <div key={guardrail} className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700">
                              {guardrail}
                            </div>
                          ))}
                        </div>
                      </div>
                    </section>
                  )}

                  {strategy && (
                    <section className="rounded-[28px] bg-white p-6 shadow-sm">
                      <h2 className="text-xl font-semibold text-slate-900">Estrutura recomendada da conta</h2>
                      <p className="mt-1 text-sm text-slate-600">{strategy.framework}</p>

                      <div className="mt-6 grid gap-3 sm:grid-cols-2">
                        {Object.entries(strategy.current_mix).map(([key, enabled]) => (
                          <div key={key} className="rounded-lg border border-gray-200 p-4">
                            <p className="font-medium text-gray-900">{key}</p>
                            <p className="mt-1 text-sm text-gray-600">
                              {enabled ? 'Ja existe sinal dessa camada na conta' : 'Gap identificado'}
                            </p>
                          </div>
                        ))}
                      </div>

                      {strategy.gaps.length > 0 && (
                        <div className="mt-6">
                          <h3 className="font-semibold text-slate-900">O que ainda esta faltando</h3>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {strategy.gaps.map((gap) => (
                              <span key={gap} className="rounded-full bg-amber-100 px-3 py-1 text-sm text-amber-800">
                                {gap}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-6">
                        <h3 className="font-semibold text-slate-900">Principios do playbook</h3>
                        <div className="mt-3 space-y-2">
                          {strategy.principles.map((principle) => (
                            <div key={principle} className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700">
                              {principle}
                            </div>
                          ))}
                        </div>
                      </div>
                    </section>
                  )}
                </div>

                <section className="rounded-[28px] bg-white p-6 shadow-sm">
                  <h2 className="text-xl font-semibold text-slate-900">O que ja ficou automatico</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Regras salvas a partir das recomendacoes que voce ja revisou.
                  </p>

                  <div className="mt-6 grid gap-4 md:grid-cols-2">
                    {automations.length > 0 ? (
                      automations.map((automation) => (
                        <div key={automation.id} className="rounded-lg border border-gray-200 p-4">
                          <div className="flex items-center justify-between gap-3">
                            <p className="font-medium text-gray-900">{automation.name}</p>
                            <span className={`rounded-full px-2 py-1 text-xs font-medium ${automation.enabled ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-700'}`}>
                              {automation.enabled ? 'Ativa' : 'Inativa'}
                            </span>
                          </div>
                          <p className="mt-2 text-sm text-gray-600">{automation.rule_type}</p>
                          <p className="mt-2 text-xs uppercase tracking-wide text-gray-400">
                            Criada em {new Date(automation.created_at).toLocaleString('pt-BR')}
                          </p>
                        </div>
                      ))
                    ) : (
                      <div className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-600">
                        Nenhuma automacao salva ainda.
                      </div>
                    )}
                  </div>
                </section>
              </>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
