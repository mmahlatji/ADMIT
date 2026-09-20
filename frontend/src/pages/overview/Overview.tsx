import { useEffect, useMemo, useState } from "react";
import {
  Anchor,
  Card,
  Grid,
  Group,
  SimpleGrid,
  Stack,
  Table,
  Text,
} from "@mantine/core";
import { Link } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import TableCard from "../../components/TableCard";
import { ErrorState, LoadingState } from "../../components/States";
import { ImportStatusBadge } from "../../components/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { fetchAllPages } from "../../lib/allPages";
import { api } from "../../lib/api";
import { formatDateTime, sourceLabel } from "../../lib/format";
import { can, CONVENOR_ADMIN, CONVENOR_ONLY } from "../../lib/roles";
import {
  APPLICATION_STATUSES,
  type Application,
  type ApplicationStatus,
  type ImportRun,
  type MatchingReview,
  type Rule,
  type User,
} from "../../types/api";
import StatusDistribution from "./StatusDistribution";
import classes from "./Overview.module.css";

function Stat({
  label,
  value,
  hint,
  to,
}: {
  label: string;
  value: number | string;
  hint?: string;
  to?: string;
}) {
  const body = (
    <Card h="100%">
      <Text size="xs" tt="uppercase" c="dimmed" fw={700}>
        {label}
      </Text>
      <div className={classes.statValue}>{value}</div>
      {hint && (
        <Text size="xs" c="dimmed" mt={4}>
          {hint}
        </Text>
      )}
    </Card>
  );

  return to ? (
    <Link to={to} style={{ textDecoration: "none", color: "inherit" }}>
      {body}
    </Link>
  ) : (
    body
  );
}

type Data = {
  applications: Application[];
  conflicts: MatchingReview[];
  imports: ImportRun[];
  rules: Rule[];
  users: User[];
};

