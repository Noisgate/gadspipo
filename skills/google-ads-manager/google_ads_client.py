#!/usr/bin/env python3
"""
Google Ads Manager Client - Pré-configurado para sua conta Google Ads
Auto-load de credenciais via .env, retry logic, error classification, análise inteligente.
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests

# Auto-load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try to load from common locations
    env_paths = [
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(__file__), '.env.local'),
        '.env',
        '.env.local'
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path, override=False)
            break
except ImportError:
    # dotenv not installed, will use environment variables directly
    pass


class GoogleAdsManagerClient:
    """
    Cliente pré-configurado para Google Ads Manager.
    Auto-carrega credenciais de .env, implementa retry logic com exponential backoff,
    classifica erros, e sugere soluções.
    """

    def __init__(self):
        """Inicializa cliente com credenciais do .env"""
        self.client_id = os.getenv('GOOGLE_ADS_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_ADS_CLIENT_SECRET')
        self.refresh_token = os.getenv('GOOGLE_ADS_REFRESH_TOKEN')
        self.customer_id = os.getenv('GOOGLE_ADS_CUSTOMER_ID')
        self.developer_token = os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')

        self.access_token = None
        self.token_expires_at = None
        self.api_base_url = 'https://googleads.googleapis.com/v17'
        self.max_retries = 5
        self.base_wait_time = 1

    def verify_connection(self) -> bool:
        """
        Verifica se consegue conectar à Google Ads API.
        Retorna True se sucesso, False caso contrário.
        """
        try:
            if not all([self.client_id, self.client_secret]):
                print("❌ Credenciais incompletas no .env")
                return False

            # Tentar refresh token para verificar credenciais
            if self.refresh_token:
                self._refresh_access_token()
                if self.access_token:
                    print("✅ Conectado com sucesso à Google Ads API")
                    return True

            print("❌ Falha ao conectar - token OAuth2 inválido")
            return False
        except Exception as e:
            print(f"❌ Erro ao verificar conexão: {e}")
            return False

    def _refresh_access_token(self) -> bool:
        """Atualiza access token usando refresh token."""
        if not self.refresh_token:
            return False

        try:
            response = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'refresh_token': self.refresh_token,
                    'grant_type': 'refresh_token'
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                return True
            return False
        except Exception as e:
            print(f"❌ Erro ao atualizar token: {e}")
            return False

    def _ensure_token(self):
        """Garante que token está válido, refresha se necessário."""
        if not self.access_token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            self._refresh_access_token()

    def _classify_error(self, status_code: int, error_data: Dict) -> Tuple[str, List[str]]:
        """
        Classifica erro e sugere soluções.
        Retorna: (tipo_erro, [sugestão1, sugestão2, ...])
        """
        error_message = error_data.get('error', {}).get('message', '')

        # Authentication errors
        if status_code == 401 or 'invalid_grant' in error_message:
            return ('Authentication', [
                'Regenerar refresh token (OAuth2 flow)',
                'Verificar credenciais no .env',
                'Verificar se contas de serviço têm permissões'
            ])

        # Rate limiting
        if status_code == 429:
            return ('RateLimit', [
                'Aguardar 1-2 minutos',
                'Reduzir número de requisições simultâneas',
                'Revisar quota diária na Google Cloud Console'
            ])

        # Quota exceeded
        if 'RESOURCE_EXHAUSTED' in error_message or 'quota' in error_message.lower():
            return ('QuotaExceeded', [
                'Verificar quota mensal em Google Cloud Console',
                'Aguardar início do novo período de billing',
                'Aumentar quota se possível'
            ])

        # Invalid request
        if status_code == 400 or 'INVALID_ARGUMENT' in error_message:
            return ('InvalidRequest', [
                'Validar dados de entrada',
                'Verificar formato de campaign ID',
                'Consultar documentação de API'
            ])

        # Server errors
        if status_code >= 500:
            return ('ServerError', [
                'Aguardar alguns minutos',
                'Tentar novamente',
                'Verificar status do Google Ads API (status.cloud.google.com)'
            ])

        return ('Unknown', [
            'Verificar logs detalhados',
            'Consultar documentação de API',
            'Contatar suporte Google'
        ])

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Faz requisição com retry automático e exponential backoff.
        """
        self._ensure_token()

        if not self.access_token:
            return {
                'error_type': 'Authentication',
                'error_message': 'Falha ao obter access token',
                'suggestions': [
                    'Verificar se refresh token está correto',
                    'Tentar fazer novo login OAuth2',
                    'Verificar credenciais no .env'
                ]
            }

        url = f"{self.api_base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Developer-Token': self.developer_token,
            'Content-Type': 'application/json'
        }

        last_error = None

        for attempt in range(self.max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, timeout=30)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, json=data, timeout=30)
                elif method == 'PUT':
                    response = requests.put(url, headers=headers, json=data, timeout=30)
                else:
                    return {'error_message': f'Método HTTP desconhecido: {method}'}

                # Success
                if response.status_code in [200, 201]:
                    return {'success': True, 'data': response.json()}

                # Handle errors
                try:
                    error_data = response.json()
                except:
                    error_data = {'error': {'message': response.text}}

                error_type, suggestions = self._classify_error(response.status_code, error_data)

                # Don't retry on client errors (except rate limit)
                if response.status_code >= 400 and response.status_code != 429:
                    return {
                        'success': False,
                        'error_type': error_type,
                        'error_message': error_data.get('error', {}).get('message', response.text),
                        'status_code': response.status_code,
                        'suggestions': suggestions
                    }

                # Retry on 429 and 5xx
                last_error = (error_type, error_data, suggestions)
                if attempt < self.max_retries - 1:
                    wait_time = self.base_wait_time * (2 ** attempt)
                    time.sleep(wait_time)

            except requests.exceptions.Timeout:
                last_error = ('Timeout', None, ['Tentar novamente', 'Verificar conexão de internet'])
                if attempt < self.max_retries - 1:
                    wait_time = self.base_wait_time * (2 ** attempt)
                    time.sleep(wait_time)
            except requests.exceptions.RequestException as e:
                last_error = ('Connection', None, ['Verificar conexão de internet', 'Tentar novamente'])
                if attempt < self.max_retries - 1:
                    wait_time = self.base_wait_time * (2 ** attempt)
                    time.sleep(wait_time)

        # All retries exhausted
        if last_error:
            error_type, error_data, suggestions = last_error
            return {
                'success': False,
                'error_type': error_type,
                'error_message': 'Máximo de tentativas atingido',
                'suggestions': suggestions
            }

        return {'success': False, 'error_message': 'Erro desconhecido'}

    def list_campaigns(self, status: Optional[str] = None) -> Dict:
        """
        Lista campanhas, opcionalmente filtradas por status.
        Status: 'ENABLED', 'PAUSED', 'REMOVED'
        """
        # Simplified - em produção teria paginação
        endpoint = f'/customers/{self.customer_id}/googleAds:searchStream'

        query = '''
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.type,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions
            FROM campaign
        '''

        if status:
            query += f" WHERE campaign.status = '{status}'"

        data = {
            'query': query.strip()
        }

        result = self._make_request('POST', endpoint, data)

        if result.get('success'):
            return {
                'success': True,
                'campaigns': result.get('data', {}).get('results', [])
            }

        return result

    def get_campaign(self, campaign_id: str) -> Dict:
        """Obtém detalhes de uma campanha específica."""
        endpoint = f'/customers/{self.customer_id}/campaigns/{campaign_id}'
        result = self._make_request('GET', endpoint)

        if result.get('success'):
            return {
                'success': True,
                'campaign': result.get('data', {})
            }

        return result

    def create_campaign(self, name: str, campaign_type: str, daily_budget_micros: int) -> Dict:
        """
        Cria uma nova campanha.
        campaign_type: 'SEARCH', 'DISPLAY', 'SHOPPING', 'VIDEO', 'PERFORMANCE_MAX'
        daily_budget_micros: R$ em micros (ex: 500000000 = R$ 500)
        """
        endpoint = f'/customers/{self.customer_id}/campaigns'

        data = {
            'campaign': {
                'name': name,
                'type': campaign_type,
                'status': 'PAUSED',  # Começa pausada para revisão
                'daily_budget_amount_micros': daily_budget_micros,
                'advertising_channel_type': 'SEARCH'
            }
        }

        result = self._make_request('POST', endpoint, data)

        if result.get('success'):
            return {
                'success': True,
                'campaign_id': result.get('data', {}).get('resource_name', '')
            }

        return result

    def update_campaign_status(self, campaign_id: str, status: str) -> Dict:
        """
        Atualiza status da campanha.
        status: 'ENABLED', 'PAUSED', 'REMOVED'
        """
        endpoint = f'/customers/{self.customer_id}/campaigns/{campaign_id}'

        data = {
            'campaign': {
                'resource_name': f'customers/{self.customer_id}/campaigns/{campaign_id}',
                'status': status
            },
            'update_mask': 'status'
        }

        result = self._make_request('PUT', endpoint, data)

        if result.get('success'):
            return {
                'success': True,
                'message': f'Campanha {status.lower()}'
            }

        return result

    def update_campaign_budget(self, campaign_id: str, daily_budget_micros: int) -> Dict:
        """Atualiza budget diário da campanha."""
        endpoint = f'/customers/{self.customer_id}/campaigns/{campaign_id}'

        data = {
            'campaign': {
                'resource_name': f'customers/{self.customer_id}/campaigns/{campaign_id}',
                'daily_budget_amount_micros': daily_budget_micros
            },
            'update_mask': 'daily_budget_amount_micros'
        }

        result = self._make_request('PUT', endpoint, data)

        if result.get('success'):
            return {
                'success': True,
                'message': f'Budget atualizado para R$ {daily_budget_micros / 1_000_000:.2f}/dia'
            }

        return result

    def get_campaign_metrics(self, campaign_id: str, days: int = 30) -> Dict:
        """
        Obtém métricas de performance da campanha.
        Retorna: impressions, clicks, conversions, cost, ROAS, CPA, CTR
        """
        endpoint = f'/customers/{self.customer_id}/googleAds:searchStream'

        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')

        query = f'''
            SELECT
                campaign.id,
                campaign.name,
                metrics.impressions,
                metrics.clicks,
                metrics.conversions,
                metrics.cost_micros,
                metrics.conversion_value_micros
            FROM campaign
            WHERE campaign.id = {campaign_id}
            AND segments.date BETWEEN '{date_from}' AND '{date_to}'
        '''

        data = {'query': query.strip()}

        result = self._make_request('POST', endpoint, data)

        if result.get('success'):
            metrics = result.get('data', {}).get('results', [])
            if metrics:
                m = metrics[0].get('metrics', {})
                cost = m.get('cost_micros', 0) / 1_000_000
                conversions = m.get('conversions', 0)
                conversion_value = m.get('conversion_value_micros', 0) / 1_000_000

                return {
                    'success': True,
                    'metrics': {
                        'impressions': m.get('impressions', 0),
                        'clicks': m.get('clicks', 0),
                        'conversions': conversions,
                        'cost': cost,
                        'ctr': (m.get('clicks', 0) / m.get('impressions', 1) * 100) if m.get('impressions') else 0,
                        'cpc': (cost / m.get('clicks', 1)) if m.get('clicks') else 0,
                        'cpa': (cost / conversions) if conversions else 0,
                        'roas': (conversion_value / cost) if cost else 0
                    }
                }

        return result

    def generate_performance_report(self, days: int = 30) -> Dict:
        """
        Gera relatório completo de performance.
        """
        endpoint = f'/customers/{self.customer_id}/googleAds:searchStream'

        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')

        query = f'''
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                metrics.cost_micros,
                metrics.conversions,
                metrics.clicks,
                metrics.impressions,
                metrics.conversion_value_micros
            FROM campaign
            WHERE segments.date BETWEEN '{date_from}' AND '{date_to}'
            ORDER BY metrics.cost_micros DESC
        '''

        data = {'query': query.strip()}

        result = self._make_request('POST', endpoint, data)

        if result.get('success'):
            campaigns = result.get('data', {}).get('results', [])

            total_cost = sum(c.get('metrics', {}).get('cost_micros', 0) for c in campaigns) / 1_000_000
            total_conversions = sum(c.get('metrics', {}).get('conversions', 0) for c in campaigns)
            total_value = sum(c.get('metrics', {}).get('conversion_value_micros', 0) for c in campaigns) / 1_000_000

            return {
                'success': True,
                'report': {
                    'period': f'{date_from} a {date_to}',
                    'total_cost': total_cost,
                    'total_conversions': total_conversions,
                    'total_value': total_value,
                    'roas': (total_value / total_cost) if total_cost else 0,
                    'campaigns': campaigns
                }
            }

        return result
