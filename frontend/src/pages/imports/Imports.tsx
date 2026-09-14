import { useState } from "react";
import {
  Alert,
  Badge,
  Button,
  Card,
  Group,
  SimpleGrid,
  Stack,
  Table,
  Text,
} from "@mantine/core";
import { Dropzone, type FileWithPath } from "@mantine/dropzone";
import { notifications } from "@mantine/notifications";
import { CircleAlert, FileSpreadsheet, RefreshCw, Upload, X } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import TableCard from "../../components/TableCard";
import { EmptyState, ErrorState, LoadingState } from "../../components/States";
import { ImportStatusBadge } from "../../components/StatusBadge";
import { api } from "../../lib/api";
import { formatDateTime, sourceLabel } from "../../lib/format";
import { useResource } from "../../lib/useResource";
import { SOURCE_TYPES, type ImportRun, type SourceType } from "../../types/api";

const ACCEPT = [
  "text/csv",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
];

const DESCRIPTIONS: Record<SourceType, string> = {
  asr: "The only sheet that creates applicants. Upload this first.",
  uct_marks: "Course marks for applicants already on file.",
  motivations: "Motivation text, matched by campus ID.",
  it_transcripts: "Transcript marks from IT, matched by campus ID.",
};

function SlotDropzone({
  source,
  file,
  onDrop,
  onClear,
  error,
  busy,
}: {
  source: SourceType;
  file: File | null;
  onDrop: (file: File) => void;
  onClear: () => void;
  error?: string;
  busy: boolean;
}) {
  return (
    <Card>
      <Group justify="space-between" mb={4}>
        <Text fw={700} size="sm">
          {sourceLabel(source)}
        </Text>
        {source === "asr" && (
          <Badge size="xs" color="attention">
            first
          </Badge>
        )}
      </Group>
      <Text size="xs" c="dimmed" mb="sm">
        {DESCRIPTIONS[source]}
      </Text>

      <Dropzone
        onDrop={(files: FileWithPath[]) => files[0] && onDrop(files[0])}
        accept={ACCEPT}
        maxFiles={1}
        multiple={false}
        disabled={busy}
        py="md"
      >
        <Group justify="center" gap="xs" style={{ pointerEvents: "none" }}>
          <Dropzone.Accept>
            <Upload size={20} />
          </Dropzone.Accept>
          <Dropzone.Reject>
            <X size={20} />
          </Dropzone.Reject>
          <Dropzone.Idle>
            <FileSpreadsheet size={20} />
          </Dropzone.Idle>
          <Text size="sm" c={file ? undefined : "dimmed"}>
            {file ? file.name : "Drop a .csv or .xlsx, or click"}
          </Text>
        </Group>
      </Dropzone>

      {file && (
        <Group justify="space-between" mt="xs">
          <Text size="xs" c="dimmed">
            {(file.size / 1024).toFixed(0)} KB
          </Text>
          <Button size="compact-xs" variant="subtle" onClick={onClear}>
            Remove
          </Button>
        </Group>
      )}

      {error && (
        <Text size="xs" c="red" mt="xs">
          {error}
        </Text>
      )}
    </Card>
  );
}

