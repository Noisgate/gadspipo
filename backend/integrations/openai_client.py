"""
OpenAI integration helpers.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from config import settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency is available in runtime
    OpenAI = None

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Small wrapper for optional OpenAI-powered enrichments."""

    def __init__(self) -> None:
        self._client = None
        if OpenAI and settings.OPENAI_API_KEY:
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def enrich_campaign_studio_brief(
        self,
        brief: dict[str, Any],
        fallback_payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Optionally enrich campaign studio output with extra messaging ideas.

        The app keeps working without OpenAI. This method only runs when an API
        key is configured and quietly falls back on errors.
        """
        if not self._client:
            return None

        system_prompt = (
            "Voce e um estrategista senior de Google Ads e CRO. "
            "Responda em JSON valido, sem markdown, com as chaves: "
            "strategic_summary, headline_ideas, description_ideas, questions_to_validate."
        )
        user_prompt = json.dumps(
            {
                "brief": brief,
                "fallback": {
                    "summary": fallback_payload["briefing_digest"]["summary"],
                    "angles": fallback_payload["messaging"]["angles"],
                    "headline_ideas": fallback_payload["messaging"]["headline_ideas"],
                    "description_ideas": fallback_payload["messaging"]["description_ideas"],
                },
            },
            ensure_ascii=False,
        )

        try:
            response = self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                return None
            return parsed
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            logger.warning("OpenAI enrichment unavailable for campaign studio: %s", exc)
            return None

    def diagnose_campaign_idea(
        self,
        request_text: str,
        fallback_payload: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Optionally turn a free-form campaign idea into a cleaner structured brief.

        The fallback rules engine remains the source of truth. AI only enriches the
        analyzer when an API key is configured.
        """
        if not self._client:
            return None

        system_prompt = (
            "Voce e um estrategista senior de Google Ads. "
            "Leia a ideia livre do usuario e responda em JSON valido, sem markdown, "
            "com as chaves: summary, suggested_brief, questions_to_clarify, next_steps. "
            "O objeto suggested_brief pode conter: business_name, product_or_service, "
            "offer, objective, intention, target_audience, location, budget_amount, "
            "budget_period, website_url, conversion_goal, differentiators, notes."
        )
        user_prompt = json.dumps(
            {
                "request": request_text,
                "fallback": fallback_payload,
            },
            ensure_ascii=False,
        )

        try:
            response = self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                return None
            return parsed
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            logger.warning("OpenAI idea diagnosis unavailable for campaign studio: %s", exc)
            return None

    def refine_recommendation_proposal(
        self,
        proposal: dict[str, Any],
        notes: str,
    ) -> dict[str, Any] | None:
        """
        Optionally refine a Google Ads proposal with free-form user feedback.

        The proposal engine works without OpenAI. When available, AI only helps
        rewrite the proposal with clearer rationale and sharper discussion points.
        """
        if not self._client or not notes.strip():
            return None

        system_prompt = (
            "Voce e um estrategista senior de Google Ads. "
            "Refine uma proposta ja estruturada com base no feedback do usuario. "
            "Responda em JSON valido, sem markdown, com as chaves: "
            "summary, why_this_proposal, suggested_changes, risks, discussion_points, "
            "approval_checklist, refinement_summary."
        )
        user_prompt = json.dumps(
            {
                "proposal": proposal,
                "user_feedback": notes,
            },
            ensure_ascii=False,
        )

        try:
            response = self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                return None
            return parsed
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            logger.warning("OpenAI proposal refinement unavailable: %s", exc)
            return None


openai_client = OpenAIClient()
