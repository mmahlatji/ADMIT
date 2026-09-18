import { useState } from "react";
import {
  ActionIcon,
  Alert,
  Button,
  Card,
  Code,
  Group,
  Stack,
  Table,
  Text,
  Textarea,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import {
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Sparkles,
  Trash2,
} from "lucide-react";
import PageHeader from "../../components/PageHeader";
import TableCard from "../../components/TableCard";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { api } from "../../lib/api";
import { formatDate, formatDateTime } from "../../lib/format";
import { useResource } from "../../lib/useResource";
import type {
  QueryAskResponse,
  QueryResult,
  QueryRow,
  SavedQueryMeta,
} from "../../types/api";
import classes from "./Ask.module.css";

// Matches the API's own default page size. Its ceiling is 500.
const PAGE_SIZE = 100;

const EXAMPLES = [
  "How many applications were denied this year?",
  "List applicants who scored above 70 in csc3003s",
  "Count applicants by population group",
];

const ISO_DATE_TIME = /^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}/;
const ISO_DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;

/**
 * Column names in first-seen order across the whole page rather than from the
 * first row alone, so a null-free row later on cannot introduce a column the
 * header never drew.
 */
function columnsOf(rows: QueryRow[]): string[] {
  const seen: string[] = [];
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (!seen.includes(key)) seen.push(key);
    }
  }
  return seen;
}

function Cell({ value }: { value: unknown }) {
  if (value === null || value === undefined) {
    return (
      <Text size="sm" c="dimmed">
        —
      </Text>
    );
  }
  if (typeof value === "boolean") return <>{value ? "Yes" : "No"}</>;
  if (typeof value === "number") {
    return <span className="identifier">{value}</span>;
  }
  if (typeof value === "object") {
    return <Code>{JSON.stringify(value)}</Code>;
  }

  const text = String(value);
  if (ISO_DATE_TIME.test(text)) {
    return <span className="identifier">{formatDateTime(text)}</span>;
  }
  if (ISO_DATE_ONLY.test(text)) {
    return <span className="identifier">{formatDate(text)}</span>;
  }
  return (
    <div className={classes.cell} title={text}>
      {text}
    </div>
  );
}

type Shown = {
  queryId: string;
  title: string;
  prompt: string;
  rows: QueryResult;
  skip: number;
};

