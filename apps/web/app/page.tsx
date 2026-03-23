import {
  campaignObjectiveOptions,
  draftLifecycleStates,
  mvpFeatureSequence,
} from "@adsmcp/domain";
import { campaignReadinessPrompt } from "@adsmcp/prompts";
import { Button, Card, SectionHeading, StatusPill } from "@adsmcp/ui";

const launchHighlights = [
  "Conectar Google Ads e Google Drive em um workspace simples.",
  "Ler a pasta da campanha e gerar um briefing estruturado.",
  "Criar drafts de campanhas Search com explicação clara.",
  "Publicar e otimizar sempre com aprovação explícita.",
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-copy">
          <StatusPill tone="neutral">MVP-01 Workspace Onboarding</StatusPill>
          <p className="eyebrow">Google Ads Copilot for Business Owners</p>
          <h1>
            Entre, conecte suas contas e deixe o workspace pronto para a
            primeira campanha.
          </h1>
          <p className="lede">
            Este primeiro corte do produto abre a jornada real do dono do
            negócio: acessar a plataforma, entender o setup e preparar Google
            Ads e Google Drive sem fricção desnecessária.
          </p>
          <div className="hero-actions">
            <Button href="/login">Entrar no workspace</Button>
            <Button href="/#stack" variant="secondary">
              Ver arquitetura inicial
            </Button>
          </div>
        </div>

        <Card accent="soft">
          <SectionHeading
            eyebrow="First cut"
            title="O que já está visível neste onboarding"
            description="A base agora já prepara a navegação entre página pública, login e dashboard inicial do produto."
          />
          <ul className="plain-list">
            {launchHighlights.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>
      </section>

      <section id="mvp" className="content-grid">
        <Card>
          <SectionHeading
            eyebrow="MVP features"
            title="Sequência recomendada"
            description="A ordem segue o pipeline real de valor: entrar, entender contexto, gerar draft, aprovar e melhorar."
          />
          <div className="stack-list">
            {mvpFeatureSequence.map((feature, index) => (
              <div className="feature-row" key={feature.id}>
                <span className="feature-index">{String(index + 1).padStart(2, "0")}</span>
                <div>
                  <h3>{feature.name}</h3>
                  <p>{feature.outcome}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionHeading
            eyebrow="Campaign state"
            title="Estados explícitos"
            description="O produto precisa manter cada transição visível para preservar segurança operacional."
          />
          <div className="pill-wrap">
            {draftLifecycleStates.map((state) => (
              <StatusPill key={state} tone="outline">
                {state}
              </StatusPill>
            ))}
          </div>
        </Card>
      </section>

      <section id="stack" className="content-grid">
        <Card accent="soft">
          <SectionHeading
            eyebrow="Objectives"
            title="Objetivos suportados"
            description="No MVP o usuário escolhe o resultado principal, e o draft nasce alinhado a esse objetivo."
          />
          <div className="pill-wrap">
            {campaignObjectiveOptions.map((objective) => (
              <StatusPill key={objective} tone="neutral">
                {objective}
              </StatusPill>
            ))}
          </div>
        </Card>

        <Card>
          <SectionHeading
            eyebrow="Prompting"
            title="Readiness before publishing"
            description="A base já separa um prompt inicial para readiness scoring e qualidade do contexto."
          />
          <pre className="prompt-preview">{campaignReadinessPrompt}</pre>
        </Card>
      </section>
    </main>
  );
}
