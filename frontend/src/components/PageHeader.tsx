import { Group, Stack, Text, Title } from "@mantine/core";

export default function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <Group justify="space-between" align="flex-start" wrap="wrap" gap="sm">
      <Stack gap={2} style={{ flex: "1 1 20rem" }}>
        <Title order={1}>{title}</Title>
        {description && (
          <Text c="dimmed" size="sm" maw="65ch">
            {description}
          </Text>
        )}
      </Stack>
      {actions && <Group gap="xs">{actions}</Group>}
    </Group>
  );
}
