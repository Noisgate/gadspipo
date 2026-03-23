import { redirect } from "next/navigation";
import { StatusPill, Card, SectionHeading, Button } from "@adsmcp/ui";
import { readSearchCampaignDraftApproval } from "../../lib/draft-approval-store";
import { readSavedSearchCampaignDraft } from "../../lib/draft-store";
import { getSupabaseEnv } from "../../lib/env";
import { getGoogleAdsConnectionDiagnostic } from "../../lib/google-ads";
import { createServerSupabaseClient } from "../../lib/supabase/server";
import { getWorkspaceSnapshot } from "../../lib/workspace";
import { readWorkspaceDriveIntake } from "../../lib/workspace-store";
import { DraftApprovalActions } from "./draft-approval-actions";
import { SignOutForm } from "./sign-out-form";
import { DriveIntakeForm } from "./drive-intake-form";
import { SearchDraftActions } from "./search-draft-actions";

function toneForIntegration(status: "connected" | "disconnected" | "attention") {
  if (status === "connected") {
    return "success" as const;
  }

  if (status === "attention") {
    return "warning" as const;
  }

  return "outline" as const;
}

function toneForReadiness(status: "ready" | "missing" | "warning") {
  if (status === "ready") {
    return "success" as const;
  }

  if (status === "warning") {
    return "warning" as const;
  }

  return "outline" as const;
}

function toneForDraftStatus(status: "ready" | "needs_context") {
  return status === "ready" ? ("success" as const) : ("warning" as const);
}

function toneForApprovalStatus(
  status: "not_requested" | "pending_review" | "approved" | "changes_requested",
) {
  if (status === "approved") {
    return "success" as const;
  }

  if (status === "pending_review" || status === "changes_requested") {
    return "warning" as const;
  }

  return "outline" as const;
}

function formatPersistenceTimestamp(value: string | null) {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "America/Sao_Paulo",
  }).format(parsed);
}

