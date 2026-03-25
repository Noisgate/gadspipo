import { Pool } from "pg";
import { getPostgresEnv } from "../env";

declare global {
  var __adsmcpPostgresPool: Pool | undefined;
}

function shouldUseSsl(databaseUrl: string, sslDisabled: boolean) {
  if (sslDisabled) {
    return false;
  }

  try {
    const parsed = new URL(databaseUrl);
    const hostname = parsed.hostname.toLowerCase();

    return !["localhost", "127.0.0.1"].includes(hostname);
  } catch {
    return !sslDisabled;
  }
}

export function getPostgresPool() {
  const env = getPostgresEnv();

  if (!env.isConfigured || !env.databaseUrl) {
    return null;
  }

  if (!globalThis.__adsmcpPostgresPool) {
    globalThis.__adsmcpPostgresPool = new Pool({
      connectionString: env.databaseUrl,
      ssl: shouldUseSsl(env.databaseUrl, env.sslDisabled)
        ? { rejectUnauthorized: false }
        : undefined,
    });
  }

  return globalThis.__adsmcpPostgresPool;
}
