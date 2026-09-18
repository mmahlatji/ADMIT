import { useState } from "react";
import { Button, Card, Divider, Group, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import { useAllPages } from "../../lib/allPages";
import { VoteBadge } from "../../components/StatusBadge";
import { LoadingState } from "../../components/States";
import type { Application, Vote, VoteDecision } from "../../types/api";

const DECISIONS: VoteDecision[] = ["yes", "no", "abstain"];

export default function VotesPanel({
  campusId,
  applications,
}: {
  campusId: string;
  applications: Application[];
}) {
  const { user } = useAuth();
  const { data, loading, reload } = useAllPages<Vote>(
    `/votes?campus_id=${encodeURIComponent(campusId)}`,
  );
  const [saving, setSaving] = useState<string | null>(null);

  const votes = data ?? [];

  async function cast(applicationNumber: string, vote: VoteDecision) {
    setSaving(`${applicationNumber}:${vote}`);
    try {
      await api.request<Vote>("/votes", {
        method: "POST",
        body: JSON.stringify({
          application_number: applicationNumber,
          vote,
        }),
      });
      await reload();
    } catch (e) {
      notifications.show({
        color: "red",
        title: "Vote not recorded",
        message: e instanceof Error ? e.message : "Something went wrong",
      });
    } finally {
      setSaving(null);
    }
  }

  return (
    <Card>
      <Text fw={700} mb={4}>
        Committee votes
      </Text>
      <Text size="xs" c="dimmed" mb="md">
        One vote each per application. Voting does not move the application on
        its own; a convenor still records the decision.
      </Text>

      {loading ? (
        <LoadingState label="Loading votes" />
      ) : applications.length === 0 ? (
        <Text size="sm" c="dimmed">
          No applications to vote on.
        </Text>
      ) : (
        <Stack gap="lg">
          {applications.map((app, index) => {
            const forApp = votes.filter(
              (v) => v.application_number === app.application_number,
            );
            const mine = forApp.find((v) => v.voter_id === user?.employee_id);
            const tally = {
              yes: forApp.filter((v) => v.vote === "yes").length,
              no: forApp.filter((v) => v.vote === "no").length,
              abstain: forApp.filter((v) => v.vote === "abstain").length,
            };

            return (
              <div key={app.application_id}>
                {index > 0 && <Divider mb="md" />}
                <Group justify="space-between" gap="xs" mb="xs" wrap="wrap">
                  <Text size="sm">
                    <span className="identifier">{app.application_number}</span>{" "}
                    · {app.academic_plan1}
                  </Text>
                  <Group gap="xs">
                    <Text size="xs" c="dimmed" className="identifier">
                      {tally.yes} yes · {tally.no} no · {tally.abstain} abstain
                    </Text>
                  </Group>
                </Group>

                <Group gap="xs">
                  {DECISIONS.map((decision) => {
                    const isMine = mine?.vote === decision;
                    return (
                      <Button
                        key={decision}
                        size="xs"
                        variant={isMine ? "filled" : "default"}
                        loading={
                          saving === `${app.application_number}:${decision}`
                        }
                        onClick={() => cast(app.application_number, decision)}
                      >
                        {decision}
                      </Button>
                    );
                  })}
                  {mine && (
                    <Text size="xs" c="dimmed">
                      you voted <VoteBadge vote={mine.vote} size="xs" />
                    </Text>
                  )}
                </Group>
              </div>
            );
          })}
        </Stack>
      )}
    </Card>
  );
}
