"""
Campaign investigation workflow.

Creates a persisted diagnosis + repair plan so the UI can move beyond
"refine text" and into "investigate cause, propose fix, wait for approval".
"""

from __future__ import annotations

from typing import Any
from uuid import UUID
import uuid
from datetime import datetime
import re

from sqlalchemy.orm import Session

from integrations.google_ads_client import google_ads_wrapper
from models.database import (
    AuditLog,
    Campaign,
    CampaignInvestigation,
    GoogleAdsAccount,
    Recommendation,
)
from services.campaign_service import campaign_service
from services.google_ads_command_center import google_ads_command_center_service


class CampaignInvestigationService:
    """Build persisted campaign investigations from current account evidence."""

    STEP_PENDING = "pending"
    STEP_IN_PROGRESS = "in_progress"
    STEP_COMPLETED = "completed"
    API_STEP_ID = "aplicar-correcoes-aprovadas-via-api"
    RECHECK_STEP_ID = "esperar-novo-sync-e-reavaliar"

    def investigate_campaign(
        self,
        user_id: UUID,
        campaign_id: UUID,
        prompt: str,
        db: Session,
    ) -> dict[str, Any] | None:
        campaign = (
            db.query(Campaign)
            .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
            .filter(
                GoogleAdsAccount.user_id == user_id,
                Campaign.id == campaign_id,
            )
            .first()
        )
        if not campaign:
            return None

        account = (
            db.query(GoogleAdsAccount)
            .filter(GoogleAdsAccount.id == campaign.account_id)
            .first()
        )
        sync_status = {
            "attempted": False,
            "success": False,
            "detail": "No sync attempted.",
        }
        if account and account.is_active:
            try:
                sync_status["attempted"] = True
                campaign_service.sync_campaigns(account, db)
                sync_status["success"] = True
                sync_status["detail"] = "Campaign sync completed before investigation."
            except Exception:
                sync_status["attempted"] = True
                sync_status["success"] = False
                sync_status["detail"] = "Campaign sync failed, so the investigation used the latest saved snapshot."

        campaign_detail = google_ads_command_center_service.build_campaign_detail(
            user_id=user_id,
            campaign_id=campaign_id,
            db=db,
        )
        if not campaign_detail:
            return None

        payload = self._build_investigation_payload(
            prompt=prompt,
            campaign_detail=campaign_detail,
            sync_status=sync_status,
        )

        investigation = CampaignInvestigation(
            id=uuid.uuid4(),
            user_id=user_id,
            campaign_id=campaign_id,
            prompt=prompt,
            status="PLAN_READY",
            analysis_mode=payload["analysis_mode"],
            summary=payload["summary"],
            root_cause=payload["root_cause"],
            diagnosis=payload["diagnosis"],
            repair_plan=payload["repair_plan"],
            approval_payload=payload["approval_payload"],
        )

        db.add(investigation)
        db.commit()
        db.refresh(investigation)

        return self._serialize_investigation(investigation)

    def get_latest_campaign_investigation(
        self,
        user_id: UUID,
        campaign_id: UUID,
        db: Session,
    ) -> dict[str, Any] | None:
        investigation = (
            db.query(CampaignInvestigation)
            .join(Campaign, CampaignInvestigation.campaign_id == Campaign.id)
            .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
            .filter(
                GoogleAdsAccount.user_id == user_id,
                CampaignInvestigation.campaign_id == campaign_id,
            )
            .order_by(CampaignInvestigation.created_at.desc())
            .first()
        )

        if not investigation:
            return None

        repair_plan = self._normalize_repair_plan(investigation.repair_plan or {})
        approval_payload = self._normalize_approval_payload(investigation.approval_payload or {})
        if repair_plan != (investigation.repair_plan or {}) or approval_payload != (investigation.approval_payload or {}):
            investigation.repair_plan = repair_plan
            investigation.approval_payload = approval_payload
            db.add(investigation)
            db.commit()
            db.refresh(investigation)

        return self._serialize_investigation(investigation)

    def approve_investigation(
        self,
        user_id: UUID,
        campaign_id: UUID,
        investigation_id: UUID,
        approval_note: str | None,
        db: Session,
    ) -> dict[str, Any] | None:
        investigation = (
            db.query(CampaignInvestigation)
            .join(Campaign, CampaignInvestigation.campaign_id == Campaign.id)
            .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
            .filter(
                GoogleAdsAccount.user_id == user_id,
                CampaignInvestigation.campaign_id == campaign_id,
                CampaignInvestigation.id == investigation_id,
            )
            .first()
        )

        if not investigation:
            return None

        repair_plan = self._normalize_repair_plan(investigation.repair_plan or {})
        approval_payload = dict(investigation.approval_payload or {})
        approval_payload["blocked_until_approval"] = False
        approval_payload["approval_note"] = approval_note
        approval_payload["approved_at"] = datetime.utcnow().isoformat()
        approval_payload["message"] = (
            "Plano aprovado. Agora avance etapa por etapa e só execute as ações candidatas quando o diagnóstico já estiver claro."
        )

        investigation.status = "APPROVED"
        investigation.repair_plan = repair_plan
        investigation.approval_payload = approval_payload
        db.add(investigation)
        db.commit()
        db.refresh(investigation)

        return self._serialize_investigation(investigation)

    def update_step_status(
        self,
        user_id: UUID,
        campaign_id: UUID,
        investigation_id: UUID,
        step_id: str,
        status: str,
        note: str | None,
        db: Session,
    ) -> dict[str, Any] | None:
        if status not in {
            self.STEP_PENDING,
            self.STEP_IN_PROGRESS,
            self.STEP_COMPLETED,
        }:
            raise ValueError("Invalid step status.")

        investigation = (
            db.query(CampaignInvestigation)
            .join(Campaign, CampaignInvestigation.campaign_id == Campaign.id)
            .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
            .filter(
                GoogleAdsAccount.user_id == user_id,
                CampaignInvestigation.campaign_id == campaign_id,
                CampaignInvestigation.id == investigation_id,
            )
            .first()
        )

        if not investigation:
            return None

        approval_payload = dict(investigation.approval_payload or {})
        if approval_payload.get("blocked_until_approval", True):
            raise ValueError("Approve the investigation plan before updating workflow steps.")

        repair_plan = self._normalize_repair_plan(investigation.repair_plan or {})
        sequence = repair_plan.get("sequence", [])

        target_step = next((step for step in sequence if step.get("id") == step_id), None)
        if not target_step:
            return None

        timestamp = datetime.utcnow().isoformat()
        target_step["status"] = status
        target_step["last_updated_at"] = timestamp
        if status == self.STEP_COMPLETED:
            target_step["completed_at"] = timestamp
            target_step["completion_note"] = note
        else:
            target_step["completed_at"] = None
            if note:
                target_step["completion_note"] = note

        history = list(repair_plan.get("history", []))
        history.append(
            {
                "step_id": step_id,
                "title": target_step.get("title"),
                "status": status,
                "note": note,
                "created_at": timestamp,
            }
        )
        repair_plan["history"] = history

        all_completed = all(
            step.get("status") == self.STEP_COMPLETED for step in sequence
        )
        investigation.status = "EXECUTED" if all_completed else "APPROVED"
        if all_completed:
            approval_payload["message"] = (
                "Todas as etapas do repair workflow foram concluídas. Agora a campanha está pronta para uma nova leitura e para otimizações posteriores."
            )
        investigation.repair_plan = repair_plan
        investigation.approval_payload = approval_payload
        db.add(investigation)
        db.commit()
        db.refresh(investigation)

        return self._serialize_investigation(investigation)

    def execute_investigation_actions(
        self,
        user_id: UUID,
        campaign_id: UUID,
        investigation_id: UUID,
        execution_note: str | None,
        db: Session,
    ) -> dict[str, Any] | None:
        investigation = (
            db.query(CampaignInvestigation)
            .join(Campaign, CampaignInvestigation.campaign_id == Campaign.id)
            .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
            .filter(
                GoogleAdsAccount.user_id == user_id,
                CampaignInvestigation.campaign_id == campaign_id,
                CampaignInvestigation.id == investigation_id,
            )
            .first()
        )

        if not investigation:
            return None

        approval_payload = dict(investigation.approval_payload or {})
        if approval_payload.get("blocked_until_approval", True):
            raise ValueError("Approve the investigation plan before asking the app to apply fixes.")

        campaign = (
            db.query(Campaign)
            .join(GoogleAdsAccount, Campaign.account_id == GoogleAdsAccount.id)
            .filter(
                GoogleAdsAccount.user_id == user_id,
                Campaign.id == campaign_id,
            )
            .first()
        )
        if not campaign:
            return None

        account = (
            db.query(GoogleAdsAccount)
            .filter(GoogleAdsAccount.id == campaign.account_id)
            .first()
        )
        if not account:
            raise ValueError("No connected Google Ads account available for this campaign.")

        repair_plan = self._normalize_repair_plan(investigation.repair_plan or {})
        candidate_actions = list(approval_payload.get("candidate_actions", []))
        executable_actions = [
            action
            for action in candidate_actions
            if "approve_and_execute" in (action.get("execution_modes") or [])
        ]

        if not executable_actions:
            candidate_count = len(candidate_actions)
            raise ValueError(
                "Esta investigacao ainda nao tem nenhuma correcao segura para o app aplicar por API. "
                + (
                    "As sugestoes atuais ainda estao em modo de plano ou revisao manual."
                    if candidate_count
                    else "A leitura atual ainda nao gerou sugestoes executaveis."
                )
            )

        execution_results: list[dict[str, Any]] = []
        executed_any = False
        failed_any = False
        now = datetime.utcnow().isoformat()

        self._set_step_status(
            repair_plan=repair_plan,
            step_id=self.API_STEP_ID,
            status=self.STEP_IN_PROGRESS,
            note="O app iniciou a aplicacao automatica das correcoes aprovadas.",
            created_at=now,
        )

        for action in executable_actions:
            result = self._execute_candidate_action(
                user_id=user_id,
                account=account,
                campaign=campaign,
                action=action,
                execution_note=execution_note,
                db=db,
            )
            execution_results.append(result)
            if result["status"] == "executed":
                executed_any = True
            if result["status"] == "failed":
                failed_any = True

        sync_status = {
            "attempted": False,
            "success": False,
            "detail": "No sync attempted after execution.",
        }
        if account.is_active:
            try:
                sync_status["attempted"] = True
                stats = campaign_service.sync_campaigns(account, db)
                sync_status["success"] = True
                sync_status["detail"] = (
                    f"Post-repair sync completed: {stats.get('updated', 0)} updated, "
                    f"{stats.get('created', 0)} created."
                )
            except Exception:
                sync_status["attempted"] = True
                sync_status["success"] = False
                sync_status["detail"] = "Post-repair sync failed; the investigation kept the latest saved snapshot."

        refreshed_detail = google_ads_command_center_service.build_campaign_detail(
            user_id=user_id,
            campaign_id=campaign_id,
            db=db,
        )
        if refreshed_detail:
            refreshed_payload = self._build_investigation_payload(
                prompt=investigation.prompt,
                campaign_detail=refreshed_detail,
                sync_status=sync_status,
            )
            investigation.summary = (
                f"Correcoes via API executadas para {refreshed_detail['name']}. "
                f"Leia o novo diagnostico antes da proxima rodada."
            )
            investigation.root_cause = refreshed_payload["root_cause"]
            investigation.analysis_mode = refreshed_payload["analysis_mode"]
            investigation.diagnosis = refreshed_payload["diagnosis"]

        api_note = (
            f"{sum(1 for item in execution_results if item['status'] == 'executed')} acao(oes) executada(s), "
            f"{sum(1 for item in execution_results if item['status'] == 'skipped')} ignorada(s), "
            f"{sum(1 for item in execution_results if item['status'] == 'failed')} com falha."
        )
        self._set_step_status(
            repair_plan=repair_plan,
            step_id=self.API_STEP_ID,
            status=self.STEP_COMPLETED if not failed_any else self.STEP_IN_PROGRESS,
            note=api_note,
            created_at=datetime.utcnow().isoformat(),
        )
        self._set_step_status(
            repair_plan=repair_plan,
            step_id=self.RECHECK_STEP_ID,
            status=self.STEP_COMPLETED if sync_status["success"] else self.STEP_IN_PROGRESS,
            note=sync_status["detail"],
            created_at=datetime.utcnow().isoformat(),
        )

        approval_payload["execution_results"] = execution_results
        approval_payload["execution_note"] = execution_note
        approval_payload["last_executed_at"] = datetime.utcnow().isoformat()
        approval_payload["message"] = (
            "O app aplicou as correcoes elegiveis por API e atualizou o diagnostico da campanha. "
            "Agora voce revisa o que foi realmente alterado e o novo estado da entrega."
        )

        investigation.status = "EXECUTED" if executed_any else "APPROVED"
        investigation.repair_plan = repair_plan
        investigation.approval_payload = approval_payload
        db.add(investigation)
        db.commit()
        db.refresh(investigation)

        return self._serialize_investigation(investigation)

    def _build_investigation_payload(
        self,
        prompt: str,
        campaign_detail: dict[str, Any],
        sync_status: dict[str, Any],
    ) -> dict[str, Any]:
        analysis = campaign_detail["analysis"]
        delivery = analysis["delivery_diagnosis"]
        performance = campaign_detail["performance"]["metrics"]
        query_intelligence = campaign_detail["query_intelligence"]
        recommended_actions = campaign_detail["recommended_actions"]

        root_cause = delivery["blockers"][0] if delivery["blockers"] else analysis["summary"]
        analysis_mode = "DIAGNOSTIC" if delivery["stage"] != "SERVING" else analysis["analysis_mode"]

        summary = (
            f"Investigacao criada para {campaign_detail['name']}. "
            f"A leitura atual aponta como causa principal: {root_cause}"
        )

        diagnosis = {
            "requested_analysis": prompt,
            "campaign_status": campaign_detail["status"],
            "google_primary_status": campaign_detail.get("primary_status"),
            "sync_status": sync_status,
            "delivery_stage": delivery["stage"],
            "delivery_summary": delivery["summary"],
            "blockers": delivery["blockers"],
            "evidence": delivery["evidence"],
            "xquads_playbooks": delivery["xquads_playbooks"],
            "metrics_snapshot": {
                "impressions": performance["total_impressions"],
                "clicks": performance["total_clicks"],
                "conversions": performance["total_conversions"],
                "cost": performance["total_cost"],
                "keyword_count": query_intelligence["keyword_count"],
                "search_term_count": query_intelligence.get("search_term_count", 0),
            },
        }

        repair_steps = self._build_repair_steps(campaign_detail)
        approval_actions = self._select_approval_actions(recommended_actions)
        api_safe_actions = [
            action
            for action in approval_actions
            if "approve_and_execute" in (action.get("execution_modes") or [])
        ]

        approval_payload = {
            "mode": "review_before_execute",
            "message": (
                "Esta investigacao gera um plano revisavel. "
                + (
                    "Ja existe ao menos uma correcao segura que o app pode aplicar por API depois da sua aprovacao."
                    if api_safe_actions
                    else "Nesta leitura, o app ainda nao encontrou nenhuma correcao segura para aplicar sozinho por API."
                )
            ),
            "candidate_actions": approval_actions,
            "blocked_until_approval": True,
            "execution_results": [],
        }

        return {
            "analysis_mode": analysis_mode,
            "summary": summary,
            "root_cause": root_cause,
            "diagnosis": diagnosis,
            "repair_plan": {
                "goal": "Descobrir por que a campanha nao funciona, destravar entrega e so depois voltar para otimizacao.",
                "sequence": repair_steps,
                "success_signals": self._build_success_signals(campaign_detail),
                "history": [],
            },
            "approval_payload": approval_payload,
        }

    def _build_repair_steps(self, campaign_detail: dict[str, Any]) -> list[dict[str, Any]]:
        analysis = campaign_detail["analysis"]
        delivery = analysis["delivery_diagnosis"]
        query_intelligence = campaign_detail["query_intelligence"]

        steps = [
            {
                "id": self._make_step_id("Diagnosticar a causa-raiz"),
                "title": "Diagnosticar a causa-raiz",
                "owner": "traffic-chief",
                "playbook": "*diagnose",
                "reason": delivery["summary"],
                "actions": delivery["blockers"][:3] or ["Concluir triagem do gargalo principal antes de alterar a campanha."],
                "status": self.STEP_COMPLETED,
                "completed_at": datetime.utcnow().isoformat(),
                "completion_note": "O diagnostico inicial foi gerado automaticamente pelo sistema.",
                "last_updated_at": datetime.utcnow().isoformat(),
            },
            {
                "id": self._make_step_id("Validar tracking e elegibilidade"),
                "title": "Validar tracking e elegibilidade",
                "owner": "pixel-specialist",
                "playbook": "*setup-tracking",
                "reason": "Sem tracking confiavel ou elegibilidade confirmada, qualquer otimização posterior fica contaminada.",
                "actions": delivery["next_checks"][:3],
                "status": self.STEP_PENDING,
                "completed_at": None,
                "completion_note": None,
                "last_updated_at": None,
            },
            {
                "id": self._make_step_id("Revisar estrutura da campanha"),
                "title": "Revisar estrutura da campanha",
                "owner": "ads-analyst / kasim-aslam",
                "playbook": "*audit-ad-account",
                "reason": "Separar intencoes e eliminar gargalos de estrutura antes de mexer em escala.",
                "actions": self._build_structure_actions(campaign_detail),
                "status": self.STEP_PENDING,
                "completed_at": None,
                "completion_note": None,
                "last_updated_at": None,
            },
            {
                "id": self.API_STEP_ID,
                "title": "Aplicar correcoes aprovadas via API",
                "owner": "system",
                "playbook": "api-execution",
                "reason": "Depois da sua aprovacao, o app tenta aplicar automaticamente as mudancas seguras que ja tem payload executavel.",
                "actions": self._build_api_repair_actions(campaign_detail),
                "status": self.STEP_PENDING,
                "completed_at": None,
                "completion_note": None,
                "last_updated_at": None,
            },
        ]

        if delivery["stage"] == "SERVING":
            steps.append(
                {
                    "id": self._make_step_id("Voltar para otimizacao de performance"),
                    "title": "Voltar para otimizacao de performance",
                    "owner": "performance-analyst",
                    "playbook": "*analyze-performance",
                    "reason": "A campanha ja tem entrega suficiente para discutir eficiencia com mais confianca.",
                    "actions": analysis["next_steps"][:3],
                    "status": self.STEP_PENDING,
                    "completed_at": None,
                    "completion_note": None,
                    "last_updated_at": None,
                }
            )
        else:
            steps.append(
                {
                    "id": self.RECHECK_STEP_ID,
                    "title": "Esperar novo sync e reavaliar",
                    "owner": "system",
                    "playbook": "sync + review",
                    "reason": "Depois das correcoes, precisamos confirmar se a campanha finalmente entrou em distribuicao real.",
                    "actions": [
                        "Rodar novo sync da conta depois da correcao aprovada.",
                        "Conferir se apareceram impressoes, cliques e search terms.",
                        "So depois discutir budget, bid e escala.",
                    ],
                    "status": self.STEP_PENDING,
                    "completed_at": None,
                    "completion_note": None,
                    "last_updated_at": None,
                }
            )

        if query_intelligence["keyword_count"] == 0:
            steps[2]["actions"].insert(
                0,
                "Sincronizar e revisar keywords antes de concluir qualquer leitura sobre cobertura de busca.",
            )

        return steps

    def _select_approval_actions(
        self,
        recommended_actions: list[dict[str, Any]],
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Prioritize executable actions so investigations don't hide safe API fixes."""
        executable = [
            action
            for action in recommended_actions
            if "approve_and_execute" in (action.get("execution_modes") or [])
        ]
        non_executable = [
            action
            for action in recommended_actions
            if "approve_and_execute" not in (action.get("execution_modes") or [])
        ]

        selected: list[dict[str, Any]] = []
        seen_keys: set[tuple[str | None, str | None]] = set()

        for action in executable + non_executable:
            key = (action.get("type"), action.get("title"))
            if key in seen_keys:
                continue
            selected.append(action)
            seen_keys.add(key)
            if len(selected) >= limit:
                break

        return selected

    def _build_structure_actions(self, campaign_detail: dict[str, Any]) -> list[str]:
        actions = [
            "Separar branded, general intent, competitor e remarketing quando essas intencoes estiverem misturadas.",
            "Revisar se a landing page, a promessa do anuncio e a intencao da keyword conversam entre si.",
            "Evitar discutir escala antes de a campanha provar que consegue entregar e medir.",
        ]

        query_intelligence = campaign_detail["query_intelligence"]
        if query_intelligence["search_term_count"] == 0:
            actions.insert(
                0,
                "A campanha ainda nao gerou search terms; trate isso como sinal de falta de entrega antes de falar em refinamento fino.",
            )

        return actions

    def _build_api_repair_actions(self, campaign_detail: dict[str, Any]) -> list[str]:
        executable_actions = [
            action["title"]
            for action in campaign_detail.get("recommended_actions", [])
            if "approve_and_execute" in (action.get("execution_modes") or [])
        ]
        if executable_actions:
            return executable_actions[:3]

        return [
            "Nenhuma correcao elegivel por API apareceu nesta leitura. Se isso continuar, o problema esta fora do que o Google Ads API permite alterar sozinho.",
        ]

    def _build_success_signals(self, campaign_detail: dict[str, Any]) -> list[str]:
        delivery = campaign_detail["analysis"]["delivery_diagnosis"]
        if delivery["stage"] != "SERVING":
            return [
                "A campanha passa a gerar impressoes reais depois da correcao aprovada.",
                "Os primeiros search terms aparecem no sync seguinte.",
                "O diagnostico sai de 'Nao esta veiculando' para pelo menos 'Veiculacao limitada'.",
            ]

        return [
            "A campanha continua entregando e ganha sinais suficientes para uma analise de performance completa.",
            "As correcoes aprovadas reduzem blockers sem piorar CTR ou CPA fora do guardrail.",
        ]

    def _make_step_id(self, title: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        return slug or str(uuid.uuid4())

    def _set_step_status(
        self,
        *,
        repair_plan: dict[str, Any],
        step_id: str,
        status: str,
        note: str | None,
        created_at: str,
    ) -> None:
        target_step = next(
            (step for step in repair_plan.get("sequence", []) if step.get("id") == step_id),
            None,
        )
        if not target_step:
            return

        target_step["status"] = status
        target_step["last_updated_at"] = created_at
        if status == self.STEP_COMPLETED:
            target_step["completed_at"] = created_at
            target_step["completion_note"] = note
        elif note:
            target_step["completion_note"] = note

        repair_plan.setdefault("history", []).append(
            {
                "step_id": step_id,
                "title": target_step.get("title"),
                "status": status,
                "note": note,
                "created_at": created_at,
            }
        )

    def _build_recommendation_audit_log(
        self,
        *,
        action_type: str,
        user_id: UUID,
        account_id: UUID,
        resource_id: str | None,
        changes: dict[str, Any],
    ) -> AuditLog:
        mapped_action_type = "RECOMMENDATION_ACCEPT"
        mapped_resource_type = "CAMPAIGN"

        if action_type == "PAUSE_UNDERPERFORMING":
            mapped_action_type = "CAMPAIGN_PAUSE"
            mapped_resource_type = "CAMPAIGN"
        elif action_type == "BUDGET_REALLOC":
            mapped_action_type = "BID_UPDATE"
            mapped_resource_type = "CAMPAIGN"
        elif action_type in {"KEYWORD_ADD", "KEYWORD_REMOVE"}:
            mapped_action_type = "KEYWORD_ADD"
            mapped_resource_type = "KEYWORD"

        return AuditLog(
            id=uuid.uuid4(),
            user_id=user_id,
            account_id=account_id,
            action_type=mapped_action_type,
            resource_type=mapped_resource_type,
            resource_id=resource_id,
            changes=changes,
            source="RECOMMENDATION",
        )

    def _execute_candidate_action(
        self,
        *,
        user_id: UUID,
        account: GoogleAdsAccount,
        campaign: Campaign,
        action: dict[str, Any],
        execution_note: str | None,
        db: Session,
    ) -> dict[str, Any]:
        action_type = action.get("type")
        recommendation = Recommendation(
            id=uuid.uuid4(),
            account_id=account.id,
            campaign_id=campaign.id,
            type=action_type,
            title=action.get("title") or action_type,
            description=action.get("description") or "",
            priority=action.get("priority", "MEDIUM"),
            estimated_impact=action.get("estimated_impact"),
            action_payload=action.get("action_payload") or {},
            status="OPEN",
        )

        payload = action.get("action_payload") or {}
        result = {
            "title": action.get("title") or action_type,
            "action_type": action_type,
            "status": "skipped",
            "message": "No API execution was attempted.",
        }

        try:
            if action_type == "PAUSE_UNDERPERFORMING":
                succeeded = google_ads_wrapper.pause_campaign(
                    refresh_token=account.refresh_token,
                    customer_id=account.customer_id,
                    google_campaign_id=campaign.google_campaign_id,
                )
                if not succeeded:
                    raise ValueError("Google Ads rejected the pause operation.")

                campaign.status = "PAUSED"
                recommendation.status = "EXECUTED"
                recommendation.executed_at = datetime.utcnow()
                db.add(recommendation)
                db.add(
                    self._build_recommendation_audit_log(
                        action_type=action_type,
                        user_id=user_id,
                        account_id=account.id,
                        resource_id=campaign.google_campaign_id,
                        changes={
                            "after": {"status": "PAUSED"},
                            "approval_note": execution_note,
                        },
                    )
                )
                db.commit()
                result["status"] = "executed"
                result["message"] = f"Campanha {campaign.name} pausada com sucesso."
                result["recommendation_id"] = str(recommendation.id)
                return result

            if action_type == "BUDGET_REALLOC":
                current_budget = float(campaign.budget_daily or 0)
                change_percent = float(payload.get("target_budget_change_percent", 0))
                target_budget = payload.get("target_daily_budget")
                new_budget = (
                    float(target_budget)
                    if target_budget is not None
                    else round(current_budget * (1 + (change_percent / 100)), 2)
                )
                if current_budget <= 0 or new_budget <= 0:
                    result["message"] = "Campaign has no valid daily budget to update."
                    return result

                succeeded = google_ads_wrapper.update_campaign_budget(
                    refresh_token=account.refresh_token,
                    customer_id=account.customer_id,
                    google_campaign_id=campaign.google_campaign_id,
                    new_daily_budget=new_budget,
                )
                if not succeeded:
                    raise ValueError("Google Ads rejected the budget update.")

                campaign.budget_daily = new_budget
                recommendation.status = "EXECUTED"
                recommendation.executed_at = datetime.utcnow()
                db.add(recommendation)
                db.add(
                    self._build_recommendation_audit_log(
                        action_type=action_type,
                        user_id=user_id,
                        account_id=account.id,
                        resource_id=campaign.google_campaign_id,
                        changes={
                            "before": {"budget_daily": current_budget},
                            "after": {"budget_daily": new_budget},
                            "approval_note": execution_note,
                        },
                    )
                )
                db.commit()
                result["status"] = "executed"
                result["message"] = f"Budget diario atualizado para R${new_budget:.2f}."
                result["recommendation_id"] = str(recommendation.id)
                return result

            if action_type == "KEYWORD_REMOVE":
                search_term = payload.get("search_term") or payload.get("keyword_text")
                if not search_term:
                    result["message"] = "Action needs a search term or keyword text."
                    return result

                succeeded = google_ads_wrapper.add_campaign_negative_keyword(
                    refresh_token=account.refresh_token,
                    customer_id=account.customer_id,
                    google_campaign_id=campaign.google_campaign_id,
                    keyword_text=search_term,
                    match_type=payload.get("match_type"),
                )
                if not succeeded:
                    raise ValueError("Google Ads rejected the negative keyword operation.")

                recommendation.status = "EXECUTED"
                recommendation.executed_at = datetime.utcnow()
                db.add(recommendation)
                db.add(
                    self._build_recommendation_audit_log(
                        action_type=action_type,
                        user_id=user_id,
                        account_id=account.id,
                        resource_id=campaign.google_campaign_id,
                        changes={
                            "after": {
                                "search_term": search_term,
                                "match_type": payload.get("match_type"),
                                "negative": True,
                            },
                            "approval_note": execution_note,
                        },
                    )
                )
                db.commit()
                result["status"] = "executed"
                result["message"] = f"Termo '{search_term}' negativado com sucesso."
                result["recommendation_id"] = str(recommendation.id)
                return result

            if action_type == "KEYWORD_ADD":
                keyword_text = payload.get("keyword_text")
                if not keyword_text:
                    result["message"] = "Action needs keyword_text."
                    return result

                response = google_ads_wrapper.add_keyword_to_best_ad_group(
                    refresh_token=account.refresh_token,
                    customer_id=account.customer_id,
                    google_campaign_id=campaign.google_campaign_id,
                    keyword_text=keyword_text,
                    match_type=payload.get("match_type"),
                )
                if not response:
                    raise ValueError("Google Ads rejected the keyword creation.")

                recommendation.status = "EXECUTED"
                recommendation.executed_at = datetime.utcnow()
                db.add(recommendation)
                db.add(
                    self._build_recommendation_audit_log(
                        action_type=action_type,
                        user_id=user_id,
                        account_id=account.id,
                        resource_id=response.get("resource_name") or campaign.google_campaign_id,
                        changes={
                            "after": {
                                "keyword_text": keyword_text,
                                "match_type": response.get("match_type"),
                                "ad_group_id": response.get("ad_group_id"),
                                "ad_group_name": response.get("ad_group_name"),
                            },
                            "approval_note": execution_note,
                        },
                    )
                )
                db.commit()
                result["status"] = "executed"
                result["message"] = (
                    f"Keyword '{keyword_text}' criada no ad group "
                    f"{response.get('ad_group_name') or response.get('ad_group_id')}."
                )
                result["recommendation_id"] = str(recommendation.id)
                return result

            result["message"] = "This action type is not API-executable in the current app."
            return result
        except Exception as exc:
            db.rollback()
            result["status"] = "failed"
            result["message"] = str(exc)
            return result

    def _normalize_repair_plan(self, repair_plan: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(repair_plan or {})
        sequence = []

        for step in normalized.get("sequence", []):
            normalized_step = dict(step)
            normalized_step.setdefault(
                "id",
                self._make_step_id(normalized_step.get("title", "repair-step")),
            )
            normalized_step.setdefault("status", self.STEP_PENDING)
            normalized_step.setdefault("completed_at", None)
            normalized_step.setdefault("completion_note", None)
            normalized_step.setdefault("last_updated_at", None)
            sequence.append(normalized_step)

        normalized["sequence"] = sequence
        normalized["history"] = list(normalized.get("history", []))
        return normalized

    def _normalize_approval_payload(self, approval_payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(approval_payload or {})
        normalized.setdefault("mode", "review_before_execute")
        normalized.setdefault("message", "")
        normalized["candidate_actions"] = list(normalized.get("candidate_actions", []))
        normalized.setdefault("blocked_until_approval", True)
        normalized.setdefault("approval_note", None)
        normalized.setdefault("approved_at", None)
        normalized.setdefault("execution_note", None)
        normalized.setdefault("last_executed_at", None)
        normalized["execution_results"] = list(normalized.get("execution_results", []))
        return normalized

    def _serialize_investigation(self, investigation: CampaignInvestigation) -> dict[str, Any]:
        return {
            "id": investigation.id,
            "campaign_id": investigation.campaign_id,
            "prompt": investigation.prompt,
            "status": investigation.status,
            "analysis_mode": investigation.analysis_mode,
            "summary": investigation.summary,
            "root_cause": investigation.root_cause,
            "diagnosis": investigation.diagnosis,
            "repair_plan": self._normalize_repair_plan(investigation.repair_plan or {}),
            "approval_payload": self._normalize_approval_payload(investigation.approval_payload or {}),
            "created_at": investigation.created_at,
            "updated_at": investigation.updated_at,
        }


campaign_investigation_service = CampaignInvestigationService()
