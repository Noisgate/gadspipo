#!/usr/bin/env python3
"""
Google Ads Manager Setup Script - Verifica e configura o ambiente automaticamente
Roda uma única vez - após configuração inicial, pula os passos já concluídos
"""

import os
import sys
import shutil
from pathlib import Path

class GoogleAdsManagerSetup:
    def __init__(self):
        self.skill_dir = Path(__file__).parent
        self.project_dir = Path.cwd()
        self.env_file = self.project_dir / '.env'
        self.env_example = self.skill_dir / '.env.example'
        self.setup_marker = self.project_dir / '.google_ads_manager_setup_done'

    def is_setup_complete(self):
        """Verifica se setup já foi feito"""
        return self.setup_marker.exists()

    def mark_setup_complete(self):
        """Marca setup como completo"""
        self.setup_marker.touch()

    def copy_env_template(self):
        """Copia .env.example para .env se não existir"""
        if self.env_file.exists():
            print("✅ .env já existe - pulando cópia")
            return True

        if not self.env_example.exists():
            print("❌ .env.example não encontrado em", self.env_example)
            return False

        try:
            shutil.copy(self.env_example, self.env_file)
            print(f"✅ Copiado: {self.env_example} → {self.env_file}")
            print("📝 IMPORTANTE: Edite .env com suas credenciais do Google Ads!")
            print(f"   nano {self.env_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao copiar .env: {e}")
            return False

    def check_env_configured(self):
        """Verifica se .env tem valores reais (não template)"""
        if not self.env_file.exists():
            return False

        try:
            with open(self.env_file, 'r') as f:
                content = f.read()
                # Verifica se tem credenciais preenchidas
                if 'your_refresh_token_here' in content or 'GOOGLE_ADS_REFRESH_TOKEN=' in content and '=' in content:
                    return False
            return True
        except:
            return False

    def install_dependencies(self):
        """Instala dependências do requirements.txt"""
        requirements_file = self.skill_dir / 'requirements.txt'

        if not requirements_file.exists():
            print("⚠️  requirements.txt não encontrado")
            return False

        print("📦 Instalando dependências...")
        exit_code = os.system(f'pip install -q -r {requirements_file}')

        if exit_code == 0:
            print("✅ Dependências instaladas")
            return True
        else:
            print("❌ Erro ao instalar dependências")
            return False

    def run(self):
        """Executa setup completo"""
        print("\n" + "="*60)
        print("🚀 Google Ads Manager - Setup Automático")
        print("="*60 + "\n")

        # Verifica se já foi feito
        if self.is_setup_complete():
            print("✅ Setup já foi executado neste projeto")
            print("   Arquivo marcador: .google_ads_manager_setup_done\n")
            return True

        print("🔍 Executando setup inicial...\n")

        # Step 1: Copy .env
        print("📋 Step 1/3: Verificando arquivo de configuração")
        if not self.copy_env_template():
            return False

        # Step 2: Check if configured
        print("\n📋 Step 2/3: Verificando configuração")
        if self.env_file.exists():
            if self.check_env_configured():
                print("✅ .env está configurado com credenciais reais")
            else:
                print("⚠️  .env ainda usa valores template")
                print("   Por favor, edite .env com suas credenciais do Google Ads:")
                print(f"   nano {self.env_file}")
                print("\n   Você precisa de:")
                print("   - GOOGLE_ADS_CLIENT_ID: Google Cloud Console")
                print("   - GOOGLE_ADS_CLIENT_SECRET: Google Cloud Console")
                print("   - GOOGLE_ADS_REFRESH_TOKEN: OAuth2 flow")
                print("   - GOOGLE_ADS_CUSTOMER_ID: Sua conta Google Ads")
                print("   - GOOGLE_ADS_DEVELOPER_TOKEN: Google Ads API")
                response = input("\n   Continuar mesmo assim? (s/n): ").strip().lower()
                if response != 's':
                    print("❌ Setup cancelado")
                    return False

        # Step 3: Install dependencies
        print("\n📋 Step 3/3: Instalando dependências")
        if not self.install_dependencies():
            return False

        # Mark as complete
        self.mark_setup_complete()

        print("\n" + "="*60)
        print("✅ Setup Completo!")
        print("="*60)
        print("\nAgora você pode usar google-ads-manager:")
        print("  from google_ads_client import GoogleAdsManagerClient")
        print("  client = GoogleAdsManagerClient()")
        print("\nPróximas vezes que rodar este script, ele vai pular as etapas já feitas.")
        print()

        return True


if __name__ == '__main__':
    setup = GoogleAdsManagerSetup()
    success = setup.run()
    sys.exit(0 if success else 1)
