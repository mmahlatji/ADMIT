import { useEffect, useMemo, useState } from "react";
import Header from "../../components/Header";
import { api } from "../../lib/api";
import type { Application, ApplicationStatus, DenyReason } from "../../types/user";
import "./Work.css";

const STATUSES: ApplicationStatus[] = [
  "Applied",
  "Reviewed",
  "Conditional Offer",
  "Accepted",
  "Ready to Register",
  "Denied",
  "Cancelled",
];

const DENY_REASONS: DenyReason[] = [
  "Not competitive",
  "Requirements not met",
  "Duplicate application",
  "Incorrect program",
];

// maps a status onto the pill colours in Work.css
export function statusClass(status: string) {
  if (status === "Applied") return "applied";
  if (status === "Reviewed") return "reviewed";
  if (status === "Conditional Offer") return "offer";
  if (status === "Accepted") return "accepted";
  if (status === "Ready to Register") return "ready";
  if (status === "Denied") return "denied";
  return "cancelled";
}

export default function Decisions() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [saving, setSaving] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      setApplications(await api.request<Application[]>("/applications?limit=500"));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load applications");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase();
    return applications.filter((a) => {
      if (statusFilter && a.application_status !== statusFilter) return false;
      if (!q) return true;
      return (
        a.application_number.toLowerCase().includes(q) ||
        a.campus_id.toLowerCase().includes(q) ||
        a.academic_plan1.toLowerCase().includes(q)
      );
    });
  }, [applications, filter, statusFilter]);

  async function changeStatus(app: Application, status: ApplicationStatus) {
    // denying needs a reason, so ask for it rather than letting the API 400
    let reason: DenyReason | null = null;
    if (status === "Denied") {
      const picked = window.prompt(
        `Reason for denying ${app.application_number}?\n\n` +
          DENY_REASONS.map((r, i) => `${i + 1}. ${r}`).join("\n"),
        "1",
      );
      if (picked === null) return;
      reason = DENY_REASONS[Number(picked) - 1] ?? null;
      if (!reason) {
        setError("Denying an application needs one of the listed reasons");
        return;
      }
    }

    setSaving(app.application_id);
    try {
      const updated = await api.request<Application>(
        `/applications/${app.application_id}/status`,
        { method: "POST", body: JSON.stringify({ status, reason }) },
      );
      setApplications((prev) =>
        prev.map((a) => (a.application_id === updated.application_id ? updated : a)),
      );
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not change status");
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="work-page">
      <Header />
      <div className="work-body">
        <h1 className="work-title">Decisions</h1>
        <p className="work-subtitle">
          Every application in the cycle. Changing a status here is recorded as a
          decision, and an import will not overturn it.
        </p>

        <div className="work-toolbar">
          <input
            className="work-input"
            placeholder="Search application number, campus id or plan"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
          <select
            className="work-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <button className="work-button secondary" onClick={load}>
            Refresh
          </button>
        </div>

        {error && <p className="work-error">{error}</p>}

        {loading ? (
          <div className="work-loading">Loading applications…</div>
        ) : visible.length === 0 ? (
          <div className="work-empty">
            No applications match. Import an ASR sheet to populate this.
          </div>
        ) : (
          <>
            <p className="work-muted">
              Showing {visible.length} of {applications.length}
            </p>
            <div className="work-scroll">
              <table className="work-table">
                <thead>
                  <tr>
                    <th>Application</th>
                    <th>Campus ID</th>
                    <th>Plan</th>
                    <th>Status</th>
                    <th>Flags</th>
                    <th>Change to</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((a) => (
                    <tr key={a.application_id}>
                      <td>{a.application_number}</td>
                      <td>{a.campus_id}</td>
                      <td>{a.academic_plan1}</td>
                      <td>
                        <span className={`pill ${statusClass(a.application_status)}`}>
                          {a.application_status}
                        </span>
                        {a.application_status_reason && (
                          <div className="work-muted">{a.application_status_reason}</div>
                        )}
                      </td>
                      <td>
                        {a.duplicate_application && <span className="pill flag">duplicate</span>}{" "}
                        {a.incorrect_plan && <span className="pill flag">wrong plan</span>}{" "}
                        {a.requires_plan_correction && (
                          <span className="pill flag">needs correction</span>
                        )}
                      </td>
                      <td>
                        <select
                          className="work-select"
                          value=""
                          disabled={saving === a.application_id}
                          onChange={(e) =>
                            e.target.value &&
                            changeStatus(a, e.target.value as ApplicationStatus)
                          }
                        >
                          <option value="">
                            {saving === a.application_id ? "Saving…" : "Set status…"}
                          </option>
                          {STATUSES.filter((s) => s !== a.application_status).map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
