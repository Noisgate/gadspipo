export type SupabaseEnv = {
  url: string | undefined;
  anonKey: string | undefined;
  isConfigured: boolean;
};

export type PostgresEnv = {
  databaseUrl: string | undefined;
  isConfigured: boolean;
  sslDisabled: boolean;
};

export function getSupabaseEnv(): SupabaseEnv {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  return {
    url,
    anonKey,
    isConfigured: Boolean(url && anonKey),
  };
}

export function getPostgresEnv(): PostgresEnv {
  const databaseUrl = process.env.DATABASE_URL;

  return {
    databaseUrl,
    isConfigured: Boolean(databaseUrl),
    sslDisabled: process.env.POSTGRES_SSL_DISABLED === "true",
  };
}
