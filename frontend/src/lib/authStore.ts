// Plain module-level session holder, outside React, so api.ts can read the
// current token synchronously without calling supabase.auth.getSession()
// (which deadlocks when called from inside onAuthStateChange).
import type { Session } from "@supabase/supabase-js";

let currentSession: Session | null = null;

export function setCurrentSession(session: Session | null) {
  currentSession = session;
}

export function getCurrentToken(): string | undefined {
  return currentSession?.access_token;
}
