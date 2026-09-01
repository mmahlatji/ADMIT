import { useEffect, useState } from "react";
import Header from "../../components/Header";
import { api } from "../../lib/api";
import type { Rule, RulePreview } from "../../types/user";
import "./Work.css";

const INSTITUTION = "University of Cape Town";
const COURSES = ["csc2001f", "csc2002s", "csc3002f", "csc3003s"];

export default function RulesPage() {
  const [rules, setRules] = useState<Rule[]>([]);
  const [expression, setExpression] = useState(
    "0.5*csc3003s + 0.5*csc2002s >= 60",
  );
  const [intakeYear, setIntakeYear] = useState(new Date().getFullYear());
  const [preview, setPreview] = useState<RulePreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setRules(await api.request<Rule[]>("/rules"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load rules");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function run(path: string) {
    setBusy(true);
    setError(null);
    try {
      const body = JSON.stringify({
        institution: INSTITUTION,
        intake_year: intakeYear,
        expression,
      });
      const result = await api.request<RulePreview | Rule>(path, {
        method: "POST",
        body,
      });
      if (path.endsWith("/preview")) {
        setPreview(result as RulePreview);
      } else {
        setPreview(null);
        await load();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not evaluate that rule");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="work-page">
      <Header />
      <div className="work-body">
        <h1 className="work-title">Admission rules</h1>
        <p className="work-subtitle">
          Write a rule in terms of course marks and see what it would do to this
          intake before saving it. Nothing changes until you save.
        </p>

        <div className="work-card">
          <div className="work-toolbar">
            <input
              className="work-input"
              value={expression}
              onChange={(e) => setExpression(e.target.value)}
              placeholder="0.5*csc3003s + 0.5*csc2002s >= 60"
            />
            <input
              className="work-select"
              type="number"
              value={intakeYear}
              onChange={(e) => setIntakeYear(Number(e.target.value))}
              style={{ width: "7rem" }}
            />
            <button
              className="work-button"
              disabled={busy}
              onClick={() => run("/rules/preview")}
            >
              {busy ? "Working…" : "Preview"}
            </button>
            <button
              className="work-button secondary"
              disabled={busy || !preview}
              onClick={() => run("/rules")}
            >
              Save as active
            </button>
          </div>
          <p className="work-muted">
            Available marks: {COURSES.join(", ")}. Use + - * / and a comparison,
            for example <code>0.6*csc3003s + 0.4*csc3002f &gt;= 65</code>.
          </p>
        </div>

        {error && <p className="work-error">{error}</p>}

        {preview && (
          <div className="work-card">
            <div className="work-stat-row">
              <div className="work-stat">
                <div className="work-stat-value">{preview.after}</div>
                <div className="work-stat-label">would be admitted</div>
              </div>
              <div className="work-stat">
                <div className="work-stat-value">
                  {preview.pass_rate_after.toFixed(1)}%
                </div>
                <div className="work-stat-label">pass rate</div>
              </div>
              {!preview.first_rule && (
                <>
                  <div className="work-stat">
                    <div className="work-stat-value">{preview.before}</div>
                    <div className="work-stat-label">admitted now</div>
                  </div>
                  <div className="work-stat">
                    <div className="work-stat-value">
                      {preview.change !== null && preview.change > 0 ? "+" : ""}
                      {preview.change}
                    </div>
                    <div className="work-stat-label">change</div>
                  </div>
                </>
              )}
              <div className="work-stat">
                <div className="work-stat-value">{preview.not_evaluable}</div>
                <div className="work-stat-label">not evaluable</div>
              </div>
            </div>
            {preview.not_evaluable > 0 && (
              <p className="work-muted">
                {preview.not_evaluable} applicant(s) have no mark for a course
                this rule uses, so they are counted as not admitted.
              </p>
            )}
            {preview.first_rule && (
              <p className="work-muted">
                This would be the first rule for {intakeYear}, so there is
                nothing to compare against yet.
              </p>
            )}
          </div>
        )}

        <h2 className="work-title" style={{ fontSize: "1.15rem" }}>
          Saved rules
        </h2>
        {rules.length === 0 ? (
          <div className="work-empty">No rules saved yet.</div>
        ) : (
          <div className="work-scroll">
            <table className="work-table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Intake</th>
                  <th>Rule</th>
                  <th>Status</th>
                  <th>By</th>
                </tr>
              </thead>
              <tbody>
                {rules.map((r) => (
                  <tr key={r.rule_id}>
                    <td>{r.version}</td>
                    <td>{r.intake_year}</td>
                    <td>
                      <code>{r.rule}</code>
                    </td>
                    <td>
                      <span className="pill accepted">{r.status}</span>
                    </td>
                    <td>{r.created_by}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
