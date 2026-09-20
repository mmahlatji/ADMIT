import { useEffect, useMemo, useState } from "react";
import {
  Anchor,
  Badge,
  Button,
  Checkbox,
  Group,
  Modal,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { RefreshCw, Search } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import Pager, { ROWS_PER_PAGE } from "../../components/Pager";
import TableCard from "../../components/TableCard";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { ApplicationStatusBadge } from "../../components/StatusBadge";
import { useAllPages } from "../../lib/allPages";
import { api } from "../../lib/api";
import {
  APPLICATION_STATUSES,
  DENY_REASONS,
  type Application,
  type ApplicationStatus,
  type DenyReason,
} from "../../types/api";

export default function Decisions() {
  const { data, loading, error, reload, setData, truncated } =
    useAllPages<Application>("/applications");
  const location = useLocation();
  const [query, setQuery] = useState(
    () => (location.state as { query?: string } | null)?.query ?? "",
  );
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [target, setTarget] = useState<ApplicationStatus | null>(null);
  const [reason, setReason] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState(1);

  const applications = useMemo(() => data ?? [], [data]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return applications.filter((a) => {
      if (statusFilter && a.application_status !== statusFilter) return false;
      if (!q) return true;
      return (
        a.application_number.toLowerCase().includes(q) ||
        a.campus_id.toLowerCase().includes(q) ||
        a.academic_plan1.toLowerCase().includes(q)
      );
    });
  }, [applications, query, statusFilter]);

  const selectedApps = useMemo(
    () => visible.filter((a) => selected.has(a.application_id)),
    [visible, selected],
  );

  const pageCount = Math.max(1, Math.ceil(visible.length / ROWS_PER_PAGE));
  const rows = useMemo(
    () => visible.slice((page - 1) * ROWS_PER_PAGE, page * ROWS_PER_PAGE),
    [visible, page],
  );

  // Narrowing the filter can leave the current page past the end of the
  // results, which renders an empty table under a pager that says otherwise.
  useEffect(() => {
    if (page > pageCount) setPage(1);
  }, [page, pageCount]);

  function toggle(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  // Selects everything matching the filter, not just the page on screen: the
  // point of filtering to a status is to act on all of it at once, and a
  // convenor should not have to walk the pages to do that.
  function toggleAll() {
    setSelected((prev) =>
      prev.size === visible.length
        ? new Set()
        : new Set(visible.map((a) => a.application_id)),
    );
  }

  async function applyStatus() {
    if (!target) return;
    // Denying without a reason is a 400 from the API, so the dialog will not
    // let it be submitted in the first place.
    const denyReason = target === "Denied" ? (reason as DenyReason) : null;

    setSaving(true);
    const succeeded: Application[] = [];
    const failures: string[] = [];

    // Sequential rather than parallel: each transition writes a system log
    // entry, and a burst of writes against one row set is what the audit
    // trail is least able to make sense of afterwards.
    for (const app of selectedApps) {
      try {
        const updated = await api.request<Application>(
          `/applications/${app.application_id}/status`,
          {
            method: "POST",
            body: JSON.stringify({ status: target, reason: denyReason }),
          },
        );
        succeeded.push(updated);
      } catch (e) {
        failures.push(
          `${app.application_number}: ${
            e instanceof Error ? e.message : "failed"
          }`,
        );
      }
    }

    if (succeeded.length > 0) {
      const byId = new Map(succeeded.map((a) => [a.application_id, a]));
      setData((prev) =>
        (prev ?? []).map((a) => byId.get(a.application_id) ?? a),
      );
      notifications.show({
        color: "green",
        title: `${succeeded.length} updated`,
        message: `Set to ${target}.`,
      });
    }
    if (failures.length > 0) {
      notifications.show({
        color: "red",
        title: `${failures.length} could not be changed`,
        message: failures.slice(0, 3).join("; "),
        autoClose: false,
      });
    }

    setSaving(false);
    setTarget(null);
    setReason(null);
    setSelected(new Set());
  }

  const allSelected = visible.length > 0 && selected.size === visible.length;

  return (
    <Stack gap="lg">
      <PageHeader
        title="Decisions"
        description="Every application in the cycle. Changing a status here is recorded as a decision, and a later import will not overturn it."
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

      <Group gap="sm" align="flex-end">
        <TextInput
          label="Search"
          placeholder="Application number, campus ID or plan"
          leftSection={<Search size={16} />}
          value={query}
          onChange={(e) => setQuery(e.currentTarget.value)}
          style={{ flex: "1 1 20rem" }}
        />
        <Select
          label="Status"
          placeholder="All statuses"
          data={APPLICATION_STATUSES as unknown as string[]}
          value={statusFilter}
          onChange={setStatusFilter}
          clearable
          w={200}
        />
      </Group>

      {error && <ErrorState error={error} />}

      {loading ? (
        <LoadingState label="Loading applications" />
      ) : applications.length === 0 ? (
        <EmptyState
          title="No applications yet"
          hint="Import an ASR sheet to populate the intake."
          action={
            <Button component={Link} to="/imports" mt="sm">
              Go to imports
            </Button>
          }
        />
      ) : (
        <>
          <Pager
            page={page}
            onChange={setPage}
            totalItems={visible.length}
            truncated={truncated}
          />

          <TableCard minWidth={880}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th w={40}>
                    <Checkbox
                      aria-label={`Select all ${visible.length} matching`}
                      checked={allSelected}
                      indeterminate={selected.size > 0 && !allSelected}
                      onChange={toggleAll}
                    />
                  </Table.Th>
                  <Table.Th>Application</Table.Th>
                  <Table.Th>Campus ID</Table.Th>
                  <Table.Th>Plan</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Flags</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {rows.map((a) => (
                  <Table.Tr
                    key={a.application_id}
                    bg={
                      selected.has(a.application_id)
                        ? "var(--mantine-color-uct-light)"
                        : undefined
                    }
                  >
                    <Table.Td>
                      <Checkbox
                        aria-label={`Select ${a.application_number}`}
                        checked={selected.has(a.application_id)}
                        onChange={() => toggle(a.application_id)}
                      />
                    </Table.Td>
                    <Table.Td className="identifier">
                      {a.application_number}
                    </Table.Td>
                    <Table.Td>
                      <Anchor
                        component={Link}
                        to={`/applicants/${a.campus_id}`}
                        className="identifier"
                      >
                        {a.campus_id}
                      </Anchor>
                    </Table.Td>
                    <Table.Td>{a.academic_plan1}</Table.Td>
                    <Table.Td>
                      <ApplicationStatusBadge status={a.application_status} />
                      {a.application_status_reason && (
                        <Text size="xs" c="dimmed">
                          {a.application_status_reason}
                        </Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Group gap={4}>
                        {a.duplicate_application && (
                          <Badge size="xs" color="attention">
                            duplicate
                          </Badge>
                        )}
                        {a.incorrect_plan && (
                          <Badge size="xs" color="attention">
                            wrong plan
                          </Badge>
                        )}
                        {a.requires_plan_correction && (
                          <Badge size="xs" color="attention">
                            needs correction
                          </Badge>
                        )}
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </TableCard>
        </>
      )}

      {/* Action bar, only present once something is selected, so the page is
          not carrying a permanently disabled toolbar. */}
      {selected.size > 0 && (
        <Paper
          withBorder
          shadow="md"
          p="sm"
          pos="sticky"
          bottom="var(--mantine-spacing-md)"
          style={{ zIndex: 20 }}
        >
          <Group justify="space-between" wrap="wrap" gap="sm">
            <Text size="sm" fw={700}>
              {selected.size} selected
            </Text>
            <Group gap="xs">
              <Button
                variant="subtle"
                color="gray"
                onClick={() => setSelected(new Set())}
              >
                Clear
              </Button>
              <Select
                placeholder="Set status to…"
                data={APPLICATION_STATUSES as unknown as string[]}
                value={null}
                onChange={(v) => {
                  setTarget(v as ApplicationStatus);
                  setReason(null);
                }}
                w={200}
              />
            </Group>
          </Group>
        </Paper>
      )}

      <Modal
        opened={target !== null}
        onClose={() => setTarget(null)}
        title={`Set ${selectedApps.length} application${
          selectedApps.length === 1 ? "" : "s"
        } to ${target}`}
      >
        <Stack gap="md">
          {target === "Denied" && (
            <Select
              withAsterisk
              label="Reason"
              description="The API refuses a denial without one of these."
              placeholder="Pick a reason"
              data={DENY_REASONS as unknown as string[]}
              value={reason}
              onChange={setReason}
            />
          )}
          <Text size="sm" c="dimmed">
            This is recorded as a decision against{" "}
            {selectedApps.length === 1
              ? selectedApps[0]?.application_number
              : `${selectedApps.length} applications`}
            , and a later import will not overturn it.
          </Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setTarget(null)}>
              Cancel
            </Button>
            <Button
              onClick={applyStatus}
              loading={saving}
              disabled={target === "Denied" && !reason}
            >
              Confirm
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
