'use client'

import React, { useState } from 'react'
import { toast } from 'sonner'

import { apiClient } from '@/lib/api-client'
import { GoogleAdsActionRecommendation, RecommendationProposal } from '@/types'

function formatImpact(value?: number | null) {
  if (value === null || value === undefined) {
    return '—'
  }

  return new Intl.NumberFormat('pt-BR', {
    maximumFractionDigits: 2,
  }).format(value)
}

function confidenceTone(confidence: RecommendationProposal['confidence']) {
  if (confidence === 'HIGH') return 'bg-emerald-50 text-emerald-700'
  if (confidence === 'MEDIUM') return 'bg-amber-50 text-amber-700'
  return 'bg-rose-50 text-rose-700'
}

function analysisTone(mode: RecommendationProposal['analysis_mode']) {
  return mode === 'OPTIMIZATION'
    ? 'bg-sky-50 text-sky-700'
    : 'bg-slate-100 text-slate-700'
}

function actionModeCopy(action: GoogleAdsActionRecommendation) {
  if (action.execution_modes.includes('approve_and_execute')) {
    return 'Se voce aprovar, o app consegue aplicar essa mudanca por API.'
  }

  if (action.execution_modes.includes('create_automation')) {
    return 'Esta sugestao pode virar uma automacao para rodar depois.'
  }

  return 'Esta sugestao ainda precisa de conversa ou trabalho manual antes de executar.'
}

function buttonLabel(action: GoogleAdsActionRecommendation, isOpen: boolean, isLoading: boolean) {
  if (isLoading) return 'Montando proposta...'
  if (isOpen) return 'Fechar leitura'
  if (action.execution_modes.includes('approve_and_execute')) return 'Entender proposta'
  if (action.execution_modes.includes('create_automation')) return 'Revisar automacao'
  return 'Entender plano'
}

