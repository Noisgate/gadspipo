#!/usr/bin/env python3
"""
Performance Analyzer - Análise de performance de campanhas
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Adiciona parent directory ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from google_ads_client import GoogleAdsManagerClient


def analyze_all_campaigns(days=30):
    """Analisa performance de todas as campanhas"""
    client = GoogleAdsManagerClient()

    print(f"📊 Análise de Performance (últimos {days} dias)\n")

    result = client.generate_performance_report(days=days)

    if not result.get('success'):
        print(f"❌ Erro: {result.get('error_message')}")
        if 'suggestions' in result:
            print("\n💡 Sugestões:")
            for i, sugg in enumerate(result['suggestions'], 1):
                print(f"   {i}. {sugg}")
        return

    report = result.get('report', {})

    # Header
    print("="*70)
    print(f"Período: {report.get('period')}")
    print("="*70)

    # Summary
    total_cost = report.get('total_cost', 0)
    total_conversions = report.get('total_conversions', 0)
    total_value = report.get('total_value', 0)
    roas = report.get('roas', 0)

    print(f"\n💰 RESUMO FINANCEIRO")
    print(f"  Gasto Total: R$ {total_cost:,.2f}")
    print(f"  Conversões: {total_conversions:.0f}")
    print(f"  Valor em Conversões: R$ {total_value:,.2f}")
    print(f"  ROAS Geral: {roas:.2f}x")

    # Top performers vs underperformers
    campaigns = report.get('campaigns', [])
    if campaigns:
        print(f"\n📈 TOP PERFORMERS (ROAS > 2.0)")
        top = [c for c in campaigns if c.get('metrics', {}).get('conversion_value_micros', 0) / max(c.get('metrics', {}).get('cost_micros', 1), 1) > 2.0]
        for c in top[:3]:
            m = c.get('metrics', {})
            print(f"  ✅ {c.get('campaign', {}).get('name')}")

        print(f"\n⚠️  UNDERPERFORMERS (ROAS < 1.5)")
        bottom = [c for c in campaigns if c.get('metrics', {}).get('conversion_value_micros', 0) / max(c.get('metrics', {}).get('cost_micros', 1), 1) < 1.5]
        for c in bottom[:3]:
            m = c.get('metrics', {})
            print(f"  ❌ {c.get('campaign', {}).get('name')}")

    print("\n" + "="*70)


def get_insights(days=30):
    """Gera insights sobre o portfólio de campanhas"""
    client = GoogleAdsManagerClient()

    print(f"💡 INSIGHTS (últimos {days} dias)\n")

    result = client.generate_performance_report(days=days)

    if not result.get('success'):
        print(f"❌ Erro: {result.get('error_message')}")
        return

    report = result.get('report', {})
    campaigns = report.get('campaigns', [])

    if not campaigns:
        print("Nenhuma campanha encontrada")
        return

    # Calcula insights
    total_cost = report.get('total_cost', 0)
    roas_list = [c.get('metrics', {}).get('conversion_value_micros', 0) / max(c.get('metrics', {}).get('cost_micros', 1), 1) for c in campaigns]
    avg_roas = sum(roas_list) / len(roas_list) if roas_list else 0

    print("🎯 RECOMENDAÇÕES PRIORITÁRIAS:\n")

    # Insight 1: Campanhas low-ROI
    low_roas = [c for c in campaigns if c.get('metrics', {}).get('conversion_value_micros', 0) / max(c.get('metrics', {}).get('cost_micros', 1), 1) < 1.0]
    if low_roas:
        total_waste = sum(c.get('metrics', {}).get('cost_micros', 0) for c in low_roas) / 1_000_000
        print(f"1. ⭐⭐⭐ PAUSAR {len(low_roas)} campanhas com ROAS < 1.0")
        print(f"   Impacto: Economizar R$ {total_waste:,.2f}/período")
        print(f"   Campanhas: {', '.join(c.get('campaign', {}).get('name', 'N/A') for c in low_roas[:3])}")

    # Insight 2: Alocar mais budget aos top performers
    high_roas = [c for c in campaigns if c.get('metrics', {}).get('conversion_value_micros', 0) / max(c.get('metrics', {}).get('cost_micros', 1), 1) > 3.0]
    if high_roas:
        print(f"\n2. ⭐⭐ AUMENTAR BUDGET de {len(high_roas)} campanhas com ROAS > 3.0")
        print(f"   Recomendação: +50% de budget para escalabilidade")
        print(f"   Campanhas: {', '.join(c.get('campaign', {}).get('name', 'N/A') for c in high_roas[:3])}")

    print(f"\n3. ⭐ MONITORAR campanhas com ROAS {avg_roas:.2f}x")
    print(f"   Ação: Testar variações de ad copy e landing pages")

    print("\n" + "="*70)


if __name__ == '__main__':
    # Exemplos de uso
    print("🚀 Performance Analyzer\n")

    analyze_all_campaigns(days=30)
    print("\n")
    get_insights(days=30)
