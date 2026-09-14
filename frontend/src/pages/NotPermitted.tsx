import { Button, Card, Stack, Text, Title } from "@mantine/core";
import { ShieldOff } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function NotPermitted() {
  const { user } = useAuth();

  return (
    <Card maw={520} mx="auto" mt="xl" padding="xl">
      <Stack align="center" gap="sm" ta="center">
        <ShieldOff size={32} />
        <Title order={2}>Not your area</Title>
        <Text c="dimmed">
          Your account is a {user?.role}, and this page is for other roles. If
          you think that is wrong, ask the convenor to check your access.
        </Text>
        <Button component={Link} to="/" mt="xs">
          Back to overview
        </Button>
      </Stack>
    </Card>
  );
}
