import { Badge, Box, type BadgeProps } from "@mantine/core";
import type {
  ApplicationStatus,
  ImportStatus,
  MatchStatus,
  VoteDecision,
} from "../types/api";

export const STATUS_COLOUR: Record<ApplicationStatus, string> = {
  Applied: "var(--status-applied)",
  Reviewed: "var(--status-reviewed)",
  "Conditional Offer": "var(--status-offer)",
  Accepted: "var(--status-accepted)",
  "Ready to Register": "var(--status-ready)",
  Denied: "var(--status-denied)",
  Cancelled: "var(--status-cancelled)",
};

const IMPORT_COLOUR: Record<ImportStatus, string> = {
  pending: "var(--status-applied)",
  processing: "var(--status-reviewed)",
  completed: "var(--status-accepted)",
  failed: "var(--status-denied)",
};

const VOTE_COLOUR: Record<VoteDecision, string> = {
  yes: "var(--status-accepted)",
  no: "var(--status-denied)",
  abstain: "var(--status-applied)",
};

export function StatusDot({ colour }: { colour: string }) {
  return (
    <Box
      aria-hidden
      w={8}
      h={8}
      style={{ borderRadius: "50%", background: colour, flexShrink: 0 }}
    />
  );
}

/**
 * A neutral chip carrying a coloured dot, rather than a tinted chip with
 * coloured text. Keeps the label in normal ink at full contrast (amber on an
 * amber tint is unreadable) and means the colour is a second cue, never the
 * only one.
 */
function DotBadge({
  colour,
  label,
  ...props
}: { colour: string; label: string } & BadgeProps) {
  return (
    <Badge
      variant="default"
      leftSection={<StatusDot colour={colour} />}
      tt="none"
      fw={500}
      {...props}
    >
      {label}
    </Badge>
  );
}

export function ApplicationStatusBadge({
  status,
  ...props
}: { status: ApplicationStatus } & BadgeProps) {
  return <DotBadge colour={STATUS_COLOUR[status]} label={status} {...props} />;
}

export function ImportStatusBadge({
  status,
  ...props
}: { status: ImportStatus } & BadgeProps) {
  return <DotBadge colour={IMPORT_COLOUR[status]} label={status} {...props} />;
}

export function MatchStatusBadge({
  status,
  ...props
}: { status: MatchStatus } & BadgeProps) {
  return (
    <DotBadge
      colour={
        status === "pending"
          ? "var(--status-offer)"
          : "var(--status-accepted)"
      }
      label={status}
      {...props}
    />
  );
}

export function VoteBadge({
  vote,
  ...props
}: { vote: VoteDecision } & BadgeProps) {
  return <DotBadge colour={VOTE_COLOUR[vote]} label={vote} {...props} />;
}
