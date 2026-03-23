# Epic PRD: Google Ads Copilot for Business Owners

## 1. Epic Name

Google Ads Copilot for Business Owners

## 2. Goal

### Problem

Donos de negócio querem anunciar no Google Ads sem depender integralmente de gestores de tráfego, mas o processo atual exige conhecimento técnico, leitura manual de briefings, criação de campanhas, revisão de anúncios, definição de palavras-chave e otimizações recorrentes. Isso torna a operação lenta, cara e inconsistente, especialmente para pequenas e médias empresas no Brasil. Mesmo quando o dono já possui materiais de campanha, esses insumos ficam dispersos em documentos, apresentações, PDFs e links, sem uma forma estruturada de virarem campanhas de qualidade. Além disso, publicar mudanças erradas ou otimizar com base em tracking fraco pode desperdiçar orçamento e reduzir confiança no canal.

### Solution

Criar uma plataforma web minimalista que conecta Google Drive e Google Ads, lê os documentos de uma pasta escolhida pelo usuário, transforma esses insumos em um briefing estruturado e gera campanhas do Google Ads com foco inicial em Search. A plataforma apresenta rascunhos claros, explica as decisões tomadas pela IA, e só publica campanhas ou aplica otimizações após aprovação explícita do dono do negócio. Depois da publicação, o sistema monitora performance continuamente e sugere melhorias de orçamento, palavras-chave, negativas, anúncios e estrutura, sempre dentro de limites configurados e com aprovação humana.

### Impact

O produto reduz o tempo entre briefing e campanha publicada, aumenta a consistência estratégica entre documentos e campanhas, e entrega ao dono do negócio uma forma mais simples de operar mídia paga sem perder controle. O impacto esperado é aumentar a velocidade de lançamento de campanhas, elevar a qualidade dos drafts gerados, reduzir desperdício por decisões manuais ruins e criar uma base escalável para futura expansão multi-país e multi-idioma. No curto prazo, o principal valor é operacional e de confiança; no médio prazo, o valor passa a incluir ganhos recorrentes de performance via recomendações aprovadas.

## 3. User Personas

### Persona Primaria: Dono de negocio

- Empresario ou operador principal de uma pequena ou media empresa.
- Tem responsabilidade direta sobre crescimento, vendas e orcamento de marketing.
- Nao domina profundamente Google Ads, mas entende os resultados que quer obter.
- Valoriza simplicidade, clareza e controle sobre o que sera publicado.
- Possui materiais de campanha em Google Drive e quer transforma-los em acao rapidamente.

### Persona Secundaria: Dono de negocio com operacao ativa de marketing

- Ja anuncia ou ja contratou gestao de trafego em algum momento.
- Quer comparar sugestoes, ganhar velocidade e reduzir dependencia operacional.
- Valoriza dashboards claros, historico de decisoes e recomendacoes priorizadas.

## 4. High-Level User Journeys

### Jornada 1: Onboarding e conexao

1. O usuario cria conta e acessa o produto em PT-BR.
2. O usuario conecta sua conta Google Ads.
3. O usuario conecta sua conta Google Drive.
4. O usuario escolhe a pasta que contem os documentos da campanha.
5. O sistema confirma integracoes, verifica permissoes e exibe status de prontidao.

### Jornada 2: Ingestao e entendimento do contexto

1. O sistema le os arquivos suportados da pasta selecionada.
2. O sistema identifica briefing, oferta, pagina de destino, criativos, restricoes e sinais ausentes.
3. O sistema gera um resumo estruturado do contexto da campanha.
4. O usuario revisa esse resumo e corrige, quando necessario.

### Jornada 3: Criacao de campanha

1. O usuario escolhe o objetivo principal da campanha, como leads, vendas, agendamentos ou outro KPI configuravel.
2. O sistema gera um draft de campanha com foco inicial em Search, incluindo estrutura, grupos, keywords, negativas, anuncios e extensoes.
3. O sistema explica a logica de cada recomendacao e destaca riscos ou lacunas.
4. O usuario aprova, rejeita ou ajusta configuracoes antes da publicacao.
5. O sistema publica apenas os itens aprovados.

### Jornada 4: Otimizacao continua com aprovacao

1. O sistema monitora campanhas ativas em janelas definidas.
2. O sistema detecta oportunidades, como keywords sem conversao, anuncios fracos, budgets mal distribuidos ou grupos incompletos.
3. O sistema cria recomendacoes ranqueadas por impacto e confianca.
4. O usuario aprova ou rejeita cada recomendacao.
5. O sistema aplica apenas as mudancas aprovadas e registra tudo em auditoria.

### Jornada 5: Acompanhamento e confianca

1. O usuario acompanha status da conta, campanhas em draft, campanhas publicadas e sugestoes pendentes.
2. O usuario visualiza historico de aprovacoes, alteracoes feitas e rationale da IA.
3. O usuario ajusta limites operacionais, como budget maximo, regioes, termos proibidos e tipos de campanha permitidos.

## 5. Business Requirements

### Functional Requirements

