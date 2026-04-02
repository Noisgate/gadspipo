"""
Campaign Studio service.

Transforms a campaign briefing into a structured Google Ads launch plan.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any
from uuid import UUID, uuid4

from integrations.openai_client import openai_client
from models.schemas import (
    CampaignStudioBriefDraft,
    CampaignStudioBriefRequest,
    CampaignStudioIdeaRequest,
    CampaignStudioUploadedMaterial,
)

_SEARCH_SIGNALS = ("buscar", "procura", "cotacao", "comprar", "contratar", "lead", "vendas")
_ECOMMERCE_SIGNALS = ("ecommerce", "loja", "catalogo", "catálogo", "sku", "produto")
_VIDEO_SIGNALS = ("video", "vídeo", "youtube", "reels", "demonstracao", "demonstração")
_AWARENESS_SIGNALS = ("awareness", "reconhecimento", "alcance", "branding", "marca")

_ASSET_LIBRARY = {
    "logo": "Logo da marca",
    "product_images": "Imagens do produto/servico",
    "lifestyle_images": "Imagens de contexto/uso",
    "video": "Video curto de demonstracao",
    "landing_page": "Landing page pronta",
    "testimonials": "Provas ou depoimentos",
    "brand_guide": "Guia visual da marca",
    "feed": "Feed/catalogo de produtos",
}

_DOCUMENT_LIBRARY = {
    "price_list": "Tabela de precos",
    "compliance_policy": "Politica/compliance do servico",
    "privacy_policy": "Politica de privacidade",
    "sales_script": "Script comercial ou atendimento",
    "offer_doc": "Documento da oferta",
    "case_studies": "Cases ou resultados anteriores",
}

_UPLOAD_ROOT = Path(__file__).resolve().parents[1] / "uploads" / "campaign_studio"
_MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024


class CampaignStudioService:
    """Builds a structured launch plan for a new campaign."""

    def store_uploaded_material(
        self,
        user_id: UUID,
        filename: str,
        content_type: str | None,
        content: bytes,
    ) -> dict[str, Any]:
        if not filename:
            raise ValueError("Arquivo sem nome nao pode ser processado")
        if not content:
            raise ValueError(f"O arquivo '{filename}' veio vazio")
        if len(content) > _MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(f"O arquivo '{filename}' excede o limite de 20 MB")

        safe_name = self._sanitize_filename(filename)
        material_id = str(uuid4())
        user_folder = _UPLOAD_ROOT / str(user_id)
        user_folder.mkdir(parents=True, exist_ok=True)

        stored_name = f"{material_id}__{safe_name}"
        stored_path = user_folder / stored_name
        stored_path.write_bytes(content)

        return self._classify_uploaded_material(
            material_id=material_id,
            original_name=filename,
            stored_name=stored_name,
            content_type=content_type or "application/octet-stream",
            size_bytes=len(content),
        )

    def diagnose_idea(self, request: CampaignStudioIdeaRequest) -> dict[str, Any]:
        material_payload = [
            material.model_dump() if isinstance(material, CampaignStudioUploadedMaterial) else material
            for material in request.uploaded_materials
        ]
        inferred_brief = self._infer_brief_from_request(request, material_payload)

        synthetic_brief = CampaignStudioBriefRequest(
            business_name=inferred_brief.business_name,
            product_or_service=inferred_brief.product_or_service or "Oferta a validar",
            offer=inferred_brief.offer or "Oferta principal a validar",
            objective=inferred_brief.objective,
            intention=inferred_brief.intention or request.request,
            target_audience=inferred_brief.target_audience or "Publico a validar",
            location=inferred_brief.location or "Brasil",
            budget_amount=inferred_brief.budget_amount or 80,
            budget_period=inferred_brief.budget_period,
            website_url=inferred_brief.website_url,
            conversion_goal=inferred_brief.conversion_goal,
            differentiators=inferred_brief.differentiators,
            current_assets=inferred_brief.current_assets,
            available_documents=inferred_brief.available_documents,
            notes=inferred_brief.notes,
        )

        context_blob = " ".join(
            filter(
                None,
                [
                    synthetic_brief.product_or_service,
                    synthetic_brief.offer,
                    synthetic_brief.intention,
                    synthetic_brief.target_audience,
                    synthetic_brief.notes,
                ],
            )
        ).lower()
        campaign_type = self._recommend_campaign_type(
            objective=synthetic_brief.objective,
            context_blob=context_blob,
            assets=synthetic_brief.current_assets,
        )
        bidding_strategy = self._recommend_bidding_strategy(
            objective=synthetic_brief.objective,
            conversion_goal=synthetic_brief.conversion_goal,
            website_url=synthetic_brief.website_url,
        )
        material_requirements = self._build_asset_requirements(
            campaign_type=campaign_type,
            current_assets=synthetic_brief.current_assets,
        )
        questions_to_clarify = self._build_idea_questions(
            brief=inferred_brief,
            uploaded_materials=material_payload,
        )
        next_steps = self._build_idea_next_steps(
            campaign_type=campaign_type,
            material_requirements=material_requirements,
            questions_to_clarify=questions_to_clarify,
        )

        fallback_payload = {
            "summary": self._build_idea_summary(
                request_text=request.request,
                brief=inferred_brief,
                campaign_type=campaign_type,
                bidding_strategy=bidding_strategy,
                material_payload=material_payload,
            ),
            "suggested_brief": inferred_brief.model_dump(),
            "questions_to_clarify": questions_to_clarify,
            "next_steps": next_steps,
        }
        ai_enrichment = openai_client.diagnose_campaign_idea(
            request_text=request.request,
            fallback_payload=fallback_payload,
        )
        if ai_enrichment:
            inferred_brief = self._merge_ai_brief(
                inferred_brief,
                ai_enrichment.get("suggested_brief", {}),
            )
            if ai_enrichment.get("questions_to_clarify"):
                questions_to_clarify = self._merge_unique(
                    ai_enrichment["questions_to_clarify"],
                    questions_to_clarify,
                )[:6]
            if ai_enrichment.get("next_steps"):
                next_steps = self._merge_unique(
                    ai_enrichment["next_steps"],
                    next_steps,
                )[:6]
            summary = ai_enrichment.get("summary", fallback_payload["summary"])
            ai_metadata = {
                "provider": "openai+rules-engine",
                "model": "gpt-4o",
                "used_ai": True,
            }
        else:
            summary = fallback_payload["summary"]
            ai_metadata = {
                "provider": "rules-engine",
                "model": "idea-analyzer-v1",
                "used_ai": False,
            }

        return {
            "summary": summary,
            "suggested_campaign_type": campaign_type,
            "suggested_bidding_strategy": bidding_strategy,
            "suggested_brief": inferred_brief.model_dump(),
            "questions_to_clarify": questions_to_clarify,
            "material_requirements": material_requirements,
            "uploaded_materials": material_payload,
            "next_steps": next_steps,
            "ai_metadata": ai_metadata,
        }

    def analyze(self, brief: CampaignStudioBriefRequest) -> dict[str, Any]:
        normalized_daily_budget = self._to_daily_budget(
            brief.budget_amount,
            brief.budget_period,
        )
        context_blob = " ".join(
            filter(
                None,
                [
                    brief.product_or_service,
                    brief.offer,
                    brief.intention,
                    brief.target_audience,
                    brief.notes,
                ],
            )
        ).lower()

        campaign_type = self._recommend_campaign_type(
            objective=brief.objective,
            context_blob=context_blob,
            assets=brief.current_assets,
        )
        bidding_strategy = self._recommend_bidding_strategy(
            objective=brief.objective,
            conversion_goal=brief.conversion_goal,
            website_url=brief.website_url,
        )

        asset_requirements = self._build_asset_requirements(
            campaign_type=campaign_type,
            current_assets=brief.current_assets,
        )
        information_requirements = self._build_information_requirements(brief)
        blockers = self._build_blockers(asset_requirements, information_requirements)
        launch_readiness = self._build_launch_readiness(
            brief=brief,
            blockers=blockers,
            asset_requirements=asset_requirements,
            information_requirements=information_requirements,
        )

        payload = {
            "briefing_digest": self._build_briefing_digest(
                brief=brief,
                normalized_daily_budget=normalized_daily_budget,
                campaign_type=campaign_type,
                blockers=blockers,
            ),
            "strategic_recommendation": {
                "recommended_campaign_type": campaign_type,
                "recommended_bidding_strategy": bidding_strategy,
                "budget_daily_suggestion": normalized_daily_budget,
                "budget_explanation": self._build_budget_explanation(
                    objective=brief.objective,
                    normalized_daily_budget=normalized_daily_budget,
                ),
                "rationale": self._build_rationale(
                    brief=brief,
                    campaign_type=campaign_type,
                    blockers=blockers,
                ),
                "launch_sequence": self._build_launch_sequence(campaign_type, blockers),
            },
            "campaign_blueprint": self._build_campaign_blueprint(
                brief=brief,
                campaign_type=campaign_type,
                normalized_daily_budget=normalized_daily_budget,
            ),
            "messaging": self._build_messaging(brief),
            "asset_requirements": asset_requirements,
            "information_requirements": information_requirements,
            "launch_checklist": self._build_launch_checklist(
                brief=brief,
                blockers=blockers,
                asset_requirements=asset_requirements,
                information_requirements=information_requirements,
            ),
            "tracking_requirements": self._build_tracking_requirements(brief),
            "compliance_checks": self._build_compliance_checks(brief),
            "launch_readiness": launch_readiness,
            "ai_metadata": {
                "provider": "rules-engine",
                "model": "internal-strategy-engine",
                "used_ai": False,
            },
        }

        ai_enrichment = openai_client.enrich_campaign_studio_brief(
            brief.model_dump(),
            payload,
        )
        if ai_enrichment:
            payload["briefing_digest"]["summary"] = ai_enrichment.get(
                "strategic_summary",
                payload["briefing_digest"]["summary"],
            )
            payload["messaging"]["headline_ideas"] = self._merge_unique(
                ai_enrichment.get("headline_ideas", []),
                payload["messaging"]["headline_ideas"],
            )[:8]
            payload["messaging"]["description_ideas"] = self._merge_unique(
                ai_enrichment.get("description_ideas", []),
                payload["messaging"]["description_ideas"],
            )[:6]

            if ai_enrichment.get("questions_to_validate"):
                payload["launch_readiness"]["next_steps"] = self._merge_unique(
                    ai_enrichment["questions_to_validate"],
                    payload["launch_readiness"]["next_steps"],
                )[:6]

            payload["ai_metadata"] = {
                "provider": "openai+rules-engine",
                "model": "gpt-4o",
                "used_ai": True,
            }

        return payload

    def _infer_brief_from_request(
        self,
        request: CampaignStudioIdeaRequest,
        uploaded_materials: list[dict[str, Any]],
    ) -> CampaignStudioBriefDraft:
        request_text = request.request.strip()
        lower_request = request_text.lower()
        budget_amount, budget_period = self._extract_budget(
            lower_request,
            request.budget_amount,
            request.budget_period,
        )
        current_assets = self._unique_items(
            [
                material["mapped_asset"]
                for material in uploaded_materials
                if material.get("mapped_asset")
            ]
        )
        available_documents = self._unique_items(
            [
                material["mapped_document"]
                for material in uploaded_materials
                if material.get("mapped_document")
            ]
        )
        upload_note = None
        if uploaded_materials:
            upload_note = (
                f"{len(uploaded_materials)} material(is) enviado(s) para leitura inicial do estúdio."
            )

        return CampaignStudioBriefDraft(
            business_name=self._guess_business_name(request_text),
            product_or_service=self._guess_product_or_service(request_text),
            offer=self._guess_offer(request_text),
            objective=request.objective or self._guess_objective(lower_request),
            intention=request_text,
            target_audience=self._guess_target_audience(request_text),
            location=request.location or self._extract_location(request_text) or "Brasil",
            budget_amount=budget_amount,
            budget_period=budget_period,
            website_url=self._extract_url(request_text),
            conversion_goal=self._guess_conversion_goal(lower_request),
            differentiators=self._guess_differentiators(request_text),
            current_assets=current_assets,
            available_documents=available_documents,
            notes=upload_note,
        )

    def _guess_business_name(self, request_text: str) -> str | None:
        match = re.search(r"(?:marca|empresa|negocio|negócio)\s+([A-Z0-9][^,.;]+)", request_text, re.IGNORECASE)
        if not match:
            return None
        return self._clean_phrase(match.group(1), max_words=5)

    def _guess_product_or_service(self, request_text: str) -> str:
        patterns = [
            r"para vender\s+([^,.]+)",
            r"quero anunciar\s+([^,.]+)",
            r"campanha para\s+([^,.]+)",
            r"divulgar\s+([^,.]+)",
            r"oferta de\s+([^,.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, request_text, re.IGNORECASE)
            if match:
                return self._clean_phrase(match.group(1))

        words = [word for word in re.findall(r"[A-Za-z0-9À-ÿ]+", request_text) if len(word) > 2]
        guess = " ".join(words[:4]).strip()
        return guess or "Produto ou servico a detalhar"

    def _guess_offer(self, request_text: str) -> str:
        patterns = [
            r"oferta\s+(?:de|com)?\s*([^,.]+)",
            r"promoc[aã]o\s+(?:de|com)?\s*([^,.]+)",
            r"com\s+([^,.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, request_text, re.IGNORECASE)
            if match:
                cleaned = self._clean_phrase(match.group(1))
                if len(cleaned) >= 3:
                    return cleaned
        return "Oferta principal a validar"

    def _guess_target_audience(self, request_text: str) -> str:
        patterns = [
            r"para\s+([^,.]+)",
            r"publico(?:-alvo)?\s+([^,.]+)",
            r"p[uú]blico\s+([^,.]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, request_text, re.IGNORECASE)
            if match:
                cleaned = self._clean_phrase(match.group(1))
                if len(cleaned) >= 6:
                    return cleaned
        return "Publico de alta intencao a validar"

    def _guess_objective(self, lower_request: str) -> str:
        if any(term in lower_request for term in ("lead", "cadastro", "whatsapp", "formulario")):
            return "LEADS"
        if any(term in lower_request for term in ("venda", "comprar", "loja", "checkout")):
            return "SALES"
        if any(term in lower_request for term in ("trafego", "tráfego", "cliques", "visitas")):
            return "TRAFFIC"
        if any(term in lower_request for term in ("alcance", "awareness", "marca", "reconhecimento")):
            return "AWARENESS"
        return "LEADS"

    def _guess_conversion_goal(self, lower_request: str) -> str | None:
        if "whatsapp" in lower_request:
            return "Inicio de conversa no WhatsApp"
        if "lead" in lower_request or "formulario" in lower_request:
            return "Lead qualificado"
        if "venda" in lower_request or "checkout" in lower_request:
            return "Compra concluida"
        return None

    def _guess_differentiators(self, request_text: str) -> str | None:
        match = re.search(r"(?:diferenciais?|vantagens?)\s+([^,.]+)", request_text, re.IGNORECASE)
        if not match:
            return None
        cleaned = self._clean_phrase(match.group(1), max_words=8)
        return cleaned or None

    def _extract_budget(
        self,
        lower_request: str,
        explicit_budget_amount: float | None,
        explicit_budget_period: str,
    ) -> tuple[float, str]:
        if explicit_budget_amount:
            return explicit_budget_amount, explicit_budget_period

        patterns = [
            (r"r\$\s*([0-9]+(?:[.,][0-9]+)?)\s*/\s*(dia|diario|diária|diario)", "daily"),
            (r"r\$\s*([0-9]+(?:[.,][0-9]+)?)\s*/\s*(mes|m[eê]s|mensal)", "monthly"),
            (r"([0-9]+(?:[.,][0-9]+)?)\s*(?:por dia|ao dia)", "daily"),
            (r"([0-9]+(?:[.,][0-9]+)?)\s*(?:por mes|por m[eê]s|ao mes|ao m[eê]s)", "monthly"),
        ]
        for pattern, period in patterns:
            match = re.search(pattern, lower_request, re.IGNORECASE)
            if match:
                value = float(match.group(1).replace(".", "").replace(",", "."))
                return value, period
        return 80.0, "daily"

    def _extract_location(self, request_text: str) -> str | None:
        match = re.search(
            r"\bem\s+([^,.]+?)(?:\s+com\s+|\s+para\s+|\s+onde\s+|$)",
            request_text,
            re.IGNORECASE,
        )
        if not match:
            return None
        cleaned = self._clean_phrase(match.group(1), max_words=4)
        return cleaned or None

    def _extract_url(self, request_text: str) -> str | None:
        match = re.search(r"https?://[^\s]+", request_text, re.IGNORECASE)
        return match.group(0) if match else None

    def _build_idea_summary(
        self,
        request_text: str,
        brief: CampaignStudioBriefDraft,
        campaign_type: str,
        bidding_strategy: str,
        material_payload: list[dict[str, Any]],
    ) -> str:
        base = (
            f"Entendi que voce quer criar uma campanha de Google Ads para "
            f"{brief.product_or_service or 'uma oferta ainda nao detalhada'}, com foco em "
            f"{brief.objective.lower()} usando {campaign_type}."
        )
        base += (
            f" A leitura inicial sugere trabalhar com lance '{bidding_strategy}'"
            f" e budget de {brief.budget_amount or 80:.0f} por "
            f"{'dia' if brief.budget_period == 'daily' else 'mes'}."
        )
        if brief.location:
            base += f" A geografia inicial mais provavel e {brief.location}."
        if material_payload:
            base += f" Ja recebi {len(material_payload)} material(is), o que ajuda a acelerar o setup."
        return base

    def _build_idea_questions(
        self,
        brief: CampaignStudioBriefDraft,
        uploaded_materials: list[dict[str, Any]],
    ) -> list[str]:
        questions: list[str] = []
        if not brief.business_name:
            questions.append("Qual e o nome exato da marca que vai aparecer nos anuncios?")
        if not brief.website_url:
            questions.append("Qual e a URL final ou landing page que vai receber o trafego?")
        if not brief.conversion_goal:
            questions.append("Qual evento deve contar como sucesso: lead, WhatsApp, compra ou outra acao?")
        if not brief.differentiators:
            questions.append("Quais sao os diferenciais reais da oferta que precisam aparecer na copy?")
        if not uploaded_materials:
            questions.append("Quais materiais voce ja pode mandar agora: logo, imagens, video, tabela comercial ou cases?")
        return questions[:5]

    def _build_idea_next_steps(
        self,
        campaign_type: str,
        material_requirements: list[dict[str, Any]],
        questions_to_clarify: list[str],
    ) -> list[str]:
        next_steps = [
            "Revisar a leitura inicial e ajustar o briefing sugerido antes do plano final.",
            f"Separar os materiais prioritarios para uma campanha {campaign_type.lower()} sair melhor estruturada.",
            "Gerar o plano completo da campanha depois de fechar os campos criticos.",
        ]
        if any(item["priority"] == "HIGH" and item["status"] != "ready" for item in material_requirements):
            next_steps.insert(1, "Enviar os ativos de alta prioridade que ainda faltam para acelerar criativo e setup.")
        if questions_to_clarify:
            next_steps.insert(0, "Responder as perguntas pendentes para o estúdio montar uma campanha menos generica.")
        return self._unique_items(next_steps)[:5]

    def _merge_ai_brief(
        self,
        base_brief: CampaignStudioBriefDraft,
        ai_brief: dict[str, Any],
    ) -> CampaignStudioBriefDraft:
        if not isinstance(ai_brief, dict):
            return base_brief

        merged = base_brief.model_dump()
        for key, value in ai_brief.items():
            if key not in merged or value in (None, "", []):
                continue
            if key in {"current_assets", "available_documents"} and isinstance(value, list):
                merged[key] = self._merge_unique(value, merged[key])
                continue
            merged[key] = value
        try:
            return CampaignStudioBriefDraft.model_validate(merged)
        except Exception:
            return base_brief

    def _to_daily_budget(self, amount: float, period: str) -> float:
        if period == "monthly":
            return round(max(amount / 30, 20), 2)
        return round(max(amount, 20), 2)

    def _recommend_campaign_type(
        self,
        objective: str,
        context_blob: str,
        assets: list[str],
    ) -> str:
        if objective in {"LEADS", "SALES"}:
            if any(term in context_blob for term in _ECOMMERCE_SIGNALS):
                if "feed" in assets:
                    return "SHOPPING"
                if {"logo", "product_images"} & set(assets):
                    return "PERFORMANCE_MAX"
            if any(term in context_blob for term in _VIDEO_SIGNALS) and "video" in assets:
                return "VIDEO"
            return "SEARCH"

        if objective == "AWARENESS":
            if any(term in context_blob for term in _VIDEO_SIGNALS) and "video" in assets:
                return "VIDEO"
            return "DISPLAY"

        if objective == "TRAFFIC" and any(term in context_blob for term in _AWARENESS_SIGNALS):
            return "DISPLAY"

        return "SEARCH"

    def _recommend_bidding_strategy(
        self,
        objective: str,
        conversion_goal: str | None,
        website_url: str | None,
    ) -> str:
        if objective in {"LEADS", "SALES"} and website_url:
            if conversion_goal and "roas" in conversion_goal.lower():
                return "Maximize conversion value"
            return "Maximize conversions"
        if objective == "AWARENESS":
            return "Target CPM / alcance"
        return "Maximize clicks"

    def _build_briefing_digest(
        self,
        brief: CampaignStudioBriefRequest,
        normalized_daily_budget: float,
        campaign_type: str,
        blockers: list[str],
    ) -> dict[str, Any]:
        funnel_stage = "fundo" if brief.objective in {"LEADS", "SALES"} else "topo"
        summary = (
            f"{brief.product_or_service} com foco em {brief.objective.lower()} para {brief.target_audience} em "
            f"{brief.location}. A recomendacao inicial e começar com {campaign_type} usando um budget diario de "
            f"R${normalized_daily_budget:.2f}."
        )
        if blockers:
            summary += f" Antes de publicar, o plano precisa resolver {len(blockers)} bloqueio(s) principais."

        return {
            "business_name": brief.business_name or "Marca nao informada",
            "objective": brief.objective,
            "funnel_stage": funnel_stage,
            "normalized_daily_budget": normalized_daily_budget,
            "campaign_type": campaign_type,
            "summary": summary,
        }

    def _build_budget_explanation(self, objective: str, normalized_daily_budget: float) -> str:
        if objective in {"LEADS", "SALES"}:
            return (
                f"R${normalized_daily_budget:.2f}/dia cria uma fase inicial de validacao com volume suficiente "
                "para ler busca, anuncio e landing page sem escalar cedo demais."
            )
        return (
            f"R${normalized_daily_budget:.2f}/dia cobre a fase inicial de distribuicao e aprendizado de audiencia."
        )

    def _build_rationale(
        self,
        brief: CampaignStudioBriefRequest,
        campaign_type: str,
        blockers: list[str],
    ) -> list[str]:
        rationale = [
            "Comecar pela intencao mais alta reduz desperdicio e acelera o aprendizado da conta."
            if campaign_type == "SEARCH"
            else "O formato escolhido depende mais de criativo e distribuicao do que de intencao de busca."
        ]
        rationale.append(
            "A oferta e o diferencial ja entram no plano para evitar campanha generica sem motivo claro de clique."
        )
        if brief.website_url:
            rationale.append("Ja existe uma URL final, entao vale preparar o tracking desde a primeira versao.")
        else:
            rationale.append("Sem URL final validada, a campanha nao deve ser publicada ainda.")
        if blockers:
            rationale.append("Os bloqueios atuais apontam o que precisa ser fechado antes do go-live.")
        return rationale

    def _build_launch_sequence(self, campaign_type: str, blockers: list[str]) -> list[str]:
        sequence = [
            "Fechar oferta, CTA e pagina final.",
            f"Montar estrutura inicial de {campaign_type} com 2-4 grupos bem separados.",
            "Configurar tracking e testar o evento principal.",
            "Publicar com budget controlado e revisar as primeiras 48 horas.",
        ]
        if blockers:
            sequence.insert(0, "Resolver os bloqueios de publicacao antes de subir a conta.")
        return sequence

    def _build_campaign_blueprint(
        self,
        brief: CampaignStudioBriefRequest,
        campaign_type: str,
        normalized_daily_budget: float,
    ) -> dict[str, Any]:
        service = brief.product_or_service.strip()
        offer = brief.offer.strip()
        business_name = brief.business_name or service

        ad_groups = [
            {
                "name": "Alta intencao",
                "intent": "Capturar pessoas prontas para agir agora.",
                "keyword_themes": self._unique_items(
                    [
                        service,
                        f"comprar {service}",
                        f"contratar {service}",
                        f"{service} {brief.location}",
                    ]
                ),
                "audiences": [brief.target_audience],
                "landing_page_focus": "Oferta principal e CTA claro acima da dobra.",
            },
            {
                "name": "Oferta e diferenciais",
                "intent": "Transformar interesse em clique com argumento comercial.",
                "keyword_themes": self._unique_items(
                    [
                        offer,
                        f"{service} promocao",
                        f"melhor {service}",
                    ]
                ),
                "audiences": [brief.target_audience],
                "landing_page_focus": "Diferenciais, prova social e objeções.",
            },
        ]

        if business_name:
            ad_groups.append(
                {
                    "name": "Marca",
                    "intent": "Proteger busca de marca e aumentar taxa de fechamento.",
                    "keyword_themes": self._unique_items(
                        [
                            business_name,
                            f"{business_name} {service}",
                            f"{business_name} {offer}",
                        ]
                    ),
                    "audiences": ["Busca pela propria marca"],
                    "landing_page_focus": "Confiança, marca e caminho curto para conversao.",
                }
            )

        negative_themes = [
            "gratis",
            "emprego",
            "curso",
            "pdf",
            "olx",
            "mercado livre",
        ]

        return {
            "suggested_campaign_name": self._suggest_campaign_name(brief, campaign_type),
            "recommended_campaign_type": campaign_type,
            "daily_budget": normalized_daily_budget,
            "ad_groups": ad_groups,
            "negative_keyword_themes": negative_themes,
            "ad_extensions": [
                "Sitelinks para oferta, prova social e contato",
                "Callouts com diferenciais reais",
                "Snippet estruturado com categorias/servicos",
                "Extensao de chamada ou formulario, se aplicavel",
            ],
        }

    def _build_messaging(self, brief: CampaignStudioBriefRequest) -> dict[str, Any]:
        service = brief.product_or_service.strip()
        offer = brief.offer.strip()
        audience = brief.target_audience.strip()
        differentiators = brief.differentiators or "atendimento, clareza da oferta e velocidade comercial"

        angles = [
            f"Gancho de resultado: mostrar o que {audience} ganha ao escolher {service}.",
            f"Gancho de oferta: destacar {offer} com CTA simples e direto.",
            f"Gancho de confiança: usar {differentiators} como motivo concreto de escolha.",
        ]

        headline_ideas = self._unique_items(
            [
                f"{service} para {audience}",
                f"{offer}",
                f"Fale com especialista em {service}",
                f"Solicite agora: {service}",
                f"{service} em {brief.location}",
                f"Veja como funciona {service}",
            ]
        )

        description_ideas = self._unique_items(
            [
                f"Transforme a busca por {service} em conversa comercial com uma oferta clara e CTA imediato.",
                f"Destaque {offer} com prova, diferenciais e resposta rapida para reduzir friccao no clique.",
                "Prepare a pagina para explicar a oferta, responder objecoes e validar o evento principal.",
            ]
        )

        return {
            "angles": angles,
            "headline_ideas": headline_ideas,
            "description_ideas": description_ideas,
        }

    def _build_asset_requirements(
        self,
        campaign_type: str,
        current_assets: list[str],
    ) -> list[dict[str, Any]]:
        asset_set = set(current_assets)
        requirements = [
            self._requirement(
                item="Logo da marca",
                category="brand",
                priority="HIGH" if campaign_type in {"DISPLAY", "VIDEO", "PERFORMANCE_MAX"} else "MEDIUM",
                status="ready" if "logo" in asset_set else "missing",
                reason="Ajuda a montar marca, extensoes visuais e ativos para formatos mais ricos.",
                example="PNG quadrado e horizontal em boa resolucao.",
            ),
            self._requirement(
                item="Imagens do produto/servico",
                category="creative",
                priority="HIGH" if campaign_type in {"DISPLAY", "VIDEO", "PERFORMANCE_MAX", "SHOPPING"} else "MEDIUM",
                status="ready" if "product_images" in asset_set else "missing",
                reason="Sem visuais bons, a campanha perde forca quando entrar em formatos visuais ou assets complementares.",
                example="3-5 imagens horizontais mostrando produto, contexto e detalhe.",
            ),
            self._requirement(
                item="Landing page pronta",
                category="destination",
                priority="HIGH",
                status="ready" if "landing_page" in asset_set else "missing",
                reason="A pagina final precisa sustentar a promessa do anuncio e capturar o evento principal.",
                example="URL final com oferta, CTA e medicao do evento principal.",
            ),
            self._requirement(
                item="Prova social / depoimentos",
                category="proof",
                priority="MEDIUM",
                status="ready" if "testimonials" in asset_set else "recommended",
                reason="Melhora a confianca da oferta, especialmente em campanhas de lead e venda.",
                example="Cases, depoimentos curtos, antes/depois ou numeros reais.",
            ),
        ]

        if campaign_type in {"VIDEO", "PERFORMANCE_MAX"}:
            requirements.append(
                self._requirement(
                    item="Video curto de demonstracao",
                    category="creative",
                    priority="HIGH",
                    status="ready" if "video" in asset_set else "missing",
                    reason="Esses formatos dependem muito de criativo em movimento para distribuir bem.",
                    example="Video de 15-30s com hook inicial e CTA.",
                )
            )

        if campaign_type == "SHOPPING":
            requirements.append(
                self._requirement(
                    item="Feed/catalogo de produtos",
                    category="catalog",
                    priority="HIGH",
                    status="ready" if "feed" in asset_set else "missing",
                    reason="Shopping so fica publicavel com feed limpo e bem categorizado.",
                    example="Feed com titulo, preco, disponibilidade, imagem e URL.",
                )
            )

        return requirements

    def _build_information_requirements(
        self,
        brief: CampaignStudioBriefRequest,
    ) -> list[dict[str, Any]]:
        doc_set = set(brief.available_documents)
        return [
            self._requirement(
                item="URL final da campanha",
                category="setup",
                priority="HIGH",
                status="ready" if brief.website_url else "missing",
                reason="Sem URL final validada nao existe publicacao segura.",
                example=brief.website_url or "https://seudominio.com/oferta",
            ),
            self._requirement(
                item="Meta de conversao principal",
                category="tracking",
                priority="HIGH",
                status="ready" if brief.conversion_goal else "missing",
                reason="O sistema precisa saber qual evento sera otimizado.",
                example=brief.conversion_goal or "Lead qualificado, WhatsApp iniciado ou compra.",
            ),
            self._requirement(
                item="Diferenciais da oferta",
                category="positioning",
                priority="HIGH",
                status="ready" if brief.differentiators else "missing",
                reason="Sem motivo claro de escolha a copy fica generica e o CPC tende a piorar.",
                example=brief.differentiators or "Prazo, garantia, bonus, atendimento, facilidade.",
            ),
            self._requirement(
                item="Politica de privacidade / compliance",
                category="legal",
                priority="MEDIUM",
                status="ready" if "privacy_policy" in doc_set or "compliance_policy" in doc_set else "recommended",
                reason="Ajuda a reduzir risco de reprovacao e melhora a confianca na pagina.",
                example="Politica de privacidade publicada e revisada.",
            ),
            self._requirement(
                item="Provas, cases ou tabela comercial",
                category="sales_enablement",
                priority="MEDIUM",
                status="ready" if {"case_studies", "price_list", "offer_doc"} & doc_set else "recommended",
                reason="Esses materiais ajudam a sustentar anuncio, landing page e atendimento.",
                example="Case curto, tabela de condicoes, oferta detalhada.",
            ),
        ]

    def _build_launch_checklist(
        self,
        brief: CampaignStudioBriefRequest,
        blockers: list[str],
        asset_requirements: list[dict[str, Any]],
        information_requirements: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        checklist = [
            {
                "label": "Briefing comercial preenchido",
                "status": "ready",
                "detail": "Objetivo, audiencia, oferta e localizacao foram informados.",
            },
            {
                "label": "Pagina final pronta",
                "status": "ready" if brief.website_url else "missing",
                "detail": "Sem URL final a campanha nao deve ir para publicacao.",
            },
            {
                "label": "Tracking definido",
                "status": "ready" if brief.conversion_goal else "missing",
                "detail": "Evento principal precisa estar nomeado e testavel.",
            },
            {
                "label": "Criativos e ativos basicos",
                "status": "ready" if not any(item["status"] == "missing" and item["priority"] == "HIGH" for item in asset_requirements) else "warning",
                "detail": "Os ativos essenciais precisam existir antes do setup final.",
            },
            {
                "label": "Bloqueios de publicacao",
                "status": "ready" if not blockers else "warning",
                "detail": "Os bloqueios devem ser resolvidos antes do go-live.",
            },
        ]
        if any(item["status"] == "missing" for item in information_requirements if item["priority"] == "HIGH"):
            checklist.append(
                {
                    "label": "Informacoes criticas fechadas",
                    "status": "warning",
                    "detail": "Ainda faltam campos importantes para a oferta ficar publicavel.",
                }
            )
        return checklist

    def _build_tracking_requirements(self, brief: CampaignStudioBriefRequest) -> list[str]:
        event_name = brief.conversion_goal or "evento principal de conversao"
        return [
            f"Configurar e testar o evento '{event_name}' antes de escalar budget.",
            "Instalar Google tag e Conversion Linker na pagina final e na thank-you page/evento.",
            "Padronizar UTM source/medium/campaign/content para leitura de performance.",
            "Validar se CRM, WhatsApp ou formulario devolvem um fechamento rastreavel.",
        ]

    def _build_compliance_checks(self, brief: CampaignStudioBriefRequest) -> list[str]:
        checks = [
            "Garantir que a promessa do anuncio existe de verdade na pagina final.",
            "Evitar claims absolutos sem prova, especialmente em saude, renda ou promessas sensiveis.",
            "Revisar politica de privacidade, contato e termos basicos antes de captar lead.",
        ]
        if brief.objective in {"LEADS", "SALES"}:
            checks.append("Confirmar que o CTA e o fluxo de atendimento respeitam o que foi prometido no anuncio.")
        return checks

    def _build_launch_readiness(
        self,
        brief: CampaignStudioBriefRequest,
        blockers: list[str],
        asset_requirements: list[dict[str, Any]],
        information_requirements: list[dict[str, Any]],
    ) -> dict[str, Any]:
        score = 45
        if brief.website_url:
            score += 15
        if brief.conversion_goal:
            score += 15
        if brief.differentiators:
            score += 10
        if brief.business_name:
            score += 5
        score += sum(4 for item in asset_requirements if item["status"] == "ready")
        score += sum(3 for item in information_requirements if item["status"] == "ready")
        score -= len(blockers) * 10
        score = max(0, min(100, score))

        status = "READY_FOR_SETUP"
        if blockers:
            status = "BLOCKED"
        elif score < 75:
            status = "NEEDS_INPUT"

        next_steps = [
            "Fechar os campos criticos e revisar o blueprint gerado.",
            "Preparar a landing page e o evento de conversao antes da publicacao.",
            "Separar as pecas criativas e documentos em uma pasta unica do projeto.",
        ]
        if blockers:
            next_steps.insert(0, "Resolver os bloqueios de publicacao destacados na coluna de prontidao.")

        return {
            "score": score,
            "status": status,
            "blockers": blockers,
            "next_steps": next_steps[:5],
        }

    def _build_blockers(
        self,
        asset_requirements: list[dict[str, Any]],
        information_requirements: list[dict[str, Any]],
    ) -> list[str]:
        blockers = [
            item["item"]
            for item in information_requirements
            if item["priority"] == "HIGH" and item["status"] == "missing"
        ]
        blockers.extend(
            item["item"]
            for item in asset_requirements
            if item["priority"] == "HIGH" and item["status"] == "missing"
        )
        return blockers

    def _sanitize_filename(self, filename: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", filename.strip())
        cleaned = cleaned.strip(".-")
        return cleaned or "material"

    def _clean_phrase(self, value: str, max_words: int = 6) -> str:
        stop_chunks = re.split(r"\s+(?:com|em|para|no|na|onde|quando)\s+", value, maxsplit=1)
        candidate = stop_chunks[0].strip(" ,.;:-")
        words = re.findall(r"[A-Za-z0-9À-ÿ]+", candidate)
        return " ".join(words[:max_words]).strip()

    def _classify_uploaded_material(
        self,
        material_id: str,
        original_name: str,
        stored_name: str,
        content_type: str,
        size_bytes: int,
    ) -> dict[str, Any]:
        lower_name = original_name.lower()
        suffix = Path(original_name).suffix.lower()
        mapped_asset = None
        mapped_document = None
        kind = "other"
        category = "other"
        notes = None

        if content_type.startswith("video/") or suffix in {".mp4", ".mov", ".avi", ".webm"}:
            mapped_asset = "video"
            kind = "asset"
            category = "creative"
            notes = "Video util para Performance Max, YouTube ou extensoes visuais."
        elif "logo" in lower_name:
            mapped_asset = "logo"
            kind = "asset"
            category = "brand"
            notes = "Arquivo com cara de identidade visual da marca."
        elif suffix in {".csv", ".xml", ".tsv"} and any(
            token in lower_name for token in ("feed", "catalog", "catalogo", "produto", "products")
        ):
            mapped_asset = "feed"
            kind = "asset"
            category = "catalog"
            notes = "Parece um feed/catalogo aproveitavel para Shopping ou PMax."
        elif content_type.startswith("image/") or suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            mapped_asset = "lifestyle_images" if any(
                token in lower_name for token in ("lifestyle", "ambiente", "uso", "cliente")
            ) else "product_images"
            kind = "asset"
            category = "creative"
            notes = "Imagem aproveitavel para criativo, extensoes visuais ou PMax."
        elif any(token in lower_name for token in ("privacy", "privacidade", "lgpd")):
            mapped_document = "privacy_policy"
            kind = "document"
            category = "legal"
            notes = "Documento util para privacidade/compliance."
        elif any(token in lower_name for token in ("compliance", "politica", "termos", "terms")):
            mapped_document = "compliance_policy"
            kind = "document"
            category = "legal"
            notes = "Material com cara de politica, termo ou compliance."
        elif any(token in lower_name for token in ("preco", "price", "tabela", "pricing")):
            mapped_document = "price_list"
            kind = "document"
            category = "sales_enablement"
            notes = "Pode servir como base comercial para oferta e extensoes."
        elif any(token in lower_name for token in ("case", "resultado", "depo", "testimonial")):
            mapped_document = "case_studies"
            kind = "document"
            category = "proof"
            notes = "Material que pode reforcar prova e credibilidade."
        elif any(token in lower_name for token in ("oferta", "proposta", "apresentacao", "brief")):
            mapped_document = "offer_doc"
            kind = "document"
            category = "offer"
            notes = "Documento que ajuda a fechar proposta e copy."
        elif any(token in lower_name for token in ("script", "roteiro", "whatsapp", "comercial")):
            mapped_document = "sales_script"
            kind = "document"
            category = "sales_enablement"
            notes = "Pode orientar atendimento e promessas da campanha."
        elif any(token in lower_name for token in ("brand", "manual", "guia")):
            mapped_asset = "brand_guide"
            kind = "asset"
            category = "brand"
            notes = "Guia visual util para coerencia de criativos."

        return {
            "id": material_id,
            "original_name": original_name,
            "stored_name": stored_name,
            "content_type": content_type,
            "size_bytes": size_bytes,
            "kind": kind,
            "category": category,
            "mapped_asset": mapped_asset,
            "mapped_document": mapped_document,
            "notes": notes,
        }

    def _suggest_campaign_name(
        self,
        brief: CampaignStudioBriefRequest,
        campaign_type: str,
    ) -> str:
        service_slug = self._slugify(brief.product_or_service, 3)
        location_slug = self._slugify(brief.location, 2)
        objective_slug = brief.objective.lower()
        return f"{campaign_type.lower()}_{objective_slug}_{service_slug}_{location_slug}"

    def _slugify(self, text: str, max_words: int) -> str:
        words = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return "-".join(words[:max_words]) if words else "campanha"

    def _requirement(
        self,
        item: str,
        category: str,
        priority: str,
        status: str,
        reason: str,
        example: str | None = None,
    ) -> dict[str, Any]:
        return {
            "item": item,
            "category": category,
            "priority": priority,
            "status": status,
            "reason": reason,
            "example": example,
        }

    def _merge_unique(self, primary: list[str], secondary: list[str]) -> list[str]:
        return self._unique_items(list(primary) + list(secondary))

    def _unique_items(self, values: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = value.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append(normalized)
        return unique


campaign_studio_service = CampaignStudioService()
