import Link from "next/link";
import { redirect } from "next/navigation";
import { Button, Card, SectionHeading, StatusPill } from "@adsmcp/ui";
import { getSupabaseEnv } from "../../lib/env";
import { createServerSupabaseClient } from "../../lib/supabase/server";
import { LoginForm } from "./login-form";

type LoginPageProps = {
  searchParams: Promise<{
    next?: string;
  }>;
};

const benefits = [
  "Entrar no workspace e acompanhar o setup da conta.",
  "Conectar Google Ads e Google Drive em ordem segura.",
  "Preparar a base para drafts, aprovação e otimização contínua.",
];

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const env = getSupabaseEnv();
  const supabase = await createServerSupabaseClient();
  const params = await searchParams;
  const next = params.next ?? "/dashboard";

  if (supabase) {
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (user) {
      redirect(next);
    }
  }

  return (
    <main className="page-shell auth-shell">
      <Card accent="soft">
        <SectionHeading
          eyebrow="Workspace onboarding"
          title="Entrar no produto sem complexidade desnecessária"
          description="No MVP o dono do negócio precisa de um ponto de entrada simples, claro e seguro para começar o setup."
        />
        <ul className="plain-list">
          {benefits.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <div className="hero-actions">
          <Button href="/">Voltar para visão geral</Button>
          <Button href="/dashboard" variant="secondary">
            Abrir preview do dashboard
          </Button>
        </div>
      </Card>

      <Card>
        <SectionHeading
          eyebrow="Acesso"
          title="Link mágico com Supabase"
          description="Quando as variáveis estiverem preenchidas, o login por email libera o dashboard protegido automaticamente."
        />
        <div className="pill-wrap auth-pills">
          <StatusPill tone={env.isConfigured ? "success" : "warning"}>
            {env.isConfigured ? "Supabase configurado" : "Faltam variáveis de ambiente"}
          </StatusPill>
          <StatusPill tone="outline">PT-BR no MVP</StatusPill>
        </div>
        <LoginForm isSupabaseConfigured={env.isConfigured} next={next} />
        <p className="support-copy">
          Assim que o login estiver ativo, o próximo passo é conectar Google Ads
          e Google Drive no dashboard.
        </p>
        <p className="support-copy">
          Se quiser avançar no layout antes das credenciais, você ainda pode
          abrir o <Link href="/dashboard">preview do dashboard</Link>.
        </p>
      </Card>
    </main>
  );
}