- O produto deve permitir conexao autenticada com Google Ads.
- O produto deve permitir conexao autenticada com Google Drive.
- O produto deve permitir ao usuario selecionar uma pasta especifica do Google Drive como fonte da campanha.
- O produto deve suportar leitura inicial de documentos relevantes, incluindo pelo menos Google Docs, PDF, texto e links informados pelo usuario.
- O produto deve classificar automaticamente os insumos em categorias como briefing, oferta, pagina de destino, criativos, brand rules e restricoes.
- O produto deve gerar um resumo estruturado do contexto antes de criar qualquer campanha.
- O produto deve permitir ao usuario escolher o objetivo principal da campanha.
- O produto deve suportar no MVP a geracao de campanhas Search.
- O produto deve gerar drafts contendo no minimo nome da campanha, objetivo, grupos, keywords, negativas, anuncios e extensoes relevantes.
- O produto deve apresentar explicacoes legiveis sobre por que cada campanha, grupo ou sugestao foi criado.
- O produto deve calcular e exibir um campaign readiness score antes da publicacao.
- O produto deve bloquear publicacao quando faltarem insumos minimos definidos, como oferta clara, pagina de destino ou configuracao de objetivo.
- O produto deve exigir aprovacao explicita antes de publicar uma campanha.
- O produto deve monitorar campanhas publicadas e gerar sugestoes continuas de otimizacao.
- O produto deve exigir aprovacao explicita antes de aplicar qualquer otimizacao.
- O produto deve manter historico de drafts, aprovacoes, publicacoes e recomendacoes.
- O produto deve permitir configuracao de guardrails, incluindo budget maximo, localizacao alvo e termos proibidos.
- O produto deve exibir uma interface minimalista com foco em clareza, aprovacao e status operacional.
- O produto deve nascer em PT-BR para usuarios do Brasil.
- O produto deve ser desenhado para expansao futura a multi-pais e multi-idioma sem refatoracao estrutural profunda.

### Non-Functional Requirements

- O sistema deve registrar 100% das publicacoes e alteracoes aprovadas em trilha de auditoria.
- O sistema nao deve aplicar mudancas sem aprovacao do usuario no MVP.
- O tempo de geracao do primeiro draft apos leitura valida dos documentos deve ser menor que 15 minutos em 95% dos casos.
- A interface principal deve ser utilizavel em desktop e mobile e atingir pelo menos 90 de accessibility score em auditoria padrao.
- Credenciais de Google Ads e Google Drive devem ser armazenadas com criptografia e menor escopo de permissao possivel.
- Logs nao devem expor segredos, tokens, IDs sensiveis ou conteudo integral de documentos privados.
- O sistema deve suportar retries e tratamento de falhas para quotas e indisponibilidade temporaria das APIs externas.
- O sistema deve separar claramente ambiente de desenvolvimento, homologacao e producao.
- O sistema deve permitir observabilidade minima com logs estruturados, status de jobs e rastreabilidade de cada recomendacao.
- O sistema deve ser projetado para suportar internacionalizacao futura de interface e geracao de campanhas.

## 6. Success Metrics

- Reduzir o tempo medio entre pasta conectada e primeiro draft de campanha para menos de 15 minutos.
- Gerar drafts tecnicamente completos em pelo menos 90% dos casos em que a pasta contenha briefing, oferta e pagina de destino utilizaveis.
- Garantir que 100% das publicacoes e otimizações no MVP ocorram somente apos aprovacao explicita do usuario.
- Alcancar taxa de aprovacao de pelo menos 60% das recomendacoes de otimização geradas nos primeiros 90 dias de uso ativo.
- Fazer com que pelo menos 70% dos usuarios que conectarem Ads e Drive concluam a publicacao da primeira campanha em ate 7 dias.
- Reduzir em pelo menos 30% o tempo operacional gasto pelo dono do negocio para colocar uma nova campanha no ar, comparado ao processo manual declarado no onboarding.

## 7. Out of Scope

- Publicacao automatica sem aprovacao humana.
- Otimizacao automatica sem aprovacao humana.
- Suporte inicial a Meta Ads, TikTok Ads, LinkedIn Ads ou outras plataformas.
- Suporte inicial a campanhas alem de Search no MVP.
- Criacao automatica de pecas visuais complexas ou edicao de imagens no MVP.
- Recursos multi-cliente e hierarquia de agencia no MVP.
- Operacao multi-pais e multi-idioma na primeira versao.
- Reestruturacao automatica total de contas legadas sem revisao humana.
- Promessas de performance garantida, como CPA fixo ou ROAS minimo garantido.

## 8. Business Value

**High**

Esta epic possui alto valor de negocio porque resolve uma dor recorrente e cara para donos de negocio: transformar materiais de marketing em campanhas de Google Ads sem depender 100% de um especialista externo. O produto combina velocidade operacional, IA aplicada a um caso com valor financeiro direto e uma camada de seguranca via aprovacao humana, o que aumenta a confianca para adocao. Alem disso, cria uma base reutilizavel para expansao futura em novos paises, novos tipos de campanha e possivelmente outros canais de midia paga.
