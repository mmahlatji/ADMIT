import { Button, Card, Center, Group, Loader, Stack, Text, Title } from "@mantine/core";
import { PlugZap } from "lucide-react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { signOut } from "../lib/auth";
import { can } from "../lib/roles";
import NotPermitted from "../pages/NotPermitted";
import type { Role } from "../types/api";

function ProfileUnavailable({ error }: { error: string }) {
  const { reloadUser } = useAuth();
  const navigate = useNavigate();

  return (
    <Center mih="100vh" p="md">
      <Card maw={520} padding="xl">
        <Stack gap="sm">
          <PlugZap size={28} />
          <Title order={2}>Signed in, but your profile did not load</Title>
          <Text c="dimmed" size="sm">
            You are signed in and the session is valid. The API did not return
            your account, which usually means the backend is not running or is
            still starting up.
          </Text>
          <Text size="sm" className="identifier">
            {error}
          </Text>
          <Group mt="xs">
            <Button onClick={reloadUser}>Try again</Button>
            <Button
              variant="default"
              onClick={async () => {
                await signOut();
                navigate("/signin", { replace: true });
              }}
            >
              Sign out
            </Button>
          </Group>
        </Stack>
      </Card>
    </Center>
  );
}

export default function ProtectedRoute({
  children,
  allowed,
}: {
  children: React.ReactNode;
  /** Omit to allow any approved role. */
  allowed?: Role[];
}) {
  const { session, user, loading, profileError } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <Center h="100vh">
        <Stack align="center" gap="xs">
          <Loader color="uct" />
          <Text size="sm" c="dimmed">
            Checking your access
          </Text>
        </Stack>
      </Center>
    );
  }

  if (!session) {
    return <Navigate to="/signin" replace state={{ from: location }} />;
  }

  // A valid session whose profile lookup failed must NOT redirect to /signin:
  // SignIn sees the session and sends it straight back here, which loops until
  // React gives up and the page goes blank. Say what happened instead.
  if (!user) {
    return <ProfileUnavailable error={profileError ?? "No profile returned"} />;
  }

  if (user.role === null) return <Navigate to="/pending" replace />;

  // Role gate. The API enforces this too; catching it here means the person
  // gets an explanation instead of a 403 from a page that half-rendered.
  if (allowed && !can(user.role, allowed)) return <NotPermitted />;

  return <>{children}</>;
}
