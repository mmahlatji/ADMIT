import { useMemo, useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Group,
  Modal,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { RefreshCw, Search } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import TableCard from "../../components/TableCard";
import { ErrorState, LoadingState } from "../../components/States";
import { StatusDot } from "../../components/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import { formatDateTime, fullName } from "../../lib/format";
import { ALL_ROLES } from "../../lib/roles";
import { useAllPages } from "../../lib/allPages";
import type { Role, User } from "../../types/api";

const REVOKE = "__revoke__";

export default function People() {
  const { user: me } = useAuth();
  const { data, loading, error, reload, setData } =
    useAllPages<User>("/users");
  const [query, setQuery] = useState("");
  const [pending, setPending] = useState<{
    target: User;
    role: Role | null;
  } | null>(null);
  const [saving, setSaving] = useState(false);

  const users = useMemo(() => data ?? [], [data]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return users;
    return users.filter(
      (u) =>
        fullName(u).toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        (u.employee_id ?? "").includes(q),
    );
  }, [users, query]);

  const awaiting = users.filter((u) => u.role === null).length;

  async function applyRole() {
    if (!pending) return;
    setSaving(true);
    try {
      const updated = await api.request<User>(
        `/users/${pending.target.user_id}/role`,
        { method: "POST", body: JSON.stringify({ role: pending.role }) },
      );
      setData((prev) =>
        (prev ?? []).map((u) => (u.user_id === updated.user_id ? updated : u)),
      );
      notifications.show({
        color: "green",
        title: pending.role ? "Role granted" : "Access revoked",
        message: `${fullName(pending.target)} is now ${
          pending.role ?? "without a role"
        }.`,
      });
      setPending(null);
    } catch (e) {
      notifications.show({
        color: "red",
        title: "Could not change the role",
        message: e instanceof Error ? e.message : "Something went wrong",
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <Stack gap="lg">
      <PageHeader
        title="People"
        description="New accounts arrive with no role and can reach nothing until a convenor grants one."
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

      {awaiting > 0 && (
        <Alert color="attention" variant="light">
          {awaiting} account{awaiting === 1 ? "" : "s"} waiting on a role. Until
          then they can sign in but see nothing.
        </Alert>
      )}

      <TextInput
        placeholder="Search by name, email or employee ID"
        leftSection={<Search size={16} />}
        value={query}
        onChange={(e) => setQuery(e.currentTarget.value)}
        maw={420}
      />

      {error && <ErrorState error={error} />}

      {loading ? (
        <LoadingState label="Loading people" />
      ) : (
        <TableCard minWidth={880}>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Name</Table.Th>
                <Table.Th>Email</Table.Th>
                <Table.Th>Employee ID</Table.Th>
                <Table.Th>Role</Table.Th>
                <Table.Th>Joined</Table.Th>
                <Table.Th>Change to</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {visible.map((u) => {
                // A convenor cannot change their own role, which the API
                // enforces too. Disabling it here avoids handing someone an
                // error they can do nothing about.
                const isSelf = me?.user_id === u.user_id;
                return (
                  <Table.Tr key={u.user_id}>
                    <Table.Td>
                      {fullName(u)}
                      {isSelf && (
                        <Text span size="xs" c="dimmed">
                          {" "}
                          (you)
                        </Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{u.email}</Text>
                    </Table.Td>
                    <Table.Td className="identifier">
                      {u.employee_id ?? "—"}
                    </Table.Td>
                    <Table.Td>
                      {u.role ? (
                        <Badge
                          variant="default"
                          tt="none"
                          fw={500}
                          leftSection={
                            <StatusDot colour="var(--status-accepted)" />
                          }
                        >
                          {u.role}
                        </Badge>
                      ) : (
                        <Badge
                          variant="default"
                          tt="none"
                          fw={500}
                          leftSection={
                            <StatusDot colour="var(--status-offer)" />
                          }
                        >
                          awaiting approval
                        </Badge>
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Text size="xs">{formatDateTime(u.created_at)}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Select
                        placeholder={isSelf ? "Not you" : "Set role…"}
                        disabled={isSelf}
                        value={null}
                        w={160}
                        data={[
                          ...ALL_ROLES.filter((r) => r !== u.role).map((r) => ({
                            value: r,
                            label: r,
                          })),
                          ...(u.role
                            ? [{ value: REVOKE, label: "Revoke access" }]
                            : []),
                        ]}
                        onChange={(value) => {
                          if (!value) return;
                          setPending({
                            target: u,
                            role: value === REVOKE ? null : (value as Role),
                          });
                        }}
                      />
                    </Table.Td>
                  </Table.Tr>
                );
              })}
            </Table.Tbody>
          </Table>
        </TableCard>
      )}

      <Modal
        opened={pending !== null}
        onClose={() => setPending(null)}
        title={pending?.role ? "Grant this role" : "Revoke access"}
      >
        {pending && (
          <Stack gap="md">
            <Text size="sm">
              {pending.role ? (
                <>
                  <strong>{fullName(pending.target)}</strong> becomes a{" "}
                  <strong>{pending.role}</strong>, and can reach everything that
                  role allows straight away.
                </>
              ) : (
                <>
                  <strong>{fullName(pending.target)}</strong> keeps their
                  account but loses access to the intake until someone grants a
                  role again. Notes and decisions they have already made stay on
                  record.
                </>
              )}
            </Text>
            <Group justify="flex-end">
              <Button variant="default" onClick={() => setPending(null)}>
                Cancel
              </Button>
              <Button
                onClick={applyRole}
                loading={saving}
                color={pending.role ? undefined : "red"}
              >
                {pending.role ? "Grant" : "Revoke"}
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Stack>
  );
}
