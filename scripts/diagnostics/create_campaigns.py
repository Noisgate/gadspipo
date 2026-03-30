#!/usr/bin/env python3
"""
Script para criar 2 novas campanhas Google Ads
Uso: python3 create_campaigns.py
"""

import sys
from google.ads.googleads.client import GoogleAdsClient

def create_campaigns():
    """Cria 2 novas campanhas no Google Ads"""
    
    # Carregar cliente
    client = GoogleAdsClient.load_from_storage("/Users/felipeassinato/google-ads.yaml")
    customer_id = "8960664207"
    campaign_service = client.get_service("CampaignService")
    
    print("\n" + "=" * 80)
    print("🚀 CRIANDO 2 NOVAS CAMPANHAS GOOGLE ADS")
    print("=" * 80)
    
    # Dados das campanhas
    campaigns_data = [
        {
            "name": "LEAD_GENERATION_2026",
            "budget_id": "customers/8960664207/campaignBudgets/15468325561",
            "descricao": "Lead Generation - R$ 10/dia"
        },
        {
            "name": "BRAND_AWARENESS_BOATSP",
            "budget_id": "customers/8960664207/campaignBudgets/15458348123",
            "descricao": "Brand Awareness - R$ 15/dia"
        }
    ]
    
    # Criar cada campanha
    for idx, campaign_info in enumerate(campaigns_data, 1):
        print(f"\n{idx}. {campaign_info['descricao']}")
        print("-" * 80)
        
        try:
            # Construir a campanha - FORMA MÍNIMA
            campaign = {
                "name": campaign_info["name"],
                "status": 2,  # ENABLED
                "campaign_budget": campaign_info["budget_id"],
                "advertising_channel_type": 2,  # SEARCH
                "bidding_strategy_type": 9,  # TARGET_CPA
            }
            
            # Executar mutação
            response = campaign_service.mutate_campaigns(
                customer_id=customer_id,
                operations=[{"create": campaign}]
            )
            
            if response.results:
                resource_name = response.results[0].resource_name
                campaign_id = resource_name.split('/')[-1]
                
                print(f"   ✅ CRIADA COM SUCESSO!")
                print(f"   ID: {campaign_id}")
                print(f"   URL: https://ads.google.com/aw/campaigns/{campaign_id}")
            else:
                print(f"   ⚠️ Sem resultados na resposta")
        
        except Exception as e:
            error_msg = str(e)
            
            if "already exists" in error_msg.lower():
                print(f"   ⚠️ Campanha já existe!")
            elif "invalid argument" in error_msg.lower():
                print(f"   ❌ Erro - Campo faltando ou inválido")
                # Tentar extrair qual campo
                if "field_name:" in error_msg:
                    import re
                    match = re.search(r'field_name: "([^"]+)"', error_msg)
                    if match:
                        print(f"      Campo: {match.group(1)}")
            else:
                print(f"   ❌ Erro: {error_msg[:100]}")
    
    # Verificação final
    print("\n\n" + "=" * 80)
    print("📊 CAMPANHAS ATIVAS")
    print("=" * 80)
    
    try:
        ga_service = client.get_service("GoogleAdsService")
        
        query = """
        SELECT
            campaign.name,
            campaign.id,
            campaign_budget.amount_micros
        FROM campaign
        WHERE campaign.status = 'ENABLED'
        ORDER BY campaign.id DESC
        """
        
        results = ga_service.search_stream(customer_id=customer_id, query=query)
        
        total_budget = 0
        count = 0
        
        for batch in results:
            for row in batch.results:
                c = row.campaign
                b = row.campaign_budget
                budget = b.amount_micros / 1_000_000
                
                count += 1
                total_budget += budget
                
                print(f"\n✅ {c.name}")
                print(f"   ID: {c.id}")
                print(f"   Orçamento: R$ {budget:.2f}/dia")
        
        print(f"\n{'=' * 80}")
        print(f"📊 RESUMO FINAL")
        print(f"{'=' * 80}")
        print(f"Total de campanhas ATIVAS: {count}")
        print(f"Orçamento diário TOTAL: R$ {total_budget:.2f}")
        print(f"{'=' * 80}\n")
        
        return True
    
    except Exception as e:
        print(f"Erro na verificação: {e}")
        return False

if __name__ == "__main__":
    try:
        success = create_campaigns()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)

