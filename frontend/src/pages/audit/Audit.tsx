import { useState } from "react";
import {
  Badge,
  Button,
  Code,
  Group,
  Select,
  Stack,
  Table,
  Text,
} from "@mantine/core";
import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import TableCard from "../../components/TableCard";
import { StatusDot } from "../../components/StatusBadge";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { formatDateTime } from "../../lib/format";
import { useResource } from "../../lib/useResource";
import type { ChangeSource, SystemLog } from "../../types/api";

// The entities the pipeline actually writes log rows for.
const ENTITIES = [
  "applicants",
  "applications",
  "applicant_marks",
  "motivations",
  "matching_reviews",
  "rules",
  "users",
];

const SOURCE_COLOUR: Record<ChangeSource, string> = {
  import: "var(--status-reviewed)",
  manual_edit: "var(--status-offer)",
  merge_resolution: "var(--status-ready)",
  rules_calc: "var(--status-applied)",
  decision: "var(--status-accepted)",
};

/** Only the fields that actually differ, so a wide row does not hide the change. */
function Diff({ log }: { log: SystemLog }) {
  const oldData = log.old_data ?? {};
  const newData = log.new_data ?? {};
  // A field absent from old_data and null in new_data has not changed. Comparing
  // the raw values marks it as one, which fills the log with "— → —" rows that
  // bury the change actually worth reading.
  const same = (a: unknown, b: unknown) =>
    (a ?? null) === (b ?? null) || JSON.stringify(a ?? null) === JSON.stringify(b ?? null);

  const fields = [
    ...new Set([...Object.keys(oldData), ...Object.keys(newData)]),
  ].filter((key) => !same(oldData[key], newData[key]));

  if (fields.length === 0) {
    return (
      <Text size="xs" c="dimmed">
        no field changes recorded
      </Text>
    );
  }

  const show = (value: unknown) =>
    value === undefined || value === null
      ? "—"
      : typeof value === "string"
        ? value
        : JSON.stringify(value);

  return (
    <Stack gap={2}>
      {fields.map((key) => (
        <Text size="xs" key={key}>
          <Text span c="dimmed">
            {key}:
          </Text>{" "}
          <Code style={{ fontSize: "0.7rem" }}>{show(oldData[key])}</Code>
          {" → "}
          <Code style={{ fontSize: "0.7rem" }}>{show(newData[key])}</Code>
        </Text>
      ))}
    </Stack>
  );
}

// Unlike every other list in the app, the audit log only grows: it gains rows
// for every field of every record each import touches. Loading all of it to
// count it would get slower for the rest of the system's life, so this is the
// one page that pages against the server instead.
const LOGS_PER_PAGE = 100;

export default function Audit() {
  const [entity, setEntity] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const { data, loading, error, reload } = useResource<SystemLog[]>(
    `/system_logs?skip=${(page - 1) * LOGS_PER_PAGE}&limit=${LOGS_PER_PAGE}` +
      (entity ? `&entity_name=${entity}` : ""),
  );

  const logs = data ?? [];
  // No total comes back, so a full page is the only sign another may exist.
  const hasMore = logs.length === LOGS_PER_PAGE;

  return (
    <Stack gap="lg">
      <PageHeader
        title="Audit log"
        description="Every change the system recorded, what it was, who made it and why. Import runs, manual edits, merge resolutions and decisions all land here."
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

      <Select
        label="Entity"
        placeholder="Everything"
        data={ENTITIES}
        value={entity}
        onChange={(value) => {
          setEntity(value);
          setPage(1);
        }}
        clearable
        w={240}
      />

      {error && <ErrorState error={error} />}

      {loading ? (
        <LoadingState label="Loading the audit log" />
      ) : logs.length === 0 ? (
        page > 1 ? (
          <EmptyState
            title="End of the log"
            hint="There is nothing beyond this point."
            action={
              <Button mt="sm" variant="default" onClick={() => setPage(1)}>
                Back to the start
              </Button>
            }
          />
        ) : (
          <EmptyState
            title="Nothing recorded yet"
            hint={
              entity
                ? `No changes to ${entity} have been logged.`
                : "Changes appear here as soon as something is imported or decided."
            }
          />
        )
      ) : (
        <>
          <Group justify="space-between" wrap="wrap" gap="xs">
            <Text size="sm" c="dimmed" className="identifier">
              {(page - 1) * LOGS_PER_PAGE + 1} to{" "}
              {(page - 1) * LOGS_PER_PAGE + logs.length}
            </Text>
            <Group gap="xs">
              <Button
                size="compact-sm"
                variant="default"
                leftSection={<ChevronLeft size={14} />}
                disabled={page === 1 || loading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Newer
              </Button>
              <Button
                size="compact-sm"
                variant="default"
                rightSection={<ChevronRight size={14} />}
                disabled={!hasMore || loading}
                onClick={() => setPage((p) => p + 1)}
              >
                Older
              </Button>
            </Group>
          </Group>
          <TableCard minWidth={900}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>When</Table.Th>
                  <Table.Th>Entity</Table.Th>
                  <Table.Th>Source</Table.Th>
                  <Table.Th>By</Table.Th>
                  <Table.Th>Change</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {logs.map((log) => (
                  <Table.Tr key={log.log_id}>
                    <Table.Td>
                      <Text size="xs" style={{ whiteSpace: "nowrap" }}>
                        {formatDateTime(log.changed_at)}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{log.entity_name}</Text>
                      <Text size="xs" c="dimmed" className="identifier">
                        {log.entity_id.slice(0, 8)}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        variant="default"
                        tt="none"
                        fw={500}
                        leftSection={
                          <StatusDot colour={SOURCE_COLOUR[log.reason]} />
                        }
                      >
                        {log.reason.replace(/_/g, " ")}
                      </Badge>
                    </Table.Td>
                    <Table.Td className="identifier">{log.changed_by}</Table.Td>
                    <Table.Td>
                      <Diff log={log} />
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </TableCard>
        </>
      )}
    </Stack>
  );
}
