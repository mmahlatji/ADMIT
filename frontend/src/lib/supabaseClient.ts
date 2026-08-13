/**
 * The ONLY file allowed to talk to Supabase directly — and only for auth.
 * All applicant data, imports, decisions, etc. go through lib/api.ts and
 * our own FastAPI backend, so authorization logic lives in one place
 * instead of two systems that can drift.
 */
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