export default function Ask() {
  const saved = useResource<SavedQueryMeta[]>("/api/query");
  const [prompt, setPrompt] = useState("");
  const [asking, setAsking] = useState(false);
  const [paging, setPaging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shown, setShown] = useState<Shown | null>(null);

  const history = saved.data ?? [];

  async function ask() {
    const question = prompt.trim();
    if (!question) return;

    setAsking(true);
    setError(null);
    try {
      const answer = await api.request<QueryAskResponse>("/api/query", {
        method: "POST",
        body: JSON.stringify({ prompt: question }),
      });
      setShown({
        queryId: answer.query_id,
        title: answer.title ?? question,
        prompt: question,
        rows: answer.rows ?? [],
        skip: 0,
      });
      await saved.reload();
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Could not answer that question",
      );
    } finally {
      setAsking(false);
    }
  }

  // Paging replays the stored query against the live database. There is no
  // second model call, so this is quick where asking is not.
  async function load(
    meta: { query_id: string; prompt: string; title: string | null },
    skip: number,
  ) {
    setPaging(true);
    setError(null);
    try {
      const rows = await api.request<QueryResult>(
        `/api/query/${meta.query_id}?skip=${skip}&limit=${PAGE_SIZE}`,
      );
      setShown({
        queryId: meta.query_id,
        title: meta.title ?? meta.prompt,
        prompt: meta.prompt,
        rows,
        skip,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not run that question");
    } finally {
      setPaging(false);
    }
  }

  async function remove(meta: SavedQueryMeta) {
    try {
      await api.request(`/api/query/${meta.query_id}`, { method: "DELETE" });
      if (shown?.queryId === meta.query_id) setShown(null);
      await saved.reload();
    } catch (e) {
      notifications.show({
        color: "red",
        title: "Could not delete that question",
        message: e instanceof Error ? e.message : "Something went wrong.",
      });
    }
  }

  const rows = shown && Array.isArray(shown.rows) ? shown.rows : null;
  const count = shown && typeof shown.rows === "number" ? shown.rows : null;
  // Nothing in the response says how many rows there are in total, so a full
  // page is the only evidence that another one might exist.
  const hasMore = rows !== null && rows.length === PAGE_SIZE;
  const columns = rows === null ? [] : columnsOf(rows);
  // How many columns come back is whatever the question asked for, so the width
  // at which the table starts scrolling has to be computed rather than fixed.
  // At a fixed 640 a nine-column answer squashes campus_id onto two lines.
  const tableMinWidth = Math.max(640, columns.length * 150);

  return (
    <Stack gap="lg">
      <PageHeader
        title="Ask"
        description="Ask a question about this intake in plain English. It is answered by a model running locally against the live database, and it only ever reads."
      />

      <Card>
        <Stack gap="sm">
          <Textarea
            label="Your question"
            placeholder="How many applicants are there from each population group?"
            value={prompt}
            onChange={(e) => setPrompt(e.currentTarget.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) ask();
            }}
            autosize
            minRows={2}
            maxRows={6}
          />

          <Group gap="xs" align="center">
            <Text size="xs" c="dimmed">
              For example:
            </Text>
            {EXAMPLES.map((example) => (
              <Button
                key={example}
                size="compact-xs"
                variant="default"
                onClick={() => setPrompt(example)}
              >
                {example}
              </Button>
            ))}
          </Group>

          <Group justify="space-between" align="center">
            <Text size="xs" c="dimmed">
              The first question after the model starts up can take a minute.
            </Text>
            <Button
              leftSection={<Sparkles size={16} />}
              loading={asking}
              disabled={!prompt.trim()}
              onClick={ask}
            >
              Ask
            </Button>
          </Group>
        </Stack>
      </Card>

      {error && (
        <Alert
          color="red"
          variant="light"
          icon={<CircleAlert size={18} />}
          title="That question did not work"
        >
          <Stack gap={4}>
            <Text size="sm">{error}</Text>
            {error.includes("reach") && (
              <Text size="xs" c="dimmed">
                The model runs in the ollama container. If it is not up, nothing
                here can be answered.
              </Text>
            )}
          </Stack>
        </Alert>
      )}

      {asking && <LoadingState label="Working out how to answer that" />}

      {shown && !asking && (
        <Card>
          <Stack gap="md">
            <Group justify="space-between" align="flex-start" wrap="wrap">
              <Stack gap={2} style={{ flex: "1 1 20rem" }}>
                <Text fw={700}>{shown.title}</Text>
                {/* The model does not always name a query, and the fallback
                    title is the question itself. Printing both then says the
                    same sentence twice. */}
                {shown.title !== shown.prompt && (
                  <Text size="xs" c="dimmed">
                    {shown.prompt}
                  </Text>
                )}
              </Stack>
              {rows !== null && (rows.length > 0 || shown.skip > 0) && (
                <Group gap="xs" align="center">
                  <Text size="xs" c="dimmed" className="identifier">
                    {rows.length > 0
                      ? `${shown.skip + 1} to ${shown.skip + rows.length}`
                      : "no more rows"}
                  </Text>
                  <ActionIcon
                    variant="default"
                    aria-label="Previous page"
                    disabled={shown.skip === 0 || paging}
                    onClick={() =>
                      load(
                        {
                          query_id: shown.queryId,
                          prompt: shown.prompt,
                          title: shown.title,
                        },
                        Math.max(0, shown.skip - PAGE_SIZE),
                      )
                    }
                  >
                    <ChevronLeft size={16} />
                  </ActionIcon>
                  <ActionIcon
                    variant="default"
                    aria-label="Next page"
                    disabled={!hasMore || paging}
                    onClick={() =>
                      load(
                        {
                          query_id: shown.queryId,
                          prompt: shown.prompt,
                          title: shown.title,
                        },
                        shown.skip + PAGE_SIZE,
                      )
                    }
                  >
                    <ChevronRight size={16} />
                  </ActionIcon>
                </Group>
              )}
            </Group>

            {count !== null && (
              <div>
                <div className={classes.countValue}>
                  {count.toLocaleString("en-ZA")}
                </div>
                <Text size="xs" c="dimmed">
                  This question was answered as a count, so there are no rows to
                  page through.
                </Text>
              </div>
            )}

            {rows !== null &&
              (rows.length === 0 ? (
                shown.skip === 0 ? (
                  <EmptyState
                    title="Nothing matched"
                    hint="The question was understood and ran, it just found no rows."
                  />
                ) : (
                  <Text size="sm" c="dimmed">
                    That is the end of the results.
                  </Text>
                )
              ) : (
                <TableCard minWidth={tableMinWidth}>
                  <Table striped highlightOnHover>
                    <Table.Thead>
                      <Table.Tr>
                        {columns.map((column) => (
                          <Table.Th key={column} className={classes.columnName}>
                            {column}
                          </Table.Th>
                        ))}
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {rows.map((row, index) => (
                        <Table.Tr key={shown.skip + index}>
                          {columns.map((column) => (
                            <Table.Td key={column}>
                              <Cell value={row[column]} />
                            </Table.Td>
                          ))}
                        </Table.Tr>
                      ))}
                    </Table.Tbody>
                  </Table>
                </TableCard>
              ))}
          </Stack>
        </Card>
      )}

      <div>
        <Text fw={700} mb="xs">
          Your earlier questions
        </Text>
        {saved.error && <ErrorState error={saved.error} />}
        {saved.loading ? (
          <LoadingState label="Loading your questions" />
        ) : history.length === 0 ? (
          <EmptyState
            title="You have not asked anything yet"
            hint="Every question you ask is kept here so you can run it again later against whatever the data says then."
          />
        ) : (
          <TableCard minWidth={560}>
            <Table highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Question</Table.Th>
                  <Table.Th>Asked</Table.Th>
                  <Table.Th />
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {history.map((meta) => (
                  <Table.Tr key={meta.query_id}>
                    <Table.Td>
                      <Stack gap={0}>
                        <Text size="sm" fw={500}>
                          {meta.title ?? meta.prompt}
                        </Text>
                        {meta.title && (
                          <Text size="xs" c="dimmed">
                            {meta.prompt}
                          </Text>
                        )}
                      </Stack>
                    </Table.Td>
                    <Table.Td>
                      <Text size="xs">{formatDateTime(meta.created_at)}</Text>
                    </Table.Td>
                    <Table.Td>
                      <Group gap="xs" justify="flex-end" wrap="nowrap">
                        <Button
                          size="compact-xs"
                          variant="default"
                          loading={paging && shown?.queryId === meta.query_id}
                          onClick={() => load(meta, 0)}
                        >
                          Run again
                        </Button>
                        <ActionIcon
                          variant="subtle"
                          color="red"
                          aria-label="Delete this question"
                          onClick={() => remove(meta)}
                        >
                          <Trash2 size={16} />
                        </ActionIcon>
                      </Group>
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
