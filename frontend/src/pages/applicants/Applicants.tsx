import { useMemo, useState } from "react";
import {
  Anchor,
  Button,
  Group,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
} from "@mantine/core";
import { RefreshCw, Search } from "lucide-react";
import { Link } from "react-router-dom";
import PageHeader from "../../components/PageHeader";
import TableCard from "../../components/TableCard";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { useResource } from "../../lib/useResource";
import type { Applicant, CitizenshipResidency } from "../../types/api";

const CITIZENSHIPS: CitizenshipResidency[] = [
  "SA Citizen",
  "International",
  "Permanent Resident",
];

export default function Applicants() {
  const { data, loading, error, reload } =
    useResource<Applicant[]>("/applicants?limit=500");
  const [query, setQuery] = useState("");
  const [citizenship, setCitizenship] = useState<string | null>(null);

  const applicants = useMemo(() => data ?? [], [data]);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return applicants.filter((a) => {
      if (citizenship && a.citizenship_residency !== citizenship) return false;
      if (!q) return true;
      return (
        a.campus_id.toLowerCase().includes(q) ||
        `${a.first_name} ${a.last_name}`.toLowerCase().includes(q) ||
        (a.email ?? "").toLowerCase().includes(q)
      );
    });
  }, [applicants, query, citizenship]);

  return (
    <Stack gap="lg">
      <PageHeader
        title="Applicants"
        description="Everyone in the cycle. Open one to see their applications, marks, motivation and the committee's notes and votes."
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
          placeholder="Name, campus ID or email"
          leftSection={<Search size={16} />}
          value={query}
          onChange={(e) => setQuery(e.currentTarget.value)}
          style={{ flex: "1 1 20rem" }}
        />
        <Select
          label="Citizenship"
          placeholder="Any"
          data={CITIZENSHIPS}
          value={citizenship}
          onChange={setCitizenship}
          clearable
          w={200}
        />
      </Group>

      {error && <ErrorState error={error} />}

      {loading ? (
        <LoadingState label="Loading applicants" />
      ) : applicants.length === 0 ? (
        <EmptyState
          title="No applicants yet"
          hint="Import an ASR sheet and the people it describes will appear here. ASR is the only source that creates applicants."
          action={
            <Button component={Link} to="/imports" mt="sm">
              Go to imports
            </Button>
          }
        />
      ) : visible.length === 0 ? (
        <EmptyState
          title="Nothing matches that search"
          hint={`None of the ${applicants.length} applicants match what you typed.`}
        />
      ) : (
        <>
          <Text size="sm" c="dimmed">
            Showing {visible.length} of {applicants.length}
          </Text>
          <TableCard minWidth={760}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Campus ID</Table.Th>
                  <Table.Th>Name</Table.Th>
                  <Table.Th>Citizenship</Table.Th>
                  <Table.Th>Email</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {visible.map((a) => (
                  <Table.Tr key={a.campus_id}>
                    <Table.Td>
                      <Anchor
                        component={Link}
                        to={`/applicants/${a.campus_id}`}
                        className="identifier"
                        fw={700}
                      >
                        {a.campus_id}
                      </Anchor>
                    </Table.Td>
                    <Table.Td>
                      {a.title === "Unspecified" ? "" : `${a.title} `}
                      {a.first_name} {a.last_name}
                    </Table.Td>
                    <Table.Td>{a.citizenship_residency}</Table.Td>
                    <Table.Td>
                      {a.email ? (
                        <Text size="sm">{a.email}</Text>
                      ) : (
                        <Text size="sm" c="dimmed">
                          none on file
                        </Text>
                      )}
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
