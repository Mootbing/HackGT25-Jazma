import { Pool } from 'pg';

let pool: Pool | null = null;

export function getDbPool(): Pool {
  if (!pool) throw new Error('DB pool not initialized');
  return pool;
}

export async function createDbPool(): Promise<Pool> {
  if (pool) return pool;
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error('DATABASE_URL is not set');
  }
  pool = new Pool({ connectionString: databaseUrl, max: 10 });
  // quick sanity check
  await pool.query('select 1');
  return pool;
}