export default function Imports() {
  const { data, loading, error, reload } = useResource<ImportRun[]>(
    "/import_runs?limit=100",
  );
  const [files, setFiles] = useState<Partial<Record<SourceType, File>>>({});
  const [errors, setErrors] = useState<Partial<Record<SourceType, string>>>({});
  const [uploading, setUploading] = useState(false);

  const chosen = SOURCE_TYPES.filter((s) => files[s]);

  async function uploadAll() {
    setUploading(true);
    setErrors({});

    const uploadOne = async (source: SourceType) => {
      const body = new FormData();
      body.append("file", files[source]!);
      return api.request<ImportRun>(`/imports/${source}`, {
        method: "POST",
        body,
      });
    };

    // ASR has to finish before the others start. It is the only source that
    // creates applicants, and marks, motivations and transcripts all look one
    // up by campus_id and flag the row when it is missing. Uploading them all
    // at once races them against ASR and produces spurious "no applicant
    // found" rows in the conflict queue.
    const asr = chosen.filter((s) => s === "asr");
    const rest = chosen.filter((s) => s !== "asr");
    const ordered = [...asr, ...rest];

    const results = [
      ...(await Promise.allSettled(asr.map(uploadOne))),
      ...(await Promise.allSettled(rest.map(uploadOne))),
    ];

    const failed: Partial<Record<SourceType, string>> = {};
    results.forEach((result, i) => {
      if (result.status === "rejected") {
        failed[ordered[i]] =
          result.reason instanceof Error
            ? result.reason.message
            : "Upload failed";
      }
    });

    setErrors(failed);
    const succeeded = ordered.length - Object.keys(failed).length;

    if (succeeded > 0) {
      notifications.show({
        color: "green",
        title: `${succeeded} sheet${succeeded === 1 ? "" : "s"} imported`,
        message: "The run history below shows what each one did.",
      });
      setFiles((prev) => {
        const next = { ...prev };
        for (const source of ordered) if (!failed[source]) delete next[source];
        return next;
      });
    }
    if (Object.keys(failed).length > 0) {
      notifications.show({
        color: "red",
        title: "Some sheets were rejected",
        message: "Each one says why under its box.",
        autoClose: false,
      });
    }

    setUploading(false);
    await reload();
  }

  const runs = data ?? [];

  return (
    <Stack gap="lg">
      <PageHeader
        title="Imports"
        description="Upload the source sheets. Re-importing a sheet updates records in place rather than duplicating them, and never overturns a decision a convenor has already made."
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

      {files.asr === undefined && chosen.length > 0 && runs.length === 0 && (
        <Alert
          color="attention"
          variant="light"
          icon={<CircleAlert size={18} />}
          title="No ASR sheet yet"
        >
          Nothing has been imported before, and ASR is the only source that
          creates applicants. Uploading marks or motivations first will flag
          every row as having no applicant to attach to.
        </Alert>
      )}

      <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
        {SOURCE_TYPES.map((source) => (
          <SlotDropzone
            key={source}
            source={source}
            file={files[source] ?? null}
            busy={uploading}
            error={errors[source]}
            onDrop={(file) => setFiles((prev) => ({ ...prev, [source]: file }))}
            onClear={() =>
              setFiles((prev) => {
                const next = { ...prev };
                delete next[source];
                return next;
              })
            }
          />
        ))}
      </SimpleGrid>

      <Group justify="flex-end">
        <Button
          onClick={uploadAll}
          loading={uploading}
          disabled={chosen.length === 0}
          leftSection={<Upload size={16} />}
        >
          Import {chosen.length > 0 ? `${chosen.length} sheet` : "sheets"}
          {chosen.length > 1 ? "s" : ""}
        </Button>
      </Group>

      <div>
        <Text fw={700} mb="xs">
          Import history
        </Text>
        {error && <ErrorState error={error} />}
        {loading ? (
          <LoadingState label="Loading import history" />
        ) : runs.length === 0 ? (
          <EmptyState
            title="Nothing imported yet"
            hint="Once a sheet is imported, this shows how many rows loaded, how many were matched to an existing applicant, and how many were flagged for review."
          />
        ) : (
          <TableCard minWidth={880}>
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Source</Table.Th>
                  <Table.Th>File</Table.Th>
                  <Table.Th>Uploaded</Table.Th>
                  <Table.Th>By</Table.Th>
                  <Table.Th>Loaded</Table.Th>
                  <Table.Th>Matched</Table.Th>
                  <Table.Th>New</Table.Th>
                  <Table.Th>Flagged</Table.Th>
                  <Table.Th>Rejected</Table.Th>
                  <Table.Th>Status</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {runs.map((run) => (
                  <Table.Tr key={run.import_run_id}>
                    <Table.Td>{sourceLabel(run.source_type)}</Table.Td>
                    <Table.Td>
                      <Text size="sm" lineClamp={1} maw={220}>
                        {run.file_name}
                      </Text>
                    </Table.Td>
                    <Table.Td>
                      <Text size="xs">{formatDateTime(run.uploaded_at)}</Text>
                    </Table.Td>
                    <Table.Td className="identifier">
                      {run.uploaded_by}
                    </Table.Td>
                    <Table.Td className="identifier">
                      {run.rows_loaded}/{run.rows_total}
                    </Table.Td>
                    <Table.Td className="identifier">
                      {run.rows_auto_matched}
                    </Table.Td>
                    <Table.Td className="identifier">
                      {run.rows_auto_new}
                    </Table.Td>
                    <Table.Td>
                      {run.rows_flagged > 0 ? (
                        <Badge size="sm" color="attention">
                          {run.rows_flagged}
                        </Badge>
                      ) : (
                        <span className="identifier">0</span>
                      )}
                    </Table.Td>
                    <Table.Td>
                      {run.rows_rejected > 0 ? (
                        <Badge size="sm" color="red">
                          {run.rows_rejected}
                        </Badge>
                      ) : (
                        <span className="identifier">0</span>
                      )}
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
    </Stack>
  );
}