export default function Overview() {
  const { user } = useAuth();
  const role = user?.role ?? null;
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        // Only ask for what this role is allowed to see. Requesting the rest
        // and swallowing the 403s would fill the network log with failures
        // that look like bugs.
        const wantsOps = can(role, CONVENOR_ADMIN);
        // Everything here is a headline count, so a capped fetch would put a
        // confidently wrong number on the dashboard. The import list is the one
        // exception: it shows the five most recent runs and says so.
        const [applications, conflicts, imports, rules, users] =
          await Promise.all([
            fetchAllPages<Application>("/applications").then((r) => r.items),
            wantsOps
              ? fetchAllPages<MatchingReview>(
                  "/matching_reviews?status=pending",
                ).then((r) => r.items)
              : Promise.resolve([]),
            wantsOps
              ? api.request<ImportRun[]>("/import_runs?limit=5")
              : Promise.resolve([]),
            fetchAllPages<Rule>("/rules").then((r) => r.items),
            can(role, CONVENOR_ONLY)
              ? fetchAllPages<User>("/users").then((r) => r.items)
              : Promise.resolve([]),
          ]);

        if (!cancelled) {
          setData({ applications, conflicts, imports, rules, users });
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Could not load the intake");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [role]);

  const counts = useMemo(() => {
    const tally = Object.fromEntries(
      APPLICATION_STATUSES.map((s) => [s, 0]),
    ) as Record<ApplicationStatus, number>;
    for (const a of data?.applications ?? []) {
      if (a.application_status in tally) tally[a.application_status] += 1;
    }
    return tally;
  }, [data]);

  if (loading) return <LoadingState label="Loading the intake" />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  const total = data.applications.length;
  const undecided = counts.Applied + counts.Reviewed;
  const activeRule = data.rules.find((r) => r.status === "active");
  const awaiting = data.users.filter((u) => u.role === null).length;
  const flagged = data.applications.filter(
    (a) =>
      a.duplicate_application || a.incorrect_plan || a.requires_plan_correction,
  ).length;

  return (
    <Stack gap="lg">
      <PageHeader
        title={`Good day, ${user?.first_name ?? "there"}`}
        description="Where the intake stands right now. Every number here links to the page that can act on it."
      />

      <SimpleGrid cols={{ base: 1, xs: 2, md: 4 }} spacing="md">
        <Stat
          label="Applications"
          value={total}
          hint={`${undecided} still undecided`}
          to="/decisions"
        />
        <Stat
          label="Flagged rows"
          value={flagged}
          hint="duplicate, wrong plan or needs correction"
          to="/decisions"
        />
        {can(role, CONVENOR_ADMIN) && (
          <Stat
            label="Open conflicts"
            value={data.conflicts.length}
            hint={
              data.conflicts.length === 0
                ? "every imported row applied cleanly"
                : "waiting on a person to decide"
            }
            to="/conflicts"
          />
        )}
        {can(role, CONVENOR_ONLY) ? (
          <Stat
            label="Awaiting approval"
            value={awaiting}
            hint="accounts with no role yet"
            to="/people"
          />
        ) : (
          <Stat
            label="Admitted"
            value={counts.Accepted + counts["Ready to Register"]}
            hint="accepted or ready to register"
            to="/decisions"
          />
        )}
      </SimpleGrid>

      <Grid gutter="md">
        <Grid.Col span={{ base: 12, md: 6 }}>
          <StatusDistribution counts={counts} total={total} />
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6 }}>
          <Stack gap="md">
            <Card>
              <Text fw={700} mb={4}>
                Rule in force
              </Text>
              {activeRule ? (
                <>
                  <Text className="identifier" size="sm">
                    {activeRule.rule}
                  </Text>
                  <Text size="xs" c="dimmed" mt={4}>
                    Version {activeRule.version}, intake{" "}
                    {activeRule.intake_year}, set by {activeRule.created_by}
                  </Text>
                </>
              ) : (
                <Text size="sm" c="dimmed">
                  No rule saved yet.{" "}
                  <Anchor component={Link} to="/rules" size="sm">
                    Write one
                  </Anchor>{" "}
                  to see what it would do to this intake before it counts.
                </Text>
              )}
            </Card>

            {can(role, CONVENOR_ADMIN) && (
              <div>
                <Group justify="space-between" mb="xs">
                  <Text fw={700}>Recent imports</Text>
                  <Anchor component={Link} to="/imports" size="sm">
                    All imports
                  </Anchor>
                </Group>
                {data.imports.length === 0 ? (
                  <Card>
                    <Text size="sm" c="dimmed">
                      Nothing imported yet. Upload an ASR sheet to populate the
                      intake.
                    </Text>
                  </Card>
                ) : (
                  <TableCard minWidth={420}>
                    <Table>
                      <Table.Thead>
                        <Table.Tr>
                          <Table.Th>Source</Table.Th>
                          <Table.Th>When</Table.Th>
                          <Table.Th>Sheet rows</Table.Th>
                          <Table.Th>Loaded</Table.Th>
                          <Table.Th>Status</Table.Th>
                        </Table.Tr>
                      </Table.Thead>
                      <Table.Tbody>
                        {data.imports.map((run) => (
                          <Table.Tr key={run.import_run_id}>
                            <Table.Td>{sourceLabel(run.source_type)}</Table.Td>
                            <Table.Td>
                              <Text size="xs">
                                {formatDateTime(run.uploaded_at)}
                              </Text>
                            </Table.Td>
                            <Table.Td className="identifier">
                              {run.rows_total}
                            </Table.Td>
                            <Table.Td className="identifier">
                              {run.rows_loaded}
                            </Table.Td>
                            <Table.Td>
                              <ImportStatusBadge status={run.status} />
                            </Table.Td>
                          </Table.Tr>
                        ))}
                      </Table.Tbody>
                    </Table>
                  </TableCard>
                )}
              </div>
            )}
          </Stack>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
