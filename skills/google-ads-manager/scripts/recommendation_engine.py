#!/usr/bin/env python3
"""
Recommendation Engine - Gera recomendações inteligentes de otimização
"""

import sys
from pathlib import Path

# Adiciona parent directory ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google_ads_client import GoogleAdsManagerClient


def generate_recommendations(days=30):
    """Gera recomendações baseadas em análise de performance"""
    client = GoogleAdsManagerClient()

    print(f"💡 Gerando Recomendações (últimos {days} dias)...\n")

    result = client.generate_performance_report(days=days)

    if not result.get('success'):
        print(f"❌ Erro: {result.get('error_message')}")
        return

    report = result.get('report', {})
    campaigns = report.get('campaigns', [])

    recommendations = []

    # Análise de cada campanha
    for campaign in campaigns:
        c = campaign.get('campaign', {})
        m = campaign.get('metrics', {})

        cost = m.get('cost_micros', 0) / 1_000_000
        conversions = m.get('conversions', 0)
        value = m.get('conversion_value_micros', 0) / 1_000_000
        clicks = m.get('clicks', 0)
        impressions = m.get('impressions', 0)

        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cpc = (cost / clicks) if clicks > 0 else 0
        cpa = (cost / conversions) if conversions > 0 else 0
        roas = (value / cost) if cost > 0 else 0

        # Recomendação 1: Pausar low-ROAS
        if roas < 1.0 and cost > 100:
            recommendations.append({
                'priority': 1,
                'type': 'PAUSE',
                'title': f'Pausar "{c.get("name")}"',
                'description': f'ROAS {roas:.2f}x está abaixo de 1.0',
                'impact': f'Economizar R$ {cost:,.0f}/período',
                'confidence': 95
            })

        # Recomendação 2: Aumentar budget de high-ROAS
        elif roas > 3.0 and cost < 5000:
            recommendations.append({
                'priority': 2,
                'type': 'INCREASE_BUDGET',
                'title': f'Aumentar budget de "{c.get("name")}" em 50%',
                'description': f'ROAS {roas:.2f}x é excelente, escale a campanha',
                'impact': f'Potencial +R$ {cost * 0.5:,.0f}/período',
                'confidence': 88
            })

        # Recomendação 3: Otimizar CTR baixo
        elif ctr < 2.0 and impressions > 1000:
            recommendations.append({
                'priority': 3,
                'type': 'OPTIMIZE_CTR',
                'title': f'Otimizar CTR de "{c.get("name")}"',
                'description': f'CTR {ctr:.2f}% está abaixo da meta',
                'impact': f'Potencial +{2-ctr:.1f}% de cliques',
                'confidence': 72
            })

        # Recomendação 4: Revisar landing page
        elif cpa > 500 and conversions > 0:
            recommendations.append({
                'priority': 4,
                'type': 'REVIEW_LANDING_PAGE',
                'title': f'Revisar landing page de "{c.get("name")}"',
                'description': f'CPA R$ {cpa:.0f} pode ser reduzido',
                'impact': f'Potencial -20% no CPA',
                'confidence': 65
            })

    # Ordena por prioridade e confiança
    recommendations.sort(key=lambda r: (r['priority'], -r['confidence']))

    # Exibe recomendações
    print("="*70)
    print(f"💡 RECOMENDAÇÕES PRIORIZADAS ({len(recommendations)} total)")
    print("="*70)

    for i, rec in enumerate(recommendations[:10], 1):
        stars = '⭐' * (5 - rec['priority'])
        print(f"\n{i}. {stars} {rec['title']}")
        print(f"   📝 {rec['description']}")
        print(f"   📈 Impacto: {rec['impact']}")
        print(f"   🎯 Confiança: {rec['confidence']}%")

    print("\n" + "="*70)
    print(f"✅ Total de recomendações geradas: {len(recommendations)}")
    print("⚠️  Revise cada recomendação antes de implementar")
    print("="*70)


def get_quick_wins():
    """Identifica oportunidades rápidas de melhoria"""
    client = GoogleAdsManagerClient()

    print(f"⚡ QUICK WINS - Oportunidades Fáceis\n")

    result = client.generate_performance_report(days=7)

    if not result.get('success'):
        print(f"❌ Erro: {result.get('error_message')}")
        return

    report = result.get('report', {})
    campaigns = report.get('campaigns', [])

    print("Analisando últimos 7 dias...\n")

    quick_wins = []

    for campaign in campaigns:
        c = campaign.get('campaign', {})
        m = campaign.get('metrics', {})

        cost = m.get('cost_micros', 0) / 1_000_000
        clicks = m.get('clicks', 0)
        conversions = m.get('conversions', 0)

        # Quick win 1: Budget muito pequeno
        if cost < 50 and clicks > 0:
            quick_wins.append(f"📌 {c.get('name')}: Aumentar budget (apenas R$ {cost:.0f}/semana)")

        # Quick win 2: Conversão alta com budget pequeno
        if conversions > 5 and cost < 100:
            quick_wins.append(f"🎯 {c.get('name')}: Campanha pronta para escalar")

    if quick_wins:
        print("💡 OPORTUNIDADES RÁPIDAS:\n")
        for win in quick_wins:
            print(f"  {win}")
    else:
        print("✅ Nenhuma quick win óbvia encontrada")

    print()


if __name__ == '__main__':
    # Exemplos de uso
    print("🚀 Recommendation Engine\n")

    generate_recommendations(days=30)
    print("\n")
    get_quick_wins()
