"use client";

import { useState, useTransition } from "react";
import { Button, StatusPill } from "@adsmcp/ui";
import { createBrowserSupabaseClient } from "../../lib/supabase/client";

type LoginFormProps = {
  isSupabaseConfigured: boolean;
  next: string;
};

export function LoginForm({
  isSupabaseConfigured,
  next,
}: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState(
    isSupabaseConfigured
      ? "Entre com seu email para receber o link mágico."
      : "Preencha as variáveis do Supabase para habilitar autenticação real.",
  );
  const [isPending, startTransition] = useTransition();

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!isSupabaseConfigured) {
      setMessage("Supabase ainda não configurado neste ambiente.");
      return;
    }

    startTransition(async () => {
      const supabase = createBrowserSupabaseClient();

      if (!supabase) {
        setMessage("Supabase ainda não configurado neste ambiente.");
        return;
      }

      const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(
        next,
      )}`;

      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          emailRedirectTo: redirectTo,
        },
      });

      setMessage(
        error
          ? "Não foi possível enviar o link mágico. Revise a configuração e tente novamente."
          : "Link mágico enviado. Verifique seu email para entrar no workspace.",
      );
    });
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <label className="field">
        <span className="field-label">Email de acesso</span>
        <input
          className="text-input"
          name="email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="voce@empresa.com"
          required
          type="email"
          value={email}
        />
      </label>

      <Button disabled={!isSupabaseConfigured || isPending} type="submit">
        {isPending ? "Enviando..." : "Enviar link mágico"}
      </Button>

      <div className="inline-message">
        <StatusPill tone={isSupabaseConfigured ? "neutral" : "warning"}>
          {isSupabaseConfigured ? "Supabase pronto" : "Configuração pendente"}
        </StatusPill>
        <p>{message}</p>
      </div>
    </form>
  );
}
