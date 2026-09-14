import { useState } from "react";
import {
  Button,
  Card,
  Code,
  Group,
  SegmentedControl,
  Stack,
  Text,
  Textarea,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { Check, RefreshCw, X } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { MatchStatusBadge } from "../../components/StatusBadge";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import { useResource } from "../../lib/useResource";
import type { MatchingReview, MatchResolution } from "../../types/api";

/** The evidence the matcher recorded, which is the whole basis for deciding. */
function Evidence({
  label,
  value,
}: {
  label: string;
  value: Record<string, unknown> | null;
}) {
  if (!value || Object.keys(value).length === 0) return null;
  return (
    <div>
      <Text size="xs" c="dimmed" tt="uppercase" fw={700} mb={4}>
        {label}
      </Text>
      <Code block style={{ fontSize: "0.75rem" }}>
        {JSON.stringify(value, null, 2)}
      </Code>
    </div>
  );
}

export default function Conflicts() {
  const [tab, setTab] = useState<"pending" | "resolved">("pending");
  const { data, loading, error, reload, setData } = useResource<
    MatchingReview[]
  >(`/matching_reviews?status=${tab}&limit=300`);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);

  const reviews = data ?? [];

  async function resolve(review: MatchingReview, resolution: MatchResolution) {
    setSaving(review.match_id);
    try {
      await api.request<MatchingReview>(
        `/matching_reviews/${review.match_id}/resolve`,
        {
          method: "POST",
          body: JSON.stringify({
            resolution,
            // The resolver's own explanation, not an echo of the matcher's.
            reason: notes[review.match_id]?.trim() || review.reason,
          }),
        },
      );
      // Drop it from the open queue rather than refetching the whole thing.
      setData((prev) =>
        (prev ?? []).filter((r) => r.match_id !== review.match_id),
      );
      notifications.show({
        color: "green",
        title: resolution === "merge" ? "Merged" : "Rejected",
        message: "The row has left the queue.",
      });
    } catch (e) {
      notifications.show({
        color: "red",
        title: "Could not resolve",
        message: e instanceof Error ? e.message : "Something went wrong",
      });
    } finally {
      setSaving(null);
    }
  }

  return (
    <Stack gap="lg">
      <PageHeader
        title="Conflicts"
        description="Rows an import could not apply on its own. Each one is a record the system declined to guess about, so a person decides instead."
        actions={
          <Button
            variant="default"
            leftSection={<RefreshCw size={16} />}
            onClick={reload}
            loading={loading}
          >
            Refresh
          </Button>
        }
      />

      <SegmentedControl
        value={tab}
        onChange={(v) => setTab(v as "pending" | "resolved")}
        data={[
          { label: "Open", value: "pending" },
          { label: "Resolved", value: "resolved" },
        ]}
        w={260}
      />

      {error && <ErrorState error={error} />}

      {loading ? (
        <LoadingState label="Loading the queue" />
      ) : reviews.length === 0 ? (
        <EmptyState
          title={
            tab === "pending" ? "Nothing waiting" : "Nothing resolved yet"
          }
          hint={
            tab === "pending"
              ? "Every imported row was applied cleanly. Rows land here when the matcher cannot tell whether a sheet row is an existing applicant or a new one."
              : "Resolved conflicts keep a record of who decided and why."
          }
        />
      ) : (
        <>
          <Text size="sm" c="dimmed">
            {reviews.length} item{reviews.length === 1 ? "" : "s"}
          </Text>

          <Stack gap="md">
            {reviews.map((review) => (
              <Card key={review.match_id}>
                <Group justify="space-between" mb="xs" wrap="wrap" gap="xs">
                  <Group gap="xs">
                    <MatchStatusBadge status={review.status} />
                    {review.resolution && (
                      <Text size="xs" c="dimmed">
                        {review.resolution === "merge" ? "merged" : "rejected"}
                        {review.resolved_by && ` by ${review.resolved_by}`}
                        {review.resolved_at &&
                          ` · ${formatDateTime(review.resolved_at)}`}
                      </Text>
                    )}
                  </Group>
                  <Text size="xs" c="dimmed" className="identifier">
                    row {review.staging_row_id.slice(0, 8)}
                  </Text>
                </Group>

                <Text size="sm" mb="md">
                  {review.reason ?? "No reason recorded."}
                </Text>

                <Stack gap="sm">
                  <Evidence
                    label="Candidate keys"
                    value={review.candidate_keys}
                  />
                  <Evidence label="Match signals" value={review.match_signals} />
                </Stack>

                {tab === "pending" && (
                  <Stack gap="xs" mt="md">
                    <Textarea
                      label="Why (optional)"
                      description="Recorded with the resolution, for whoever reads this later."
                      autosize
                      minRows={1}
                      value={notes[review.match_id] ?? ""}
                      onChange={(e) =>
                        setNotes((prev) => ({
                          ...prev,
                          [review.match_id]: e.currentTarget.value,
                        }))
                      }
                    />
                    <Group gap="xs">
                      <Button
                        leftSection={<Check size={16} />}
                        loading={saving === review.match_id}
                        onClick={() => resolve(review, "merge")}
                      >
                        Merge into the existing applicant
                      </Button>
                      <Button
                        variant="default"
                        leftSection={<X size={16} />}
                        loading={saving === review.match_id}
                        onClick={() => resolve(review, "reject")}
                      >
                        Reject the row
                      </Button>
                    </Group>
                  </Stack>
                )}
              </Card>
            ))}
          </Stack>
        </>
      )}
    </Stack>
  );
}
