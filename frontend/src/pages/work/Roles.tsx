import { useEffect, useState } from "react";
import Header from "../../components/Header";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import type { Role, User } from "../../types/user";
import "./Work.css";

const ROLES: Exclude<Role, null>[] = ["convenor", "committee", "admin"];

export default function Roles() {
  const { user: me } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      setUsers(await api.request<User[]>("/users"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function setRole(target: User, role: Role) {
    setSaving(target.user_id);
    try {
      const updated = await api.request<User>(`/users/${target.user_id}/role`, {
        method: "POST",
        body: JSON.stringify({ role }),
      });
      setUsers((prev) =>
        prev.map((u) => (u.user_id === updated.user_id ? updated : u)),
      );
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not change role");
    } finally {
      setSaving(null);
    }
  }

  const pending = users.filter((u) => !u.role).length;

  return (
    <div className="work-page">
      <Header />
      <div className="work-body">
        <h1 className="work-title">Assign roles</h1>
        <p className="work-subtitle">
          New accounts arrive with no role and can reach nothing until a convenor
          grants one. {pending > 0 && `${pending} waiting.`}
        </p>

        {error && <p className="work-error">{error}</p>}

        {loading ? (
          <div className="work-loading">Loading users…</div>
        ) : (
          <div className="work-scroll">
            <table className="work-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Employee ID</th>
                  <th>Role</th>
                  <th>Change to</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  // a convenor cannot change their own role, which the API
                  // enforces too; disabling it here avoids an error they
                  // cannot do anything about
                  const isSelf = me?.user_id === u.user_id;
                  return (
                    <tr key={u.user_id}>
                      <td>
                        {u.first_name} {u.last_name}
                        {isSelf && <span className="work-muted"> (you)</span>}
                      </td>
                      <td>{u.email}</td>
                      <td>{u.employee_id}</td>
                      <td>
                        {u.role ? (
                          <span className="pill accepted">{u.role}</span>
                        ) : (
                          <span className="pill flag">pending</span>
                        )}
                      </td>
                      <td>
                        <select
                          className="work-select"
                          value=""
                          disabled={isSelf || saving === u.user_id}
                          onChange={(e) =>
                            setRole(u, (e.target.value || null) as Role)
                          }
                        >
                          <option value="">
                            {saving === u.user_id ? "Saving…" : "Set role…"}
                          </option>
                          {ROLES.filter((r) => r !== u.role).map((r) => (
                            <option key={r} value={r}>
                              {r}
                            </option>
                          ))}
                          {u.role && <option value="">revoke</option>}
                        </select>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
