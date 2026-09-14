import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { can, CONVENOR_ADMIN, CONVENOR_ONLY } from "../lib/roles";
import type { MatchingReview, User } from "../types/api";

export type NavCounts = { conflicts: number; pendingUsers: number };

/** Counts for the sidebar badges, fetched only for roles the API allows. */
export function useNavCounts(): NavCounts {
  const { user } = useAuth();
  const [counts, setCounts] = useState<NavCounts>({
    conflicts: 0,
    pendingUsers: 0,
  });

  useEffect(() => {
    const role = user?.role ?? null;
    let cancelled = false;

    async function load() {
      // Each is allowed to fail quietly: a badge is not worth an error state,
      // and the page behind it reports properly if something is actually wrong.
      if (can(role, CONVENOR_ADMIN)) {
        try {
          const pending = await api.request<MatchingReview[]>(
            "/matching_reviews?status=pending&limit=500",
          );
          if (!cancelled)
            setCounts((c) => ({ ...c, conflicts: pending.length }));
        } catch {
          /* leave at 0 */
        }
      }
      if (can(role, CONVENOR_ONLY)) {
        try {
          const users = await api.request<User[]>("/users?limit=500");
          if (!cancelled)
            setCounts((c) => ({
              ...c,
              pendingUsers: users.filter((u) => u.role === null).length,
            }));
        } catch {
          /* leave at 0 */
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [user?.role]);

  return counts;
}