function ListBlock({
  title,
  items,
}: {
  title: string
  items: string[]
}) {
  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-4">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</h4>
      <div className="mt-3 space-y-2">
        {items.length > 0 ? (
          items.map((item) => (
            <div key={item} className="rounded-xl bg-gray-50 px-3 py-2 text-sm text-gray-700">
              {item}
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500">Nenhum item nesta etapa.</p>
        )}
      </div>
    </div>
  )
}

export function ProposalActionCard({
  action,
  onAfterChange,
}: {
  action: GoogleAdsActionRecommendation
  onAfterChange?: () => Promise<void> | void
}) {
  const [proposal, setProposal] = useState<RecommendationProposal | null>(null)
  const [notes, setNotes] = useState('')
  const [isOpen, setIsOpen] = useState(false)
  const [isLoadingProposal, setIsLoadingProposal] = useState(false)
  const [activeAction, setActiveAction] = useState<string | null>(null)
  const [proposalNotesSnapshot, setProposalNotesSnapshot] = useState('')

  const handleLoadProposal = async (notesOverride?: string) => {
    const effectiveNotes = (notesOverride ?? notes).trim()
    try {
      setIsLoadingProposal(true)
      const response = await apiClient.getGoogleAdsActionProposal({
        action_type: action.type,
        title: action.title,
        description: action.description,
        priority: action.priority,
        campaign_id: action.campaign_id,
        campaign_name: action.campaign_name,
        action_payload: action.action_payload,
        notes: effectiveNotes,
      })
      setProposal(response)
      setProposalNotesSnapshot(effectiveNotes)
      setIsOpen(true)
      return response as RecommendationProposal
    } catch (error: any) {
      toast.error(apiClient.getErrorMessage(error))
      return null
    } finally {
      setIsLoadingProposal(false)
    }
  }

  const ensureFreshProposal = async () => {
    const effectiveNotes = notes.trim()
    if (!proposal || effectiveNotes !== proposalNotesSnapshot) {
      return handleLoadProposal(effectiveNotes)
    }

    return proposal
  }

  const handleApprove = async () => {
    const proposalData = await ensureFreshProposal()
    if (!proposalData) {
      return
    }

    try {
      setActiveAction('approve_and_execute')
      const response = await apiClient.executeGoogleAdsAction({
        action_type: action.type,
        title: proposalData.refined_action.title,
        description: proposalData.refined_action.description,
        priority: action.priority,
        campaign_id: action.campaign_id,
        campaign_name: action.campaign_name,
        action_payload: proposalData.refined_action.action_payload,
        execution_mode: 'approve_and_execute',
        approval_note: notes || undefined,
      })
      toast.success(response.message)
      await onAfterChange?.()
    } catch (error: any) {
      toast.error(apiClient.getErrorMessage(error))
    } finally {
      setActiveAction(null)
    }
  }

  const handleCreateAutomation = async () => {
    const proposalData = await ensureFreshProposal()
    if (!proposalData) {
      return
    }

    try {
      setActiveAction('create_automation')
      const response = await apiClient.executeGoogleAdsAction({
        action_type: action.type,
        title: proposalData.refined_action.title,
        description: proposalData.refined_action.description,
        priority: action.priority,
        campaign_id: action.campaign_id,
        campaign_name: action.campaign_name,
        action_payload: proposalData.refined_action.action_payload,
        execution_mode: 'create_automation',
        approval_note: notes || undefined,
      })
      toast.success(response.message)
      await onAfterChange?.()
    } catch (error: any) {
      toast.error(apiClient.getErrorMessage(error))
    } finally {
      setActiveAction(null)
    }
  }

  const hasPendingNotes = notes.trim() !== proposalNotesSnapshot

  return (
    <div className="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Acao sugerida</p>
          <h3 className="mt-2 text-lg font-semibold text-slate-900">{action.title}</h3>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
          {action.priority}
        </span>
      </div>

      <p className="mt-3 text-sm text-slate-600">{action.description}</p>
      <p className="mt-3 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-700">
        {actionModeCopy(action)}
      </p>

      {action.campaign_name ? (
        <p className="mt-3 text-sm text-slate-500">Campanha: {action.campaign_name}</p>
      ) : null}

      {action.estimated_impact ? (
        <p className="mt-3 text-sm text-slate-500">
          Impacto esperado em <span className="font-medium">{action.estimated_impact.metric}</span>:{' '}
          {formatImpact(action.estimated_impact.current)} → {formatImpact(action.estimated_impact.projected)}
        </p>
      ) : null}

      <p className="mt-3 text-xs uppercase tracking-wide text-slate-400">Origem: {action.source}</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {action.execution_modes.includes('approve_and_execute') ? (
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
            O app pode executar por API
          </span>
        ) : null}
        {action.execution_modes.includes('create_automation') ? (
          <span className="rounded-full bg-sky-50 px-3 py-1 text-xs font-medium text-sky-700">
            Pode virar automacao
          </span>
        ) : null}
        {action.execution_modes.includes('plan_only') ? (
          <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-800">
            Ainda precisa de conversa
          </span>
        ) : null}
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => {
            if (isOpen) {
              setIsOpen(false)
              return
            }
            void handleLoadProposal()
          }}
          disabled={isLoadingProposal}
          className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {buttonLabel(action, isOpen, isLoadingProposal)}
        </button>
      </div>

      {isOpen && proposal ? (
        <div className="mt-5 space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex flex-wrap gap-2">
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${analysisTone(proposal.analysis_mode)}`}>
              {proposal.analysis_mode === 'DIAGNOSTIC' ? 'Modo diagnostico' : 'Modo otimizacao'}
            </span>
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${confidenceTone(proposal.confidence)}`}>
              Confianca {proposal.confidence.toLowerCase()}
            </span>
            <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700">
              {proposal.ai_metadata.used_ai ? 'Refino com IA' : 'Refino por regras'}
            </span>
          </div>

          <div className="rounded-2xl bg-white p-4">
            <h4 className="text-sm font-semibold text-slate-900">{proposal.proposal_title}</h4>
            <p className="mt-2 text-sm text-slate-700">{proposal.summary}</p>
            {proposal.refinement_summary ? (
              <p className="mt-3 rounded-xl bg-slate-50 px-3 py-2 text-sm text-slate-700">
                {proposal.refinement_summary}
              </p>
            ) : null}
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <ListBlock title="O que voce pediu" items={proposal.feedback_notes} />
            <ListBlock title="O que aplicamos" items={proposal.applied_feedback} />
            <ListBlock title="O que ainda depende de conversa" items={proposal.pending_feedback} />
            <ListBlock title="Leitura de dados" items={proposal.data_notes} />
            <ListBlock title="Por que esta proposta" items={proposal.why_this_proposal} />
            <ListBlock title="O que foi corrigido nesta versao" items={proposal.change_highlights} />
            <ListBlock title="Mudancas sugeridas" items={proposal.suggested_changes} />
            <ListBlock title="Riscos" items={proposal.risks} />
            <ListBlock title="Checklist antes de aprovar" items={proposal.preflight_checklist} />
            <ListBlock title="Pontos para discutirmos" items={proposal.discussion_points} />
            <ListBlock title="Sinais de sucesso" items={proposal.success_signals} />
            <ListBlock title="Checklist de aprovacao" items={proposal.approval_checklist} />
          </div>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">
              O que voce quer que o app mude antes de aprovar?
            </span>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={4}
              placeholder="Ex.: quero uma versao mais conservadora, sem ampliar budget agora; prefiro phrase match; vamos separar branded antes."
              className="mt-2 w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm text-gray-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200"
            />
          </label>

          {hasPendingNotes ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              Seu feedback mudou desde a ultima versao da proposta. Se voce aprovar agora, o sistema primeiro vai
              atualizar a proposta com esse texto e so depois executar.
            </div>
          ) : null}

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void handleLoadProposal(notes)}
              disabled={isLoadingProposal}
              className="rounded-xl border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoadingProposal ? 'Refinando...' : 'Pedir ajuste'}
            </button>

            {action.execution_modes.includes('approve_and_execute') ? (
              <button
                type="button"
                onClick={() => void handleApprove()}
                disabled={
                  activeAction === 'approve_and_execute' ||
                  isLoadingProposal ||
                  proposal.refined_action.recommended_execution_mode !== 'approve_and_execute'
                }
                className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {activeAction === 'approve_and_execute'
                  ? 'Executando...'
                  : proposal.refined_action.recommended_execution_mode !== 'approve_and_execute'
                  ? 'Ainda precisa de conversa'
                  : 'Aprovar para o app executar'}
              </button>
            ) : null}

            {action.execution_modes.includes('create_automation') ? (
              <button
                type="button"
                onClick={() => void handleCreateAutomation()}
                disabled={activeAction === 'create_automation' || isLoadingProposal}
                className="rounded-xl bg-sky-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {activeAction === 'create_automation' ? 'Criando...' : 'Deixar automatico depois'}
              </button>
            ) : null}

            {action.execution_modes.includes('plan_only') ? (
              <span className="rounded-xl bg-amber-50 px-4 py-2 text-sm font-medium text-amber-800">
                Este item fica como proposta manual.
              </span>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  )
}