export default async function DashboardPage() {
  const env = getSupabaseEnv();
  const supabase = await createServerSupabaseClient();
  let userEmail: string | null = null;
  let userId: string | null = null;

  if (env.isConfigured && supabase) {
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      redirect("/login?next=/dashboard");
    }

    userId = user.id;
    userEmail = user.email ?? null;
  }

  const driveIntakeRecord = await readWorkspaceDriveIntake({
    supabase,
    userId,
  });
  const savedDraftRecord = await readSavedSearchCampaignDraft({
    supabase,
    userId,
  });
  const approvalRecord = await readSearchCampaignDraftApproval({
    supabase,
    userId,
  });
  const workspace = getWorkspaceSnapshot(userEmail, driveIntakeRecord.intake);
  const googleAdsDiagnostic = getGoogleAdsConnectionDiagnostic(
    workspace.driveIntake.googleAdsCustomerId,
  );
  const formattedPersistenceTimestamp = formatPersistenceTimestamp(
    driveIntakeRecord.updatedAt,
  );
  const formattedDraftSavedAt = formatPersistenceTimestamp(savedDraftRecord.updatedAt);
  const formattedApprovalUpdatedAt = formatPersistenceTimestamp(approvalRecord.updatedAt);
  const formattedApprovedAt = formatPersistenceTimestamp(approvalRecord.approvedAt);

  return (
    <main className="page-shell dashboard-shell">
      <section className="dashboard-header">
        <div>
          <StatusPill tone={env.isConfigured ? "success" : "warning"}>
            {env.isConfigured ? "Auth ativa" : "Modo preview"}
          </StatusPill>
          <p className="eyebrow">Workspace onboarding</p>
          <h1>Bem-vindo, {workspace.ownerLabel}.</h1>
          <p className="lede">
            Este dashboard mostra o primeiro objetivo operacional do produto:
            deixar o workspace pronto para receber a pasta da campanha e gerar o
            primeiro draft Search.
          </p>
        </div>

        <div className="dashboard-actions">
          {env.isConfigured ? <SignOutForm /> : null}
          <Button href="/login" variant="secondary">
            Ajustar acesso
          </Button>
        </div>
      </section>

      <section className="content-grid">
        <Card accent="soft">
          <SectionHeading
            eyebrow="Setup progress"
            title={`${workspace.progress}% do onboarding e intake concluídos`}
            description="Enquanto as integrações reais não entram, o produto já pode estruturar contexto e deixar o próximo passo totalmente explícito."
          />
          <div className="progress-track" aria-hidden="true">
            <div
              className="progress-fill"
              style={{ width: `${workspace.progress}%` }}
            />
          </div>
          <div className="pill-wrap">
            <StatusPill
              tone={
                driveIntakeRecord.persistenceMode === "workspace"
                  ? "success"
                  : "warning"
              }
            >
              {driveIntakeRecord.persistenceLabel}
            </StatusPill>
            {formattedPersistenceTimestamp ? (
              <StatusPill tone="outline">
                Ultima sincronizacao: {formattedPersistenceTimestamp}
              </StatusPill>
            ) : null}
          </div>
          <p className="support-copy strong">{workspace.nextAction}</p>
        </Card>

        <Card>
          <SectionHeading
            eyebrow="Current scope"
            title="Drive intake antes da ingestão real"
            description="Este corte ja captura a conta alvo do Google Ads, a pasta da campanha e os sinais essenciais para o primeiro readiness score, com persistencia por usuario quando o workspace estiver pronto."
          />
          <div className="pill-wrap">
            <StatusPill tone="neutral">Google Ads Search</StatusPill>
            <StatusPill tone="neutral">Google Drive como contexto</StatusPill>
            <StatusPill tone="neutral">Publicação com aprovação</StatusPill>
            <StatusPill tone="neutral">Otimização com aprovação</StatusPill>
          </div>
          <div className="next-step-box">
            <p className="section-eyebrow">Persistencia atual</p>
            <p>{driveIntakeRecord.persistenceDetail}</p>
          </div>
        </Card>
      </section>

      <section className="content-grid">
        <Card accent="soft">
          <SectionHeading
            eyebrow="Workspace setup"
            title="Registrar a conta alvo e o contexto minimo da campanha"
            description="No MVP tecnico atual, esse estado fica salvo localmente ou no workspace para preparar a conexao real com Google Ads e Google Drive."
          />
          <DriveIntakeForm defaultValues={workspace.driveIntake} />
        </Card>

        <Card>
          <SectionHeading
            eyebrow="Readiness"
            title={`${workspace.readinessScore}% de prontidão para gerar um brief`}
            description="O score combina pasta, objetivo, oferta, landing page e notas adicionais. Ele não substitui ingestão real, mas já organiza a próxima ação."
          />
          <div className="pill-wrap">
            <StatusPill
              tone={
                workspace.readinessScore >= 80
                  ? "success"
                  : workspace.readinessScore >= 50
                    ? "warning"
                    : "outline"
              }
            >
              Score atual: {workspace.readinessScore}
            </StatusPill>
          </div>
          <div className="readiness-list">
            {workspace.readinessChecks.map((check) => (
              <div className="readiness-row" key={check.label}>
                <div className="readiness-topline">
                  <h3>{check.label}</h3>
                  <StatusPill tone={toneForReadiness(check.status)}>
                    {check.status === "ready"
                      ? "Pronto"
                      : check.status === "warning"
                        ? "Parcial"
                        : "Faltando"}
                  </StatusPill>
                </div>
                <p>{check.detail}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <section className="content-grid">
        <Card>
          <SectionHeading
            eyebrow="Brief preview"
            title="Resumo estruturado do contexto atual"
            description="Este preview antecipa a forma como o produto vai transformar materiais da pasta em um briefing utilizável para drafts de campanha."
          />
          <div className="brief-stack">
            <div className="next-step-box">
              <p className="section-eyebrow">Origem</p>
              <p>{workspace.briefPreview.sourceSummary}</p>
            </div>
            <div className="next-step-box">
              <p className="section-eyebrow">Ângulo da campanha</p>
              <p>{workspace.briefPreview.campaignAngle}</p>
            </div>
            <div className="next-step-box">
              <p className="section-eyebrow">Resultado alvo</p>
              <p>{workspace.briefPreview.targetOutcome}</p>
            </div>
          </div>
        </Card>

        <Card>
          <SectionHeading
            eyebrow="Next best actions"
            title="O que falta para chegar ao primeiro draft"
            description="O produto precisa ser explícito sobre os gaps restantes antes de prometer automação de campanha."
          />
          <ul className="plain-list">
            {workspace.briefPreview.nextBestActions.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <div className="missing-signals">
            <p className="section-eyebrow">Sinais ausentes ou parciais</p>
            <div className="pill-wrap">
              {workspace.briefPreview.missingSignals.length > 0 ? (
                workspace.briefPreview.missingSignals.map((item) => (
                  <StatusPill key={item} tone="outline">
                    {item}
                  </StatusPill>
                ))
              ) : (
                <StatusPill tone="success">Contexto base completo</StatusPill>
              )}
            </div>
          </div>
        </Card>
      </section>

      <section className="content-grid">
        <Card accent="soft">
          <SectionHeading
            eyebrow="Search draft"
            title="Primeiro draft revisavel da campanha"
            description="Este draft ainda e um artefato de revisao interna, mas ja traduz o contexto atual para uma estrutura inicial de Google Ads Search."
          />
          <div className="pill-wrap">
            <StatusPill tone={toneForDraftStatus(workspace.searchCampaignDraft.status)}>
              {workspace.searchCampaignDraft.status === "ready"
                ? "Draft pronto para revisao"
                : "Draft aguardando contexto"}
            </StatusPill>
            <StatusPill tone="outline">
              {workspace.searchCampaignDraft.campaignName}
            </StatusPill>
            <StatusPill
              tone={
                savedDraftRecord.hasSavedDraft
                  ? savedDraftRecord.persistenceMode === "workspace"
                    ? "success"
                    : "warning"
                  : "outline"
              }
            >
              {savedDraftRecord.persistenceLabel}
            </StatusPill>
          </div>
          <div className="next-step-box">
            <p className="section-eyebrow">Budget guidance</p>
            <p>{workspace.searchCampaignDraft.budgetGuidance}</p>
          </div>
          <div className="next-step-box">
            <p className="section-eyebrow">Status do snapshot</p>
            <p>{savedDraftRecord.persistenceDetail}</p>
            {formattedDraftSavedAt ? (
              <p className="support-copy">Ultimo snapshot salvo em {formattedDraftSavedAt}.</p>
            ) : null}
          </div>
          <SearchDraftActions
            canSave={workspace.searchCampaignDraft.status === "ready"}
            hasSavedDraft={savedDraftRecord.hasSavedDraft}
          />
          <div className="next-step-box">
            <p className="section-eyebrow">Aprovacao antes da publicacao</p>
            <div className="pill-wrap">
              <StatusPill tone={toneForApprovalStatus(approvalRecord.status)}>
                {approvalRecord.statusLabel}
              </StatusPill>
              <StatusPill
                tone={
                  approvalRecord.hasApprovalRequest
                    ? approvalRecord.persistenceMode === "workspace"
                      ? "success"
                      : "warning"
                    : "outline"
                }
              >
                {approvalRecord.persistenceLabel}
              </StatusPill>
            </div>
            <p>{approvalRecord.statusDetail}</p>
            {approvalRecord.approvalSummary ? (
              <p className="support-copy">{approvalRecord.approvalSummary}</p>
            ) : null}
            {formattedApprovalUpdatedAt ? (
              <p className="support-copy">
                Ultimo movimento de aprovacao em {formattedApprovalUpdatedAt}.
              </p>
            ) : null}
            {formattedApprovedAt ? (
              <p className="support-copy">
                Liberado para publicacao em {formattedApprovedAt}.
              </p>
            ) : null}
          </div>
          <DraftApprovalActions
            approvalStatus={approvalRecord.status}
            hasApprovalRequest={approvalRecord.hasApprovalRequest}
            hasSavedDraft={savedDraftRecord.hasSavedDraft}
          />
          <div className="draft-stack">
            {workspace.searchCampaignDraft.adGroups.map((group) => (
              <div className="draft-group" key={group.name}>
                <div className="readiness-topline">
                  <h3>{group.name}</h3>
                  <StatusPill tone="neutral">Ad group</StatusPill>
                </div>
                <p>{group.focus}</p>
                <div className="pill-wrap">
                  {group.keywords.map((keyword) => (
                    <StatusPill key={keyword} tone="outline">
                      {keyword}
                    </StatusPill>
                  ))}
                </div>
                <div className="draft-copy">
                  <p>
                    <strong>Headlines:</strong> {group.headlines.join(" | ")}
                  </p>
                  <p>
                    <strong>Descriptions:</strong> {group.descriptions.join(" | ")}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <SectionHeading
            eyebrow="Draft rationale"
            title="Porque o sistema montaria esse draft"
            description="A ideia aqui e deixar a logica da campanha transparente para facilitar aprovacao humana antes de qualquer publicacao."
          />
          <ul className="plain-list">
            {workspace.searchCampaignDraft.rationale.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <div className="next-step-box">
            <p className="section-eyebrow">Salvamento antes da publicacao</p>
            <p>{workspace.searchCampaignDraft.statusDetail}</p>
          </div>
          <div className="missing-signals">
            <p className="section-eyebrow">Negative keywords iniciais</p>
            <div className="pill-wrap">
              {workspace.searchCampaignDraft.negativeKeywords.map((item) => (
                <StatusPill key={item} tone="outline">
                  {item}
                </StatusPill>
              ))}
            </div>
          </div>
          <div className="missing-signals">
            <p className="section-eyebrow">Extensoes sugeridas</p>
            <div className="pill-wrap">
              {workspace.searchCampaignDraft.extensions.map((item) => (
                <StatusPill key={item} tone="neutral">
                  {item}
                </StatusPill>
              ))}
            </div>
          </div>
          <div className="missing-signals">
            <p className="section-eyebrow">Bloqueios atuais</p>
            <div className="pill-wrap">
              {workspace.searchCampaignDraft.blockers.length > 0 ? (
                workspace.searchCampaignDraft.blockers.map((item) => (
                  <StatusPill key={item} tone="warning">
                    {item}
                  </StatusPill>
                ))
              ) : (
                <StatusPill tone="success">Sem bloqueios criticos</StatusPill>
              )}
            </div>
          </div>
        </Card>
      </section>

      <section className="integration-grid">
        <Card accent={googleAdsDiagnostic.isConfigured ? undefined : "soft"}>
          <div className="integration-topline">
            <div>
              <p className="eyebrow">googleAds</p>
              <h2 className="integration-title">Google Ads API</h2>
            </div>
            <StatusPill tone={toneForIntegration(googleAdsDiagnostic.status)}>
              {googleAdsDiagnostic.status === "connected"
                ? "Conectado"
                : googleAdsDiagnostic.status === "attention"
                  ? "Atenção"
                  : "Não conectado"}
            </StatusPill>
          </div>
          <div className="pill-wrap">
            <StatusPill tone="outline">
              {googleAdsDiagnostic.credentialSourceLabel}
            </StatusPill>
            {googleAdsDiagnostic.targetCustomerId ? (
              <StatusPill tone="neutral">
                Customer ID: {googleAdsDiagnostic.targetCustomerId}
              </StatusPill>
            ) : null}
            {googleAdsDiagnostic.loginCustomerId ? (
              <StatusPill tone="neutral">
                MCC: {googleAdsDiagnostic.loginCustomerId}
              </StatusPill>
            ) : null}
          </div>
          <p className="integration-summary">{googleAdsDiagnostic.summary}</p>
          <div className="readiness-list">
            {googleAdsDiagnostic.checks.map((check) => (
              <div className="readiness-row" key={check.label}>
                <div className="readiness-topline">
                  <h3>{check.label}</h3>
                  <StatusPill tone={toneForReadiness(check.status)}>
                    {check.status === "ready"
                      ? "Pronto"
                      : check.status === "warning"
                        ? "Parcial"
                        : "Faltando"}
                  </StatusPill>
                </div>
                <p>{check.detail}</p>
              </div>
            ))}
          </div>
          <div className="next-step-box">
            <p className="section-eyebrow">Próxima ação</p>
            <p>{googleAdsDiagnostic.nextStep}</p>
          </div>
          <div className="missing-signals">
            <p className="section-eyebrow">Itens faltando</p>
            <div className="pill-wrap">
              {googleAdsDiagnostic.missingRequirements.length > 0 ? (
                googleAdsDiagnostic.missingRequirements.map((item) => (
                  <StatusPill key={item} tone="warning">
                    {item}
                  </StatusPill>
                ))
              ) : (
                <StatusPill tone="success">Conexão pronta para API mode</StatusPill>
              )}
            </div>
          </div>
          {googleAdsDiagnostic.configPath ? (
            <p className="support-copy">
              Arquivo local detectado em {googleAdsDiagnostic.configPath}.
            </p>
          ) : null}
          <Button disabled variant="secondary">
            {googleAdsDiagnostic.isConfigured
              ? "Google Ads pronto para o proximo corte"
              : "Aguardando credenciais reais"}
          </Button>
        </Card>

        {workspace.integrations
          .filter((integration) => integration.key !== "googleAds")
          .map((integration) => (
          <Card key={integration.key}>
            <div className="integration-topline">
              <div>
                <p className="eyebrow">{integration.key}</p>
                <h2 className="integration-title">{integration.name}</h2>
              </div>
              <StatusPill tone={toneForIntegration(integration.status)}>
                {integration.status === "connected"
                  ? "Conectado"
                  : integration.status === "attention"
                    ? "Atenção"
                    : "Não conectado"}
              </StatusPill>
            </div>
            <p className="integration-summary">{integration.summary}</p>
            <div className="next-step-box">
              <p className="section-eyebrow">Próxima ação</p>
              <p>{integration.nextStep}</p>
            </div>
            <Button disabled variant="secondary">
              Integração entra na próxima etapa
            </Button>
          </Card>
        ))}
      </section>
    </main>
  );
}
