import { Card, Group, Stack, Text } from "@mantine/core";
import { APPLICATION_STATUSES, type ApplicationStatus } from "../../types/api";
import { STATUS_COLOUR } from "../../components/StatusBadge";
import classes from "./Overview.module.css";

/**
 * Seven long-named lifecycle states is at the ceiling for a categorical chart
 * and past it for a pie, so this is a labelled bar list: name and count are
 * always readable as text, the bar carries the magnitude, and the rows stay in
 * lifecycle order rather than sorted by size so the shape of the funnel reads
 * top to bottom.
 */
export default function StatusDistribution({
  counts,
  total,
}: {
  counts: Record<ApplicationStatus, number>;
  total: number;
}) {
  return (
    <Card>
      <Text fw={700} mb="xs">
        Applications by status
      </Text>
      <Text size="xs" c="dimmed" mb="md">
        {total} application{total === 1 ? "" : "s"} in the cycle
      </Text>
      <Stack gap="sm">
        {APPLICATION_STATUSES.map((status) => {
          const count = counts[status] ?? 0;
          const share = total === 0 ? 0 : (count / total) * 100;
          return (
            <div key={status}>
              <Group justify="space-between" gap="xs" mb={4} wrap="nowrap">
                <Text size="sm" style={{ minWidth: 0 }}>
                  {status}
                </Text>
                <Group gap="xs" wrap="nowrap">
                  <Text size="sm" fw={700} className="identifier">
                    {count}
                  </Text>
                  <Text size="xs" c="dimmed" className="identifier" w={44} ta="right">
                    {share.toFixed(1)}%
                  </Text>
                </Group>
              </Group>
              <div
                className={classes.track}
                role="img"
                aria-label={`${status}: ${count} of ${total}`}
              >
                <div
                  className={classes.bar}
                  style={{
                    // Share of the whole intake, not of the largest category,
                    // so the bar length and the percentage beside it agree.
                    width: `${share}%`,
                    background: STATUS_COLOUR[status],
                  }}
                />
              </div>
            </div>
          );
        })}
      </Stack>
    </Card>
  );
}
