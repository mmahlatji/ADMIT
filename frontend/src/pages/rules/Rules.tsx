import { useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  Code,
  Group,
  NumberInput,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { CircleAlert, Play, Save } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import TableCard from "../../components/TableCard";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import { can, CONVENOR_ADMIN } from "../../lib/roles";
import { useResource } from "../../lib/useResource";
import {
  RULE_VARIABLES,
  type Rule,
  type RulePreview,
} from "../../types/api";
import classes from "./Rules.module.css";

const INSTITUTION = "University of Cape Town";

function Stat({
  label,
  value,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
}) {
  return (
    <div>
      <Text size="xs" tt="uppercase" c="dimmed" fw={700}>
        {label}
      </Text>
      <div className={classes.statValue}>{value}</div>
      {hint && (
        <Text size="xs" c="dimmed">
          {hint}
        </Text>
      )}
    </div>
  );
}

export default function Rules() {
  const { user } = useAuth();
  const canWrite = can(user?.role ?? null, CONVENOR_ADMIN);

  const { data, loading, error, reload } =
    useResource<Rule[]>("/rules?limit=100");
  const [expression, setExpression] = useState(
    "0.5*csc3003s + 0.5*csc2002s >= 60",
  );
  const [intakeYear, setIntakeYear] = useState<number>(
    new Date().getFullYear(),
  );
  const [preview, setPreview] = useState<RulePreview | null>(null);
  const [busy, setBusy] = useState<"preview" | "save" | null>(null);
  const [ruleError, setRuleError] = useState<string | null>(null);

  const rules = data ?? [];

  async function run(path: "/rules/preview" | "/rules") {
    setBusy(path === "/rules" ? "save" : "preview");
    setRuleError(null);
    try {
      const result = await api.request<RulePreview | Rule>(path, {
        method: "POST",
        body: JSON.stringify({
          institution: INSTITUTION,
          intake_year: intakeYear,
          expression,
        }),
      });
      if (path === "/rules/preview") {
        setPreview(result as RulePreview);
      } else {
        setPreview(null);
        notifications.show({
          color: "green",
          title: "Rule saved",
          message: `Version ${(result as Rule).version} is now active for ${intakeYear}.`,
        });
        await reload();
      }
    } catch (e) {
      setRuleError(
        e instanceof Error ? e.message : "Could not evaluate that rule",
      );
    } finally {
      setBusy(null);
    }
  }

  function insertVariable(variable: string) {
    setExpression((prev) => `${prev}${prev.trim() ? " + " : ""}${variable}`);
  }

  return (
    <Stack gap="lg">
      <PageHeader
        title="Admission rules"
        description="Write a rule in terms of course marks and see what it would do to this intake before saving it. Nothing changes until you save."
      />

      {!canWrite && (
        <Alert color="uct" variant="light">
          You can read the rules in force. Writing one is for convenors and
          admins.
        </Alert>
      )}

      {canWrite && (
        <Card>
          <Stack gap="sm">
            <TextInput
              label="Rule"
              description="Use + - * / and one comparison, for example 0.6*csc3003s + 0.4*csc3002f >= 65"
              value={expression}
              onChange={(e) => setExpression(e.currentTarget.value)}
              classNames={{ input: classes.expression }}
            />

            <Group gap="xs" align="center">
              <Text size="xs" c="dimmed">
                Available marks:
              </Text>
              {RULE_VARIABLES.map((v) => (
                <Button
                  key={v}
                  size="compact-xs"
                  variant="default"
                  className="identifier"
                  onClick={() => insertVariable(v)}
                >
                  {v}
                </Button>
              ))}
            </Group>

            <Group align="flex-end" gap="sm">
              <NumberInput
                label="Intake year"
                value={intakeYear}
                onChange={(v) => setIntakeYear(Number(v) || intakeYear)}
                min={2000}
                max={2100}
                w={140}
                allowDecimal={false}
              />
              <Button
                leftSection={<Play size={16} />}
                loading={busy === "preview"}
                onClick={() => run("/rules/preview")}
              >
                Preview
              </Button>
              <Button
                variant="default"
                leftSection={<Save size={16} />}
                loading={busy === "save"}
                disabled={!preview}
                onClick={() => run("/rules")}
              >
                Save as active
              </Button>
            </Group>

            {!preview && (
              <Text size="xs" c="dimmed">
                Saving is available once you have previewed the rule, so nothing
                takes effect before you have seen what it does.
              </Text>
            )}
          </Stack>
        </Card>
      )}

      {ruleError && (
        <Alert
          color="red"
          variant="light"
          icon={<CircleAlert size={18} />}
          title="That rule did not work"
        >
          {ruleError}
        </Alert>
      )}

      {preview && (
        <Card>
          <Text fw={700} mb="md">
            What this rule would do
          </Text>
          <SimpleGrid cols={{ base: 2, sm: 3, md: 5 }} spacing="lg">
            <Stat
              label="Would be admitted"
              value={preview.after}
              hint={`${preview.pass_rate_after.toFixed(1)}% pass rate`}
            />
            {!preview.first_rule && (
              <>
                <Stat
                  label="Admitted now"
                  value={preview.before ?? "—"}
                  hint={
                    preview.pass_rate_before !== null
                      ? `${preview.pass_rate_before.toFixed(1)}% pass rate`
                      : undefined
                  }
                />
                <Stat
                  label="Change"
                  value={
                    <Text
                      component="span"
                      className={classes.statValue}
                      c={
                        (preview.change ?? 0) > 0
                          ? "var(--status-accepted)"
                          : (preview.change ?? 0) < 0
                            ? "var(--status-denied)"
                            : undefined
                      }
                    >
                      {(preview.change ?? 0) > 0 ? "+" : ""}
                      {preview.change ?? 0}
                    </Text>
                  }
                  hint={
                    preview.pct_change !== null
                      ? `${preview.pct_change > 0 ? "+" : ""}${preview.pct_change.toFixed(1)}%`
                      : undefined
                  }
                />
              </>
            )}
            <Stat
              label="Not evaluable"
              value={preview.not_evaluable}
              hint="no mark for a course this rule uses"
            />
          </SimpleGrid>

          {preview.not_evaluable > 0 && (
            <Alert color="attention" variant="light" mt="md">
              {preview.not_evaluable} applicant
              {preview.not_evaluable === 1 ? " has" : "s have"} no mark for a
              course this rule uses. They are counted as not admitted, so the
              headline number above is a floor rather than an estimate.
            </Alert>
          )}

          {preview.first_rule && (
            <Text size="sm" c="dimmed" mt="md">
              This would be the first rule for {intakeYear}, so there is nothing
              to compare it against yet.
            </Text>
          )}
        </Card>
      )}

      <div>
        <Text fw={700} mb="xs">
          Saved rules
        </Text>
        {error && <ErrorState error={error} />}
        {loading ? (
          <LoadingState label="Loading rules" />
        ) : rules.length === 0 ? (
          <EmptyState
            title="No rules saved yet"
            hint="Until a rule is in force, nothing is being evaluated automatically and every decision is made by hand."
          />
        ) : (
          <TableCard minWidth={720}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Version</Table.Th>
                  <Table.Th>Intake</Table.Th>
                  <Table.Th>Rule</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>By</Table.Th>
                  <Table.Th>Saved</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {rules.map((rule) => (
                  <Table.Tr key={rule.rule_id}>
                    <Table.Td className="identifier">{rule.version}</Table.Td>
                    <Table.Td className="identifier">
                      {rule.intake_year}
                    </Table.Td>
                    <Table.Td>
                      <Code>{rule.rule}</Code>
                    </Table.Td>
                    <Table.Td>
                      <Badge
                        color={rule.status === "active" ? "green" : "gray"}
                        variant="light"
                      >
                        {rule.status}
                      </Badge>
                    </Table.Td>
                    <Table.Td className="identifier">
                      {rule.created_by}
                    </Table.Td>
                    <Table.Td>
                      <Text size="xs">{formatDateTime(rule.created_at)}</Text>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </TableCard>
        )}
      </div>
    </Stack>
  );
}
