// One place mirroring the backend's require_role() gating. Anything that
// disagrees with app/routers/*.py is a bug here, not there: showing someone a
// door the API will not open is worse than not showing it at all.
import type { Role } from "../types/api";

export const ALL_ROLES: Role[] = ["convenor", "committee", "admin"];

/** applicants, applications, votes, notes, rules (read), import_documents */
export const READ_ROLES: Role[] = ["convenor", "committee", "admin"];

/** imports, matching_reviews, import_runs, system_logs, users (list), rules (write) */
export const CONVENOR_ADMIN: Role[] = ["convenor", "admin"];

/** users/{id}/role is the only convenor-exclusive endpoint */
export const CONVENOR_ONLY: Role[] = ["convenor"];

/** An unapproved account has a null role and is allowed nothing. */
export function can(role: Role | null, allowed: Role[]): boolean {
  return role !== null && allowed.includes(role);
}
