import { Alert, Card, Center, Loader, Stack, Text } from "@mantine/core";
import { CircleAlert, Inbox } from "lucide-react";

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <Center py="xl">
      <Stack align="center" gap="xs">
        <Loader color="uct" />
        <Text size="sm" c="dimmed">
          {label}
        </Text>
      </Stack>
    </Center>
  );
}

export function ErrorState({ error }: { error: string }) {
  return (
    <Alert
      color="red"
      variant="light"
      icon={<CircleAlert size={18} />}
      title="Could not load this"
    >
      {error}
    </Alert>
  );
}

/** An empty screen should say why it is empty and what fills it. */
export function EmptyState({
  title,
  hint,
  action,
}: {
  title: string;
  hint?: string;
  action?: React.ReactNode;
}) {
  return (
    <Card padding="xl">
      <Stack align="center" gap="xs" ta="center" py="lg">
        <Inbox size={28} opacity={0.5} />
        <Text fw={700}>{title}</Text>
        {hint && (
          <Text size="sm" c="dimmed" maw="45ch">
            {hint}
          </Text>
        )}
        {action}
      </Stack>
    </Card>
  );
}
