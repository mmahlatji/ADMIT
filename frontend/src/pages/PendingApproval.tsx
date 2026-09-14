import {
  Anchor,
  Button,
  Card,
  Center,
  Group,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import { Hourglass } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { signOut } from "../lib/auth";

/**
 * Where an approved-but-unassigned account lands. The old build sent these
 * people back to /signup, which reads as "your account did not save" when in
 * fact it saved fine and is waiting on a convenor.
 */
export default function PendingApproval() {
  const { user } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate("/signin", { replace: true });
  }

  return (
    <Center mih="100vh" p="md">
      <Card maw={480} padding="xl">
        <Stack gap="sm">
          <Hourglass size={28} />
          <Title order={2}>Waiting on approval</Title>
          <Text c="dimmed">
            Your account was created and is on file as{" "}
            <Text span fw={700}>
              {user?.email}
            </Text>
            . A convenor still has to assign you a role before you can see the
            intake. Nothing more is needed from you.
          </Text>
          <Group mt="xs">
            <Button variant="default" onClick={() => window.location.reload()}>
              Check again
            </Button>
            <Anchor component="button" type="button" onClick={handleSignOut}>
              Sign out
            </Anchor>
          </Group>
        </Stack>
      </Card>
    </Center>
  );
}
