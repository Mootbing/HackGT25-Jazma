import 'dotenv/config';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { Pool } from 'pg';
async function run() {
    const databaseUrl = process.env.DATABASE_URL;
    if (!databaseUrl)
        throw new Error('DATABASE_URL is not set');
    const pool = new Pool({ connectionString: databaseUrl });
    try {
        await pool.query('begin');
        await pool.query('create table if not exists _migrations (id text primary key, applied_at timestamptz not null default now())');
        await pool.query('commit');
    }
    catch (e) {
        await pool.query('rollback');
        throw e;
    }
    const migrationsDir = join(process.cwd(), 'infra', 'migrations');
    const files = readdirSync(migrationsDir)
        .filter(f => f.endsWith('.sql'))
        .sort();
    for (const file of files) {
        const id = file;
        const res = await pool.query('select 1 from _migrations where id = $1', [id]);
        if (res.rowCount) {
            // eslint-disable-next-line no-console
            console.log(`[migrate] skip ${id}`);
            continue;
        }
        const sql = readFileSync(join(migrationsDir, file), 'utf8');
        // eslint-disable-next-line no-console
        console.log(`[migrate] apply ${id}`);
        try {
            await pool.query('begin');
            await pool.query(sql);
            await pool.query('insert into _migrations (id) values ($1)', [id]);
            await pool.query('commit');
        }
        catch (e) {
            await pool.query('rollback');
            // eslint-disable-next-line no-console
            console.error(`[migrate] failed ${id}`, e);
            throw e;
        }
    }
    await pool.end();
}
run().catch((err) => {
    // eslint-disable-next-line no-console
    console.error(err);
    process.exit(1);
});
