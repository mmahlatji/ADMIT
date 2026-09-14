import {
  Anchor,
  Badge,
  Button,
  Card,
  Grid,
  Group,
  Stack,
  Table,
  Text,
} from "@mantine/core";
import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/States";
import { ApplicationStatusBadge } from "../../components/StatusBadge";
import { formatDate } from "../../lib/format";
import { useResource } from "../../lib/useResource";
import type { ApplicantDetail as Detail } from "../../types/api";
import NotesPanel from "./NotesPanel";
import VotesPanel from "./VotesPanel";

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <Text size="xs" c="dimmed" tt="uppercase" fw={700}>
        {label}
      </Text>
      <Text size="sm">{value || "—"}</Text>
    </div>
  );
}

export default function ApplicantDetail() {
  const { campusId = "" } = useParams();
  const { data, loading, error, reload } = useResource<Detail>(
    campusId ? `/applicants/${encodeURIComponent(campusId)}` : null,
  );

  if (loading) return <LoadingState label="Loading applicant" />;
  if (error) return <ErrorState error={error} />;
  if (!data) return null;

  const name = [
    data.title === "Unspecified" ? null : data.title,
    data.first_name,
    data.last_name,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Stack gap="lg">
      <Anchor component={Link} to="/applicants" size="sm">
        <Group gap={4}>
          <ArrowLeft size={14} />
          All applicants
        </Group>
      </Anchor>

      <PageHeader
        title={name}
        description={`Campus ID ${data.campus_id} · ${data.citizenship_residency}`}
      />

      <Card>
        <Grid gutter="lg">
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
            <Field
              label="Campus ID"
              value={<span className="identifier">{data.campus_id}</span>}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
            <Field
              label="Student number"
              value={<span className="identifier">{data.employee_id}</span>}
            />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
            <Field label="Email" value={data.email} />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
            <Field label="Cell" value={data.cell_phone} />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
            <Field label="Citizenship" value={data.citizenship_residency} />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
            <Field label="Non-SA citizenship" value={data.non_sa_citizenship} />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
            <Field label="Date of birth" value={formatDate(data.birth_date)} />
          </Grid.Col>
          <Grid.Col span={{ base: 6, sm: 4, md: 3 }}>
            <Field label="Population group" value={data.population_group} />
          </Grid.Col>
        </Grid>
      </Card>

      <Card padding={0}>
        <Text fw={700} p="lg" pb="xs">
          Applications
        </Text>
        {data.applications.length === 0 ? (
          <Text size="sm" c="dimmed" px="lg" pb="lg">
            None on file.
          </Text>
        ) : (
          <Table.ScrollContainer minWidth={720} type="native">
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Number</Table.Th>
                  <Table.Th>Plan</Table.Th>
                  <Table.Th>Choice</Table.Th>
                  <Table.Th>Applied</Table.Th>
                  <Table.Th>Status</Table.Th>
                  <Table.Th>Flags</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {data.applications.map((a) => (
                  <Table.Tr key={a.application_id}>
                    <Table.Td className="identifier">
                      {a.application_number}
                    </Table.Td>
                    <Table.Td>{a.academic_plan1}</Table.Td>
                    <Table.Td>
                      {a.choice === "FRST" ? "First" : "Second"}
                    </Table.Td>
                    <Table.Td>{formatDate(a.application_date)}</Table.Td>
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
          </Table.ScrollContainer>
        )}
      </Card>

      <Grid gutter="md">
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card padding={0} h="100%">
            <Text fw={700} p="lg" pb="xs">
              Marks
            </Text>
            {data.applicant_marks.length === 0 ? (
              <Text size="sm" c="dimmed" px="lg" pb="lg">
                No marks imported. Upload a UCT marks or IT transcripts sheet.
              </Text>
            ) : (
              <Table.ScrollContainer minWidth={320} type="native">
                <Table>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Course</Table.Th>
                      <Table.Th>Mark</Table.Th>
                      <Table.Th>Result</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {data.applicant_marks.map((m) => (
                      <Table.Tr key={m.mark_id}>
                        <Table.Td className="identifier">
                          {m.course_code}
                        </Table.Td>
                        <Table.Td className="identifier">{m.mark}</Table.Td>
                        <Table.Td>
                          {m.result_code === "NONE" ? (
                            <Text size="xs" c="dimmed">
                              —
                            </Text>
                          ) : (
                            <Badge size="xs" color="attention">
                              {m.result_code}
                            </Badge>
                          )}
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </Table.ScrollContainer>
            )}
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card h="100%">
            <Text fw={700} mb="xs">
              Motivation
            </Text>
            {data.motivation?.motivation ? (
              <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
                {data.motivation.motivation}
              </Text>
            ) : (
              <Text size="sm" c="dimmed">
                None on file. Upload a motivations sheet to fill this in.
              </Text>
            )}
          </Card>
        </Grid.Col>
      </Grid>

      <Grid gutter="md">
        <Grid.Col span={{ base: 12, md: 6 }}>
          <NotesPanel
            campusId={data.campus_id}
            notes={data.notes}
            onChanged={reload}
          />
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <VotesPanel
            campusId={data.campus_id}
            applications={data.applications}
          />
        </Grid.Col>
      </Grid>

      <Group>
        <Button component={Link} to="/decisions" variant="default">
          Record a decision
        </Button>
      </Group>
    </Stack>
  );
}
