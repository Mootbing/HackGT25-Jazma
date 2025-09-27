import { createClient } from '@supabase/supabase-js';
let supabase = null;
export function getSupabase() {
    if (!supabase)
        throw new Error('Supabase client not initialized');
    return supabase;
}
export async function createDbPool() {
    if (supabase)
        return supabase;
    const url = process.env.SUPABASE_URL;
    const anonKey = process.env.SUPABASE_ANON_KEY;
    if (!url || !anonKey) {
        throw new Error('SUPABASE_URL or SUPABASE_ANON_KEY is not set');
    }
    supabase = createClient(url, anonKey, {
        auth: { persistSession: false }
    });
    return supabase;
}
