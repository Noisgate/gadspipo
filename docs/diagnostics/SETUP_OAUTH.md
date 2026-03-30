# Google Ads OAuth Setup Guide

## Requisitos

- Conta Google Ads ativa
- Projeto no Google Cloud Console com Google Ads API habilitada
- Python 3.8+ com google-ads instalado

## Passo a Passo

### 1. Criar Credenciais OAuth

1. Acesse [Google Cloud Console](https://console.cloud.google.com)
2. Crie ou selecione um projeto
3. Habilite a **Google Ads API**
4. Va em **Credenciais** > **Criar Credenciais** > **ID do cliente OAuth**
5. Tipo: **Aplicativo para Desktop**
6. Anote o **Client ID** e **Client Secret**

### 2. Gerar Refresh Token

1. Acesse [OAuth Playground](https://developers.google.com/oauthplayground/)
2. Clique na engrenagem (Settings)
3. Marque **Use your own OAuth credentials**
4. Coloque seu **Client ID** e **Client Secret**
5. No campo de scopes, adicione: `https://www.googleapis.com/auth/adwords`
6. Clique em **Authorize APIs**
7. Complete o fluxo de autorizacao
8. Copie o **Refresh Token** gerado

### 3. Obter Developer Token

1. Acesse [Google Ads](https://ads.google.com)
2. Va em **Ferramentas e Configuracoes** > **Centro de API**
3. Copie o **Developer Token**

### 4. Configurar Arquivo YAML

```yaml
client_id: SEU_CLIENT_ID.apps.googleusercontent.com
client_secret: SEU_CLIENT_SECRET
refresh_token: SEU_REFRESH_TOKEN
developer_token: SEU_DEVELOPER_TOKEN
login_customer_id: "SEU_CUSTOMER_ID_SEM_HIFENS"
use_proto_plus: true
```

Salve como `~/google-ads.yaml`

### 5. Configurar Variaveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```bash
cp skills/google-ads-manager/.env.example skills/google-ads-manager/.env
```

### 6. Testar Conexao

```python
from google.ads.googleads.client import GoogleAdsClient

client = GoogleAdsClient.load_from_storage("~/google-ads.yaml")
ga_service = client.get_service("GoogleAdsService")
customer_id = "SEU_CUSTOMER_ID"

query = "SELECT campaign.name FROM campaign"
results = ga_service.search_stream(customer_id=customer_id, query=query)

for batch in results:
    for row in batch.results:
        print(row.campaign.name)
```

## Notas Importantes

- O **Refresh Token** deve ser gerado com o MESMO Client ID e Client Secret
- Nunca commite credenciais reais no repositorio
- Use `.env` e `.gitignore` para proteger credenciais
- O Customer ID deve ser sem hifens (ex: 8960664207, nao 896-066-4207)
- O `use_proto_plus: true` e obrigatorio para versoes recentes da API

## Troubleshooting

### Erro: unauthorized_client
- O Refresh Token foi gerado com um Client ID diferente
- Solucao: Gere um novo Refresh Token com as credenciais corretas

### Erro: UNRECOGNIZED_FIELD
- Campo nao existe na versao da API em uso
- Solucao: Verifique a documentacao da versao atual da API

### Erro: 404 na REST API
- URL do endpoint incorreta
- Solucao: Use a versao correta (ex: v14, v16, v23)
