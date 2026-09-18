import { useState } from "react";
import {
  ActionIcon,
  Button,
  Card,
  Group,
  Stack,
  Text,
  Tooltip,
} from "@mantine/core";
import { Dropzone, type FileWithPath } from "@mantine/dropzone";
import { notifications } from "@mantine/notifications";
import { ExternalLink, FileText, Upload, X } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import { notifyTabBlocked, openTab, signedUrlFor } from "../../lib/documents";
import { formatDateTime } from "../../lib/format";
import { can, CONVENOR_ADMIN } from "../../lib/roles";
import { useResource } from "../../lib/useResource";
import type { StudentDocument } from "../../types/api";

// Mirrors STUDENT_DOCUMENT_EXTENSIONS and MAX_FILE_SIZE in
// app/services/storage. Rejecting here is only a courtesy; the API rejects too.
const ACCEPT = ["application/pdf"];
const MAX_BYTES = 1_000_000;

export default function DocumentsPanel({ campusId }: { campusId: string }) {
  const { user } = useAuth();
  const canUpload = can(user?.role ?? null, CONVENOR_ADMIN);

  const { data, loading, error, reload } = useResource<StudentDocument[]>(
    `/applicants/${encodeURIComponent(campusId)}/documents`,
  );
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [opening, setOpening] = useState<string | null>(null);

  const documents = data ?? [];

  async function upload() {
    if (!file) return;
    setUploading(true);
    setUploadError(null);
    try {
      const body = new FormData();
      body.append("file", file);
      await api.request<StudentDocument>(
        `/applicants/${encodeURIComponent(campusId)}/documents`,
        { method: "POST", body },
      );
      setFile(null);
      await reload();
      notifications.show({
        color: "green",
        title: "Document uploaded",
        message: "It is attached to this applicant.",
      });
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function openDocument(doc: StudentDocument) {
    const tab = openTab();
    setOpening(doc.document_id);
    try {
      const url = await signedUrlFor(`/student_documents/${doc.document_id}`);
      if (!tab.go(url)) notifyTabBlocked(url, doc.original_file_name);
    } catch (e) {
      tab.cancel();
      notifications.show({
        color: "red",
        title: "Could not open that document",
        message: e instanceof Error ? e.message : "Something went wrong.",
      });
    } finally {
      setOpening(null);
    }
  }

  return (
    <Card>
      <Text fw={700} mb={4}>
        Documents
      </Text>
      <Text size="xs" c="dimmed" mb="md">
        Anything scanned or emailed in that belongs on this applicant's record.
        Marks and motivations come from the import sheets instead.
      </Text>

      {canUpload && (
        <Stack gap="xs" mb="lg">
          <Dropzone
            onDrop={(files: FileWithPath[]) => {
              setUploadError(null);
              if (files[0]) setFile(files[0]);
            }}
            onReject={() =>
              setUploadError("A document has to be a PDF of 1 MB or less.")
            }
            accept={ACCEPT}
            maxSize={MAX_BYTES}
            maxFiles={1}
            multiple={false}
            disabled={uploading}
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
                <FileText size={20} />
              </Dropzone.Idle>
              <Text size="sm" c={file ? undefined : "dimmed"}>
                {file ? file.name : "Drop a PDF, or click"}
              </Text>
            </Group>
          </Dropzone>

          {uploadError && (
            <Text size="xs" c="red">
              {uploadError}
            </Text>
          )}

          <Group justify="space-between">
            <Text size="xs" c="dimmed">
              PDF, up to 1 MB.
            </Text>
            <Group gap="xs">
              {file && (
                <Button
                  size="compact-sm"
                  variant="subtle"
                  onClick={() => setFile(null)}
                  disabled={uploading}
                >
                  Remove
                </Button>
              )}
              <Button
                size="compact-sm"
                onClick={upload}
                loading={uploading}
                disabled={!file}
              >
                Upload
              </Button>
            </Group>
          </Group>
        </Stack>
      )}

      {error ? (
        <Text size="sm" c="red">
          {error}
        </Text>
      ) : loading ? (
        <Text size="sm" c="dimmed">
          Loading documents.
        </Text>
      ) : documents.length === 0 ? (
        <Text size="sm" c="dimmed">
          Nothing uploaded yet.
        </Text>
      ) : (
        <Stack gap="xs">
          {documents.map((doc) => (
            <Group
              key={doc.document_id}
              justify="space-between"
              gap="xs"
              wrap="nowrap"
            >
              <Stack gap={0} style={{ minWidth: 0 }}>
                <Text size="sm" lineClamp={1}>
                  {doc.original_file_name}
                </Text>
                <Text size="xs" c="dimmed">
                  {formatDateTime(doc.uploaded_at)}
                </Text>
              </Stack>
              <Tooltip label="Open in a new tab">
                <ActionIcon
                  variant="subtle"
                  aria-label={`Open ${doc.original_file_name}`}
                  loading={opening === doc.document_id}
                  onClick={() => openDocument(doc)}
                >
                  <ExternalLink size={16} />
                </ActionIcon>
              </Tooltip>
            </Group>
          ))}
        </Stack>
      )}
    </Card>
  );
}
