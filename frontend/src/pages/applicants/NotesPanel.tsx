import { useState } from "react";
import {
  ActionIcon,
  Button,
  Card,
  Group,
  Stack,
  Text,
  Textarea,
  Tooltip,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { Trash2 } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../lib/api";
import { formatDateTime } from "../../lib/format";
import type { Note } from "../../types/api";

export default function NotesPanel({
  campusId,
  notes,
  onChanged,
}: {
  campusId: string;
  notes: Note[];
  onChanged: () => void;
}) {
  const { user } = useAuth();
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  async function addNote() {
    const trimmed = content.trim();
    if (!trimmed) return;
    setSaving(true);
    try {
      await api.request<Note>("/notes", {
        method: "POST",
        body: JSON.stringify({
          campus_id: campusId,
          // NoteCreate requires author_id, though create_note ignores it and
          // attributes the note to the authenticated user. Omitting it is a
          // 422, so it is sent and the server's own value is what sticks.
          author_id: user?.employee_id,
          content: trimmed,
        }),
      });
      setContent("");
      onChanged();
    } catch (e) {
      notifications.show({
        color: "red",
        title: "Note not saved",
        message: e instanceof Error ? e.message : "Something went wrong",
      });
    } finally {
      setSaving(false);
    }
  }

  async function deleteNote(note: Note) {
    setDeleting(note.note_id);
    try {
      await api.request(`/notes/${note.note_id}`, { method: "DELETE" });
      onChanged();
    } catch (e) {
      notifications.show({
        color: "red",
        title: "Note not deleted",
        message: e instanceof Error ? e.message : "Something went wrong",
      });
    } finally {
      setDeleting(null);
    }
  }

  const sorted = [...notes].sort(
    (a, b) => Date.parse(b.created_at) - Date.parse(a.created_at),
  );

  return (
    <Card>
      <Text fw={700} mb={4}>
        Notes
      </Text>
      <Text size="xs" c="dimmed" mb="md">
        A note is your own record of your reasoning. Everyone on the committee
        can read it, and only you can delete it.
      </Text>

      <Stack gap="xs" mb="lg">
        <Textarea
          label="Add a note"
          placeholder="What stood out, and why"
          autosize
          minRows={2}
          maxRows={8}
          value={content}
          onChange={(e) => setContent(e.currentTarget.value)}
        />
        <Group justify="flex-end">
          <Button
            onClick={addNote}
            loading={saving}
            disabled={content.trim().length === 0}
          >
            Save note
          </Button>
        </Group>
      </Stack>

      {sorted.length === 0 ? (
        <Text size="sm" c="dimmed">
          Nothing recorded yet.
        </Text>
      ) : (
        <Stack gap="md">
          {sorted.map((note) => {
            const mine = note.author_id === user?.employee_id;
            return (
              <div key={note.note_id}>
                <Group justify="space-between" align="flex-start" gap="xs">
                  <Text size="xs" c="dimmed">
                    <span className="identifier">{note.author_id}</span>
                    {mine && " (you)"} · {formatDateTime(note.created_at)}
                  </Text>
                  {mine && (
                    <Tooltip label="Delete this note">
                      <ActionIcon
                        variant="subtle"
                        color="red"
                        size="sm"
                        aria-label="Delete this note"
                        loading={deleting === note.note_id}
                        onClick={() => deleteNote(note)}
                      >
                        <Trash2 size={15} />
                      </ActionIcon>
                    </Tooltip>
                  )}
                </Group>
                <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
                  {note.content}
                </Text>
              </div>
            );
          })}
        </Stack>
      )}
    </Card>
  );
}
