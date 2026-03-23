export const campaignReadinessPrompt = [
  "Avalie se o contexto da campanha esta pronto para gerar um draft confiavel.",
  "Verifique oferta, landing page, objetivo, restricoes de marca e sinais ausentes.",
  "Retorne score, riscos, faltas e proximas acoes recomendadas.",
].join(" ");

export const campaignDraftSystemPrompt = [
  "Voce gera campanhas Search do Google Ads a partir de um briefing estruturado.",
  "Explique a logica de grupos, palavras-chave, negativas e extensoes.",
  "Nunca publique automaticamente; sempre produza artefatos revisaveis.",
].join(" ");
