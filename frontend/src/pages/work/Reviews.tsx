import { useEffect, useState } from "react";
import Header from "../../components/Header";
import { api } from "../../lib/api";
import type { MatchingReview } from "../../types/user";
import "./Work.css";

export default function Reviews() {
  const [reviews, setReviews] = useState<MatchingReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showResolved, setShowResolved] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);

  async function load(resolved: boolean) {
    setLoading(true);
    try {
      const query = resolved ? "?status=resolved&limit=300" : "?status=pending&limit=300";
      setReviews(await api.request<MatchingReview[]>(`/matching_reviews${query}`));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load reviews");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load(showResolved);
  }, [showResolved]);

  async function resolve(review: MatchingReview, resolution: "merge" | "reject") {
    setSaving(review.match_id);
    try {
      await api.request(`/matching_reviews/${review.match_id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ resolution, reason: review.reason }),
      });
      // drop it from the pending list rather than refetching the whole queue
      setReviews((prev) => prev.filter((r) => r.match_id !== review.match_id));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not resolve");
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="work-page">
      <Header />
      <div className="work-body">
        <h1 className="work-title">Resolve conflicts</h1>
        <p className="work-subtitle">
          Rows an import could not apply on its own. Each one is a record the
          system declined to guess about, so a person decides instead.
        </p>

        <div className="work-toolbar">
          <button
            className={`work-button ${showResolved ? "secondary" : ""}`}
            onClick={() => setShowResolved(false)}
          >
            Open
          </button>
          <button
            className={`work-button ${showResolved ? "" : "secondary"}`}
            onClick={() => setShowResolved(true)}
          >
            Resolved
          </button>
          <button className="work-button secondary" onClick={() => load(showResolved)}>
            Refresh
          </button>
        </div>

        {error && <p className="work-error">{error}</p>}

        {loading ? (
          <div className="work-loading">Loading review queue…</div>
        ) : reviews.length === 0 ? (
          <div className="work-empty">
            {showResolved
              ? "Nothing has been resolved yet."
              : "Nothing waiting. Every imported row was applied cleanly."}
          </div>
        ) : (
          <>
            <p className="work-muted">{reviews.length} item(s)</p>
            {reviews.map((r) => (
              <div className="work-card" key={r.match_id}>
                <div style={{ marginBottom: "0.5rem" }}>
                  <span className={`pill ${r.status === "pending" ? "flag" : "accepted"}`}>
                    {r.status}
                  </span>
                  {r.resolution && <span className="pill"> {r.resolution}</span>}
                </div>
                <div>{r.reason ?? "No reason recorded"}</div>
                {!showResolved && (
                  <div className="work-toolbar" style={{ marginTop: "0.75rem" }}>
                    <button
                      className="work-button"
                      disabled={saving === r.match_id}
                      onClick={() => resolve(r, "merge")}
                    >
                      {saving === r.match_id ? "Saving…" : "Accept"}
                    </button>
                    <button
                      className="work-button secondary"
                      disabled={saving === r.match_id}
                      onClick={() => resolve(r, "reject")}
                    >
                      Reject
                    </button>
                  </div>
                )}
                {r.resolved_by && (
                  <p className="work-muted">Resolved by {r.resolved_by}</p>
                )}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
