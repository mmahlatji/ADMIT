import { useEffect, useMemo, useState } from "react";
import Header from "../../components/Header";
import { api } from "../../lib/api";
import type { Applicant, ApplicantDetail } from "../../types/user";
import { statusClass } from "./Decisions";
import "./Work.css";

export default function Workspace() {
  const [applicants, setApplicants] = useState<Applicant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState<ApplicantDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setApplicants(await api.request<Applicant[]>("/applicants?limit=500"));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not load applicants");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const visible = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return applicants;
    return applicants.filter(
      (a) =>
        a.campus_id.toLowerCase().includes(q) ||
        `${a.first_name} ${a.last_name}`.toLowerCase().includes(q),
    );
  }, [applicants, filter]);

  async function open(campusId: string) {
    setDetailLoading(true);
    try {
      setSelected(await api.request<ApplicantDetail>(`/applicants/${campusId}`));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load that applicant");
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <div className="work-page">
      <Header />
      <div className="work-body">
        <h1 className="work-title">Workspace</h1>
        <p className="work-subtitle">
          Everyone in the cycle, with their applications, marks and motivation in
          one place.
        </p>

        {error && <p className="work-error">{error}</p>}

        {selected ? (
          <>
            <button className="work-button secondary" onClick={() => setSelected(null)}>
              ← Back to list
            </button>
            <div className="work-card" style={{ marginTop: "1rem" }}>
              <h2 className="work-title" style={{ fontSize: "1.15rem" }}>
                {selected.title} {selected.first_name} {selected.last_name}
              </h2>
              <p className="work-muted">
                {selected.campus_id} · {selected.employee_id} ·{" "}
                {selected.citizenship_residency}
                {selected.email ? ` · ${selected.email}` : ""}
              </p>
            </div>

            <div className="work-card">
              <strong>Applications</strong>
              {selected.applications.length === 0 ? (
                <p className="work-muted">None on file.</p>
              ) : (
                <div className="work-scroll">
                  <table className="work-table" style={{ marginTop: "0.5rem" }}>
                    <thead>
                      <tr>
                        <th>Number</th>
                        <th>Plan</th>
                        <th>Choice</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selected.applications.map((a) => (
                        <tr key={a.application_id}>
                          <td>{a.application_number}</td>
                          <td>{a.academic_plan1}</td>
                          <td>{a.choice}</td>
                          <td>
                            <span className={`pill ${statusClass(a.application_status)}`}>
                              {a.application_status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="work-card">
              <strong>Marks</strong>
              {selected.applicant_marks.length === 0 ? (
                <p className="work-muted">
                  No marks imported. Upload a UCT marks or IT transcripts sheet.
                </p>
              ) : (
                <div className="work-scroll">
                  <table className="work-table" style={{ marginTop: "0.5rem" }}>
                    <thead>
                      <tr>
                        <th>Course</th>
                        <th>Mark</th>
                        <th>Result</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selected.applicant_marks.map((m) => (
                        <tr key={m.course_code}>
                          <td>{m.course_code}</td>
                          <td>{m.mark}</td>
                          <td>
                            {m.result_code !== "NONE" && (
                              <span className="pill flag">{m.result_code}</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="work-card">
              <strong>Motivation</strong>
              <p className={selected.motivation?.motivation ? "" : "work-muted"}>
                {selected.motivation?.motivation ?? "None on file."}
              </p>
            </div>
          </>
        ) : (
          <>
            <div className="work-toolbar">
              <input
                className="work-input"
                placeholder="Search by name or campus id"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
              />
            </div>

            {loading || detailLoading ? (
              <div className="work-loading">Loading…</div>
            ) : visible.length === 0 ? (
              <div className="work-empty">
                No applicants yet. Import an ASR sheet to populate this.
              </div>
            ) : (
              <>
                <p className="work-muted">
                  Showing {visible.length} of {applicants.length}
                </p>
                <div className="work-scroll">
                  <table className="work-table">
                    <thead>
                      <tr>
                        <th>Campus ID</th>
                        <th>Name</th>
                        <th>Citizenship</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {visible.map((a) => (
                        <tr key={a.campus_id}>
                          <td>{a.campus_id}</td>
                          <td>
                            {a.first_name} {a.last_name}
                          </td>
                          <td>{a.citizenship_residency}</td>
                          <td>
                            <button
                              className="work-button secondary"
                              onClick={() => open(a.campus_id)}
                            >
                              Open
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
