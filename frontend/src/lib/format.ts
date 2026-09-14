const dateTime = new Intl.DateTimeFormat("en-ZA", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const dateOnly = new Intl.DateTimeFormat("en-ZA", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? "—" : dateTime.format(parsed);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? "—" : dateOnly.format(parsed);
}

export function fullName(person: {
  first_name?: string | null;
  last_name?: string | null;
}): string {
  return [person.first_name, person.last_name].filter(Boolean).join(" ") || "—";
}

/** "asr" -> "ASR", "it_transcripts" -> "IT transcripts" */
export function sourceLabel(source: string): string {
  if (source === "asr") return "ASR";
  if (source === "uct_marks") return "UCT marks";
  if (source === "it_transcripts") return "IT transcripts";
  return source.charAt(0).toUpperCase() + source.slice(1).replace(/_/g, " ");
}
