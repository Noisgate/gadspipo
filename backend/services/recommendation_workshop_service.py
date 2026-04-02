"""
Recommendation workshop service.

Transforms raw Google Ads actions into proposal-first payloads so the user can
discuss, refine, and only then approve execution.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any
import unicodedata
from uuid import UUID

from sqlalchemy.orm import Session

from integrations.openai_client import openai_client
from models.database import Campaign, GoogleAdsAccount
from models.schemas import RecommendationProposalRequest
from services.google_ads_command_center import google_ads_command_center_service


class RecommendationWorkshopService:
    """Builds discussion-ready proposals around Google Ads actions."""

    def build_proposal(
        self,
        user_id: UUID,
        request: RecommendationProposalRequest,
        db: Session,
    ) -> dict[str, Any]:
        command_center = google_ads_command_center_service.build(user_id, db)
        summary = command_center["summary"]

        campaign = None
        campaign_detail = None
        if request.campaign_id:
            campaign = (
                db.query(Campaign)
                .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
                .filter(
                    GoogleAdsAccount.user_id == user_id,
                    Campaign.id == request.campaign_id,
                )
                .first()
            )
            if campaign:
                campaign_detail = google_ads_command_center_service.build_campaign_detail(
                    user_id=user_id,
                    campaign_id=campaign.id,
                    db=db,
                )

        analysis_mode = self._analysis_mode(summary, campaign_detail)
        confidence = self._confidence(summary, campaign_detail)
        refined_payload, refinement_notes = self._refine_action_payload(
            action_type=request.action_type,
            action_payload=request.action_payload,
            campaign_budget=float(campaign.budget_daily) if campaign and campaign.budget_daily is not None else None,
            notes=request.notes or "",
        )
        feedback_context = self._build_feedback_context(
            action_type=request.action_type,
            notes=request.notes or "",
            campaign_detail=campaign_detail,
            analysis_mode=analysis_mode,
            original_payload=request.action_payload,
            refined_payload=refined_payload,
        )

        base = self._base_proposal(
            request=request,
            summary=summary,
            campaign_detail=campaign_detail,
            analysis_mode=analysis_mode,
            confidence=confidence,
            original_payload=request.action_payload,
            refined_payload=refined_payload,
            refinement_notes=refinement_notes,
            feedback_context=feedback_context,
        )

        ai_metadata = {
            "provider": "rules",
            "model": "internal",
            "used_ai": False,
        }
        ai_refinement = openai_client.refine_recommendation_proposal(base, request.notes or "")
        if ai_refinement:
            if isinstance(ai_refinement.get("summary"), str) and ai_refinement["summary"].strip():
                base["summary"] = ai_refinement["summary"].strip()
            for field in (
                "why_this_proposal",
                "suggested_changes",
                "risks",
                "discussion_points",
                "approval_checklist",
            ):
                value = ai_refinement.get(field)
                if isinstance(value, list):
                    base[field] = [str(item).strip() for item in value if str(item).strip()]
            refinement_summary = ai_refinement.get("refinement_summary")
            if isinstance(refinement_summary, str) and refinement_summary.strip():
                base["refinement_summary"] = refinement_summary.strip()
            ai_metadata = {
                "provider": "openai",
                "model": "configured",
                "used_ai": True,
            }

        base["ai_metadata"] = ai_metadata
        return base

    def _analysis_mode(
        self,
        summary: dict[str, Any],
        campaign_detail: dict[str, Any] | None,
    ) -> str:
        if not campaign_detail:
            return "DIAGNOSTIC" if summary["measurement_readiness"] != "HIGH" else "OPTIMIZATION"

        delivery_diagnosis = campaign_detail["analysis"].get("delivery_diagnosis")
        if delivery_diagnosis and delivery_diagnosis["stage"] in {"NOT_SERVING", "LIMITED"}:
            return "DIAGNOSTIC"

        metrics = campaign_detail["performance"]["metrics"]
        if metrics["total_impressions"] == 0 and metrics["total_clicks"] == 0 and metrics["total_cost"] == 0:
            return "DIAGNOSTIC"
        if metrics["total_conversions"] == 0 or summary["measurement_readiness"] != "HIGH":
            return "DIAGNOSTIC"
        return "OPTIMIZATION"

    def _confidence(
        self,
        summary: dict[str, Any],
        campaign_detail: dict[str, Any] | None,
    ) -> str:
        if not campaign_detail:
            return "LOW" if summary["measurement_readiness"] == "LOW" else "MEDIUM"

        delivery_diagnosis = campaign_detail["analysis"].get("delivery_diagnosis")
        if delivery_diagnosis and delivery_diagnosis["stage"] == "NOT_SERVING":
            return "HIGH" if delivery_diagnosis.get("google_primary_status") else "LOW"
        if delivery_diagnosis and delivery_diagnosis["stage"] == "LIMITED":
            return "MEDIUM"

        metrics = campaign_detail["performance"]["metrics"]
        has_search_terms = bool(campaign_detail["query_intelligence"]["top_search_terms"])
        if metrics["total_conversions"] > 0 and has_search_terms and summary["measurement_readiness"] == "HIGH":
            return "HIGH"
        if metrics["total_clicks"] > 0 or metrics["total_impressions"] > 0:
            return "MEDIUM"
        return "LOW"

    def _refine_action_payload(
        self,
        action_type: str,
        action_payload: dict[str, Any],
        campaign_budget: float | None,
        notes: str,
    ) -> tuple[dict[str, Any], list[str]]:
        payload = deepcopy(action_payload)
        normalized = notes.lower()
        refinement_notes: list[str] = []

        if action_type == "BUDGET_REALLOC" and campaign_budget and (
            payload.get("target_daily_budget") is not None or payload.get("target_budget_change_percent") is not None
        ):
            target_budget = payload.get("target_daily_budget")
            if target_budget is None:
                change_percent = float(payload.get("target_budget_change_percent", 0))
                target_budget = round(campaign_budget * (1 + (change_percent / 100)), 2)
            target_budget = float(target_budget)

            if any(term in normalized for term in ("conserv", "cautel", "prud", "devagar")):
                if target_budget > campaign_budget:
                    target_budget = round(min(target_budget, campaign_budget * 1.1), 2)
                else:
                    target_budget = round(max(target_budget, campaign_budget * 0.9), 2)
                refinement_notes.append("Ajuste suavizado para um ritmo mais conservador.")
            elif any(term in normalized for term in ("agress", "forte", "rapido")):
                if target_budget > campaign_budget:
                    target_budget = round(max(target_budget, campaign_budget * 1.2), 2)
                refinement_notes.append("Ajuste mantido em um ritmo mais agressivo.")

            payload["target_daily_budget"] = target_budget
            payload["target_budget_change_percent"] = round(((target_budget / campaign_budget) - 1) * 100, 2)

        if action_type in {"KEYWORD_ADD", "KEYWORD_REMOVE"}:
            if "exata" in normalized or "exact" in normalized:
                payload["match_type"] = "EXACT"
                refinement_notes.append("Match type refinado para EXACT.")
            elif "frase" in normalized or "phrase" in normalized:
                payload["match_type"] = "PHRASE"
                refinement_notes.append("Match type refinado para PHRASE.")
            elif "ampla" in normalized or "broad" in normalized:
                payload["match_type"] = "BROAD"
                refinement_notes.append("Match type refinado para BROAD.")

        return payload, refinement_notes

    def _base_proposal(
        self,
        request: RecommendationProposalRequest,
        summary: dict[str, Any],
        campaign_detail: dict[str, Any] | None,
        analysis_mode: str,
        confidence: str,
        original_payload: dict[str, Any],
        refined_payload: dict[str, Any],
        refinement_notes: list[str],
        feedback_context: dict[str, Any],
    ) -> dict[str, Any]:
        metrics = campaign_detail["performance"]["metrics"] if campaign_detail else None
        campaign_name = request.campaign_name or (campaign_detail["name"] if campaign_detail else None)
        delivery_diagnosis = (
            campaign_detail["analysis"].get("delivery_diagnosis")
            if campaign_detail and campaign_detail.get("analysis")
            else None
        )
        data_notes = self._build_data_notes(summary, campaign_detail, delivery_diagnosis)

        summary_line = (
            "Esta proposta esta em modo de diagnostico. Ainda nao existe sinal suficiente para dizer o que performa melhor; "
            "o objetivo agora e destravar entrega, validar medicao e ajustar risco antes de otimizar."
            if analysis_mode == "DIAGNOSTIC"
            else "Esta proposta ja esta em modo de otimizacao. Existe sinal suficiente para mexer em budget, keywords ou pausa com mais confianca."
        )
        if feedback_context["summary_suffix"]:
            summary_line = f"{summary_line} {feedback_context['summary_suffix']}"

        why_this_proposal = [
            f"Measurement readiness atual: {summary['measurement_readiness']}.",
        ]
        if metrics:
            why_this_proposal.append(
                f"Campanha com {metrics['total_impressions']} impressoes, {metrics['total_clicks']} cliques, "
                f"{metrics['total_conversions']:.2f} conversoes e custo de R${metrics['total_cost']:.2f} no recorte salvo."
            )
        if delivery_diagnosis:
            why_this_proposal.append(delivery_diagnosis["summary"])
        if campaign_detail and campaign_detail["analysis"]["summary"]:
            why_this_proposal.append(campaign_detail["analysis"]["summary"])

        suggested_changes = self._build_suggested_changes(
            request.action_type,
            refined_payload,
            campaign_detail,
        )
        risks = self._build_risks(request.action_type, analysis_mode)
        preflight_checklist = self._build_preflight_checklist(request.action_type, analysis_mode, campaign_detail)
        discussion_points = self._build_discussion_points(request.action_type, analysis_mode, campaign_detail)
        success_signals = self._build_success_signals(request.action_type, analysis_mode)
        approval_checklist = self._build_approval_checklist(request.action_type, analysis_mode)
        change_highlights = self._build_change_highlights(
            action_type=request.action_type,
            original_payload=original_payload,
            refined_payload=refined_payload,
        )
        suggested_changes = self._dedupe_items(suggested_changes + feedback_context["suggested_overlays"])
        preflight_checklist = self._dedupe_items(feedback_context["preflight_overlays"] + preflight_checklist)
        discussion_points = self._dedupe_items(feedback_context["discussion_overlays"] + discussion_points)
        approval_checklist = self._dedupe_items(approval_checklist + feedback_context["approval_overlays"])
        change_highlights = self._dedupe_items(change_highlights + feedback_context["applied_feedback"])

        refinement_summary = None
        if refinement_notes:
            refinement_summary = " ".join(refinement_notes)
        elif feedback_context["refinement_summary"]:
            refinement_summary = feedback_context["refinement_summary"]
        elif (request.notes or "").strip():
            refinement_summary = (
                "Seu feedback foi incorporado na leitura e no checklist, mas nao alterou os parametros executaveis desta acao."
            )

        return {
            "action_type": request.action_type,
            "proposal_title": f"Proposta para {request.title}",
            "campaign_id": request.campaign_id,
            "campaign_name": campaign_name,
            "analysis_mode": analysis_mode,
            "confidence": confidence,
            "summary": summary_line,
            "data_notes": data_notes,
            "why_this_proposal": why_this_proposal,
            "suggested_changes": suggested_changes,
            "risks": risks,
            "preflight_checklist": preflight_checklist,
            "discussion_points": discussion_points,
            "success_signals": success_signals,
            "approval_checklist": approval_checklist,
            "change_highlights": change_highlights,
            "feedback_notes": feedback_context["feedback_notes"],
            "applied_feedback": feedback_context["applied_feedback"],
            "pending_feedback": feedback_context["pending_feedback"],
            "refinement_summary": refinement_summary,
            "refined_action": {
                "title": request.title,
                "description": request.description,
                "action_payload": refined_payload,
                "recommended_execution_mode": feedback_context["recommended_execution_mode"],
            },
            "ai_metadata": {
                "provider": "rules",
                "model": "internal",
                "used_ai": False,
            },
        }

    def _build_data_notes(
        self,
        summary: dict[str, Any],
        campaign_detail: dict[str, Any] | None,
        delivery_diagnosis: dict[str, Any] | None,
    ) -> list[str]:
        notes = [
            f"Conta: {summary['impressions']} impressoes, {summary['clicks']} cliques, {summary['conversions']:.2f} conversoes e R${summary['cost']:.2f} de custo em 30 dias.",
        ]
        if campaign_detail:
            metrics = campaign_detail["performance"]["metrics"]
            notes.append(
                f"Campanha: {metrics['total_impressions']} impressoes, {metrics['total_clicks']} cliques, {metrics['total_conversions']:.2f} conversoes e R${metrics['total_cost']:.2f} de custo."
            )
            query_intelligence = campaign_detail["query_intelligence"]
            notes.append(
                f"Search terms salvos: {query_intelligence.get('search_term_count', len(query_intelligence['top_search_terms']))}; keywords sincronizadas: {query_intelligence['keyword_count']}."
            )
        if delivery_diagnosis:
            notes.append(
                f"Diagnostico de entrega: {delivery_diagnosis['status_label']}."
            )
        return notes

    def _build_suggested_changes(
        self,
        action_type: str,
        refined_payload: dict[str, Any],
        campaign_detail: dict[str, Any] | None,
    ) -> list[str]:
        if action_type == "BUDGET_REALLOC":
            current_budget = refined_payload.get("current_budget_daily")
            target_budget = refined_payload.get("target_daily_budget")
            if current_budget is not None and target_budget is not None:
                return [
                    f"Alterar o budget diario de R${float(current_budget):.2f} para R${float(target_budget):.2f}.",
                    "Usar o ajuste como controle de risco enquanto a campanha ainda acumula os primeiros sinais.",
                ]
        if action_type == "KEYWORD_REMOVE":
            search_term = refined_payload.get("search_term") or refined_payload.get("keyword_text")
            match_type = refined_payload.get("match_type") or "PHRASE"
            return [
                f"Negativar o termo '{search_term}' em match type {match_type}.",
                "Evitar que consultas fracas consumam impressao e clique antes de haver mais dados.",
            ]
        if action_type == "KEYWORD_ADD":
            keyword_text = refined_payload.get("keyword_text")
            match_type = refined_payload.get("match_type") or "EXACT"
            return [
                f"Criar a keyword '{keyword_text}' em {match_type}.",
                "Ganhar mais controle sobre uma consulta que merece leitura separada da massa atual.",
            ]
        if action_type == "PAUSE_UNDERPERFORMING":
            return [
                "Pausar a campanha ou segurar a entrega ate revisar a causa-raiz.",
                "Evitar continuar queimando verba em uma estrutura que ainda nao mostrou encaixe.",
            ]

        recommendations = campaign_detail["analysis"]["next_steps"] if campaign_detail else []
        return recommendations[:2] or ["Concluir a revisao manual antes de qualquer mudanca na conta."]

    def _build_risks(self, action_type: str, analysis_mode: str) -> list[str]:
        risks = [
            "Toda mudanca em campanha ativa precisa de rechecagem apos o proximo sync.",
        ]
        if analysis_mode == "DIAGNOSTIC":
            risks.append("Como ainda falta sinal suficiente, qualquer ajuste agora serve mais para diagnosticar do que para otimizar performance.")
        if action_type == "BUDGET_REALLOC":
            risks.append("Budget muito baixo pode atrasar ainda mais a aprendizagem; budget alto demais pode queimar verba sem leitura clara.")
        if action_type == "KEYWORD_REMOVE":
            risks.append("Negativar cedo demais pode cortar volume util se a query ainda nao teve dados suficientes.")
        if action_type == "KEYWORD_ADD":
            risks.append("Adicionar keyword sem estrutura de ad group ou anuncio alinhado pode criar mais ruido do que controle.")
        if action_type == "PAUSE_UNDERPERFORMING":
            risks.append("Pausar campanha em aprendizado pode esconder um problema de tracking ou elegibilidade, e nao de performance real.")
        return risks

    def _build_preflight_checklist(
        self,
        action_type: str,
        analysis_mode: str,
        campaign_detail: dict[str, Any] | None,
    ) -> list[str]:
        checklist = [
            "Confirmar se a campanha esta aprovada, elegivel e realmente servindo.",
            "Validar URL final, evento principal e Enhanced Conversions.",
        ]
        delivery_diagnosis = (
            campaign_detail["analysis"].get("delivery_diagnosis")
            if campaign_detail and campaign_detail.get("analysis")
            else None
        )
        if delivery_diagnosis:
            checklist = delivery_diagnosis["next_checks"][:2] + checklist
        if analysis_mode == "DIAGNOSTIC":
            checklist.append("Confirmar que ainda estamos em diagnostico de entrega, nao em otimizacao de performance.")
        if action_type in {"KEYWORD_ADD", "KEYWORD_REMOVE"}:
            checklist.append("Revisar se a query faz sentido dentro da estrutura branded, general, competitor ou remarketing.")
        if action_type == "BUDGET_REALLOC":
            checklist.append("Checar se o budget novo respeita o risco que voce quer correr nesta fase.")
        return self._dedupe_items(checklist)

    def _build_discussion_points(
        self,
        action_type: str,
        analysis_mode: str,
        campaign_detail: dict[str, Any] | None,
    ) -> list[str]:
        points = [
            "Esse ajuste esta alinhado com o objetivo principal da campanha?",
            "Queremos uma postura mais conservadora ou mais agressiva neste ciclo?",
        ]
        if analysis_mode == "DIAGNOSTIC":
            points.append("Devemos priorizar destravar entrega primeiro ou ja testar uma mudanca estrutural?")
        if action_type == "BUDGET_REALLOC":
            points.append("Faz sentido discutir antes se a campanha deveria ser separada por intencao antes de mexer no budget?")
        if action_type in {"KEYWORD_ADD", "KEYWORD_REMOVE"}:
            points.append("A query proposta precisa ir para um ad group proprio ou basta revisar a lista atual?")
        if campaign_detail:
            points.extend(campaign_detail["analysis"]["next_steps"][:1])
            delivery_diagnosis = campaign_detail["analysis"].get("delivery_diagnosis")
            if delivery_diagnosis and delivery_diagnosis["blockers"]:
                points.append(f"O maior bloqueio agora parece ser: {delivery_diagnosis['blockers'][0]}")
        return self._dedupe_items(points)

    def _build_success_signals(self, action_type: str, analysis_mode: str) -> list[str]:
        if analysis_mode == "DIAGNOSTIC":
            return [
                "Primeiras impressoes reais aparecendo no recorte sincronizado.",
                "Primeiros cliques e search terms suficientes para leitura.",
                "Evento principal disparando de forma confiavel.",
            ]
        if action_type == "BUDGET_REALLOC":
            return [
                "CTR se mantem ou melhora apos a mudanca.",
                "CPA nao piora acima do guardrail definido.",
                "Conversoes sobem sem perda de eficiencia fora do combinado.",
            ]
        return [
            "Mudanca refletida no Google Ads sem erro.",
            "Proximo sync mostra impacto legivel na campanha.",
        ]

    def _build_approval_checklist(self, action_type: str, analysis_mode: str) -> list[str]:
        checklist = [
            "Voce revisou a proposta e concorda com a direcao?",
            "Os riscos e guardrails estao aceitaveis para este ciclo?",
        ]
        if action_type == "BUDGET_REALLOC":
            checklist.append("O budget final esta exatamente no valor que voce quer aprovar?")
        if action_type in {"KEYWORD_ADD", "KEYWORD_REMOVE"}:
            checklist.append("A keyword e o match type estao do jeito que voce quer publicar?")
        if analysis_mode == "DIAGNOSTIC":
            checklist.append("Voce entende que esta aprovando um movimento de diagnostico, nao uma otimizacao definitiva?")
        return checklist

    def _build_change_highlights(
        self,
        action_type: str,
        original_payload: dict[str, Any],
        refined_payload: dict[str, Any],
    ) -> list[str]:
        if action_type == "BUDGET_REALLOC":
            before_budget = original_payload.get("current_budget_daily") or original_payload.get("target_daily_budget")
            after_budget = refined_payload.get("target_daily_budget")
            change_percent = refined_payload.get("target_budget_change_percent")
            if before_budget is not None and after_budget is not None:
                return [
                    f"Budget alvo: R${float(before_budget):.2f} -> R${float(after_budget):.2f}.",
                    (
                        f"Variacao prevista: {float(change_percent):.2f}%."
                        if change_percent is not None
                        else "Variacao percentual recalculada pelo refino."
                    ),
                ]
        if action_type in {"KEYWORD_ADD", "KEYWORD_REMOVE"}:
            label = refined_payload.get("keyword_text") or refined_payload.get("search_term") or "query principal"
            match_type = refined_payload.get("match_type") or original_payload.get("match_type") or "PHRASE"
            return [
                f"Termo principal desta proposta: '{label}'.",
                f"Match type final aprovado para a proposta: {match_type}.",
            ]
        if action_type == "PAUSE_UNDERPERFORMING":
            return [
                "A campanha ficara pausada somente depois da sua aprovacao final.",
                "O foco desta proposta e conter gasto enquanto o gargalo principal e revisado.",
            ]

        changes: list[str] = []
        for key, value in refined_payload.items():
            if original_payload.get(key) != value:
                changes.append(f"{key}: {original_payload.get(key)} -> {value}")
        return changes or ["Os parametros executaveis permaneceram iguais; o refino ficou concentrado na explicacao e no checklist."]

    def _build_feedback_context(
        self,
        action_type: str,
        notes: str,
        campaign_detail: dict[str, Any] | None,
        analysis_mode: str,
        original_payload: dict[str, Any],
        refined_payload: dict[str, Any],
    ) -> dict[str, Any]:
        normalized = self._normalize_text(notes)
        default_execution_mode = "approve_and_execute" if action_type != "BID_ADJUSTMENT" else "plan_only"

        context = {
            "summary_suffix": "",
            "feedback_notes": [],
            "applied_feedback": [],
            "pending_feedback": [],
            "suggested_overlays": [],
            "preflight_overlays": [],
            "discussion_overlays": [],
            "approval_overlays": [],
            "recommended_execution_mode": default_execution_mode,
            "refinement_summary": "",
        }

        if not notes.strip():
            return context

        context["feedback_notes"].append(f"Pedido registrado: {notes.strip()}")

        if any(term in normalized for term in ("nao executar", "nao rodar", "somente discutir", "só discutir", "so discutir", "esperar")):
            context["recommended_execution_mode"] = "plan_only"
            context["applied_feedback"].append("A proposta foi mantida em modo plano/manual porque voce pediu para nao executar agora.")
            context["approval_overlays"].append("O proprio feedback desta rodada pede discussao antes de qualquer execucao.")

        if any(
            term in normalized
            for term in (
                "quero deixar ele funcional",
                "deixar ele funcional",
                "analisar o pq nao funcionou",
                "analisar porque nao funcionou",
                "analisar por que nao funcionou",
                "preciso que analise o pq nao funcionou",
                "preciso q analise o pq nao funcionou",
                "gere a solucao pra eu analisar",
                "gerar a solucao para eu analisar",
                "ver se aprovo",
                "ver se eu aprovo",
            )
        ):
            context["recommended_execution_mode"] = "plan_only"
            context["applied_feedback"].append(
                "Seu pedido mudou o fluxo para: diagnosticar por que nao funcionou, gerar uma solucao e deixar a execucao bloqueada ate sua aprovacao."
            )
            context["summary_suffix"] = (
                "Nesta rodada, o sistema mudou a proposta para um fluxo de diagnostico e solucao revisavel, sem execucao automatica."
            )
            context["suggested_overlays"].extend(
                [
                    "Trocar a conversa de ajuste imediato para diagnostico de causa-raiz da falta de entrega.",
                    "Gerar uma solucao revisavel antes de qualquer mudanca executavel na conta.",
                ]
            )
            context["preflight_overlays"].extend(
                [
                    "Confirmar por que a campanha nao esta funcionando antes de aprovar qualquer acao operacional.",
                    "Validar aprovacao, elegibilidade, tracking, keywords e configuracao estrutural como primeira etapa da solucao.",
                ]
            )
            context["discussion_overlays"].extend(
                [
                    "Qual e a causa-raiz mais provavel para a campanha nao estar funcionando hoje?",
                    "A solucao precisa atacar entrega, estrutura, tracking ou politica antes de mexer em budget?",
                ]
            )
            context["approval_overlays"].append(
                "Esta rodada ficou em modo de diagnostico + solucao revisavel; a execucao deve esperar sua aprovacao final."
            )

        if action_type == "BUDGET_REALLOC":
            current_budget = original_payload.get("current_budget_daily")
            refined_budget = refined_payload.get("target_daily_budget")
            if current_budget is not None and any(
                term in normalized
                for term in (
                    "nao aumentar budget",
                    "nao mexer no budget",
                    "sem ampliar budget",
                    "segurar budget",
                    "manter budget",
                )
            ):
                refined_payload["target_daily_budget"] = float(current_budget)
                refined_payload["target_budget_change_percent"] = 0.0
                context["applied_feedback"].append("Voce pediu para nao ampliar budget agora; a proposta foi recalibrada para manter o budget atual.")
                context["summary_suffix"] = "Seu feedback mudou a proposta para um ajuste de contencao, nao de escala."
            elif current_budget is not None and refined_budget is not None and refined_budget != original_payload.get("target_daily_budget"):
                context["applied_feedback"].append("O budget alvo foi recalculado com base no tom do seu feedback.")

        if action_type in {"KEYWORD_ADD", "KEYWORD_REMOVE"}:
            match_type = refined_payload.get("match_type")
            if match_type:
                context["applied_feedback"].append(f"O match type final da proposta ficou em {match_type}.")

        if any(term in normalized for term in ("branded", "marca")):
            context["applied_feedback"].append("A proposta passou a destacar a necessidade de separar branded da estrutura generica.")
            context["discussion_overlays"].append("Faz sentido abrir uma campanha branded separada antes de insistir nesta mesma estrutura?")
            context["suggested_overlays"].append("Separar branded de general intent para ganhar clareza de leitura e controle de budget.")

        if any(term in normalized for term in ("competitor", "concorr")):
            context["applied_feedback"].append("Seu feedback puxou a discussao para competitor, que pede campanha e budget separados.")
            context["discussion_overlays"].append("Queremos mesmo atacar competitor agora ou isso deve entrar numa campanha propria?")
            context["suggested_overlays"].append("Criar uma esteira separada para competitor em vez de misturar essa intencao com busca generica.")

        if any(term in normalized for term in ("tracking", "tag", "convers", "evento", "ga4", "pixel")):
            context["applied_feedback"].append("A proposta passou a enfatizar tracking como gate obrigatorio antes de otimizar.")
            context["preflight_overlays"].append("Rodar o playbook *setup-tracking e validar evento principal com teste real.")

        if any(term in normalized for term in ("nao esta veiculando", "nao esta servindo", "por que nao veicula", "por que nao entrega")):
            context["applied_feedback"].append("O diagnostico de veiculacao foi promovido para o centro da proposta.")
            context["summary_suffix"] = "O foco desta rodada ficou em explicar por que a campanha nao esta entregando antes de falar em performance."

        if any(term in normalized for term in ("manual", "depois", "mais tarde")):
            context["recommended_execution_mode"] = "plan_only"
            context["applied_feedback"].append("A proposta foi rebaixada para plano/manual nesta rodada, conforme o seu pedido.")

        if campaign_detail:
            delivery_diagnosis = campaign_detail["analysis"].get("delivery_diagnosis")
            if delivery_diagnosis and delivery_diagnosis["stage"] != "SERVING":
                context["discussion_overlays"].append(
                    f"O gargalo principal agora e: {delivery_diagnosis['blockers'][0]}"
                )

        if not context["applied_feedback"]:
            context["pending_feedback"].append(
                "Seu texto foi anexado a proposta, mas ainda nao consegui converter isso em parametro executavel automatico."
            )
            context["pending_feedback"].append(
                "Mesmo assim, a proposta foi atualizada para registrar essa direcao antes da aprovacao."
            )
            context["summary_suffix"] = "Nesta rodada, o sistema registrou sua direcao estrategica, mas ela ainda depende de discussao manual."

        if context["pending_feedback"]:
            context["discussion_overlays"].extend(context["pending_feedback"])

        context["refinement_summary"] = " ".join(self._dedupe_items(context["applied_feedback"] + context["pending_feedback"]))
        return context

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", text or "")
        normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
        return normalized.lower()

    def _dedupe_items(self, items: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in items:
            normalized = str(item).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            ordered.append(normalized)
        return ordered


recommendation_workshop_service = RecommendationWorkshopService()
