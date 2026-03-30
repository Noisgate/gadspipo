#!/usr/bin/env python3
"""
Campaign Manager - CRUD operations para campanhas Google Ads
"""

import sys
from pathlib import Path

# Adiciona parent directory ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google_ads_client import GoogleAdsManagerClient


def list_campaigns(status=None):
    """Lista todas as campanhas, opcionalmente filtradas por status"""
    client = GoogleAdsManagerClient()

    print("🔄 Buscando campanhas...")
    result = client.list_campaigns(status=status)

    if not result.get('success'):
        print(f"❌ Erro: {result.get('error_message')}")
        if 'suggestions' in result:
            print("\n💡 Sugestões:")
            for i, sugg in enumerate(result['suggestions'], 1):
                print(f"   {i}. {sugg}")
        return

    campaigns = result.get('campaigns', [])
    print(f"\n📊 Total de campanhas: {len(campaigns)}")

    if campaigns:
        for campaign in campaigns[:10]:  # Mostra primeiras 10
            c = campaign.get('campaign', {})
            m = campaign.get('metrics', {})
            print(f"\n  📌 {c.get('name')}")
            print(f"     Status: {c.get('status')}")
            print(f"     Spend: R$ {m.get('cost_micros', 0) / 1_000_000:.2f}")
            print(f"     Impressões: {m.get('impressions', 0)}")
            print(f"     Cliques: {m.get('clicks', 0)}")


def analyze_campaign(campaign_id, days=30):
    """Analisa performance de uma campanha"""
    client = GoogleAdsManagerClient()

    print(f"🔄 Analisando campanha {campaign_id} (últimos {days} dias)...")
    result = client.get_campaign_metrics(campaign_id, days=days)

    if not result.get('success'):
        print(f"❌ Erro: {result.get('error_message')}")
        return

    metrics = result.get('metrics', {})

    print(f"\n📊 Análise de Performance")
    print(f"  Impressões: {metrics.get('impressions', 0):,}")
    print(f"  Cliques: {metrics.get('clicks', 0):,}")
    print(f"  CTR: {metrics.get('ctr', 0):.2f}%")
    print(f"  Conversões: {metrics.get('conversions', 0):.0f}")
    print(f"  CPC: R$ {metrics.get('cpc', 0):.2f}")
    print(f"  CPA: R$ {metrics.get('cpa', 0):.2f}")
    print(f"  ROAS: {metrics.get('roas', 0):.2f}x")
    print(f"  Gasto Total: R$ {metrics.get('cost', 0):.2f}")


def pause_campaign(campaign_id):
    """Pausa uma campanha"""
    client = GoogleAdsManagerClient()

    print(f"⏸️  Pausando campanha {campaign_id}...")
    result = client.update_campaign_status(campaign_id, 'PAUSED')

    if result.get('success'):
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ Erro: {result.get('error_message')}")


def resume_campaign(campaign_id):
    """Retoma uma campanha pausada"""
    client = GoogleAdsManagerClient()

    print(f"▶️  Retomando campanha {campaign_id}...")
    result = client.update_campaign_status(campaign_id, 'ENABLED')

    if result.get('success'):
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ Erro: {result.get('error_message')}")


def update_budget(campaign_id, daily_budget_reais):
    """Atualiza budget diário da campanha"""
    client = GoogleAdsManagerClient()

    daily_budget_micros = int(daily_budget_reais * 1_000_000)
    print(f"💰 Atualizando budget para R$ {daily_budget_reais:.2f}/dia...")

    result = client.update_campaign_budget(campaign_id, daily_budget_micros)

    if result.get('success'):
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ Erro: {result.get('error_message')}")


if __name__ == '__main__':
    # Exemplos de uso
    print("🚀 Campaign Manager\n")

    # Listar campanhas ativas
    list_campaigns(status='ENABLED')
