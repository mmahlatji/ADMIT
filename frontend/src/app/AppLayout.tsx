import {
  ActionIcon,
  AppShell,
  Avatar,
  Badge,
  Box,
  Burger,
  Divider,
  Group,
  Menu,
  NavLink as MantineNavLink,
  ScrollArea,
  Stack,
  Text,
  Tooltip,
  useComputedColorScheme,
  useMantineColorScheme,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { LogOut, Moon, Sun } from "lucide-react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { signOut } from "../lib/auth";
import { can } from "../lib/roles";
import { navigation } from "./navigation";
import { useNavCounts } from "./useNavCounts";
import classes from "./AppLayout.module.css";

function ColorSchemeToggle() {
  const { setColorScheme } = useMantineColorScheme();
  const computed = useComputedColorScheme("light", {
    getInitialValueInEffect: true,
  });
  const next = computed === "light" ? "dark" : "light";

  return (
    <Tooltip label={`Switch to ${next} mode`}>
      <ActionIcon
        variant="subtle"
        color="gray"
        size="lg"
        onClick={() => setColorScheme(next)}
        aria-label={`Switch to ${next} mode`}
      >
        {computed === "light" ? <Moon size={18} /> : <Sun size={18} />}
      </ActionIcon>
    </Tooltip>
  );
}

export default function AppLayout() {
  const [opened, { toggle, close }] = useDisclosure(false);
  const { user } = useAuth();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const counts = useNavCounts();

  const role = user?.role ?? null;
  const initials =
    `${user?.first_name?.[0] ?? ""}${user?.last_name?.[0] ?? ""}`.toUpperCase();

  async function handleSignOut() {
    await signOut();
    navigate("/signin", { replace: true });
  }

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{
        width: 248,
        breakpoint: "sm",
        collapsed: { mobile: !opened },
      }}
      padding="lg"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group gap="sm" wrap="nowrap">
            <Burger
              opened={opened}
              onClick={toggle}
              hiddenFrom="sm"
              size="sm"
              aria-label="Toggle navigation"
            />
            <Link to="/" className={classes.brand}>
              ADMIT
            </Link>
            <Divider orientation="vertical" visibleFrom="xs" />
            <Text className={classes.institution} visibleFrom="xs">
              University of Cape Town
            </Text>
          </Group>

          <Group gap="xs" wrap="nowrap">
            <ColorSchemeToggle />
            <Menu position="bottom-end" width={220} withArrow>
              <Menu.Target>
                <Group
                  gap="xs"
                  wrap="nowrap"
                  style={{ cursor: "pointer" }}
                  role="button"
                  tabIndex={0}
                  aria-label="Account menu"
                >
                  <Box visibleFrom="sm" style={{ textAlign: "right" }}>
                    <Text size="sm" fw={700} lh={1.2}>
                      {user?.first_name} {user?.last_name}
                    </Text>
                    <Text size="xs" c="dimmed" tt="capitalize" lh={1.2}>
                      {role ?? "awaiting approval"}
                    </Text>
                  </Box>
                  <Avatar color="uct" radius="sm" size={34}>
                    {initials}
                  </Avatar>
                </Group>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Label>{user?.email}</Menu.Label>
                <Menu.Item
                  leftSection={<LogOut size={16} />}
                  onClick={handleSignOut}
                >
                  Sign out
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar className={classes.navbar} p="sm">
        <AppShell.Section grow component={ScrollArea}>
          <Stack gap="lg">
            {navigation.map((section) => {
              const items = section.items.filter((item) =>
                can(role, item.roles),
              );
              if (items.length === 0) return null;

              return (
                <div key={section.title}>
                  <Text component="div" className={classes.sectionTitle}>
                    {section.title}
                  </Text>
                  {items.map((item) => {
                    const count = item.badgeKey ? counts[item.badgeKey] : 0;
                    return (
                      <MantineNavLink
                        key={item.to}
                        component={Link}
                        to={item.to}
                        label={item.label}
                        leftSection={item.icon}
                        className={classes.navLink}
                        onClick={close}
                        active={
                          item.to === "/"
                            ? pathname === "/"
                            : pathname.startsWith(item.to)
                        }
                        rightSection={
                          count > 0 ? (
                            <Badge size="sm" color="attention" circle>
                              {count}
                            </Badge>
                          ) : undefined
                        }
                      />
                    );
                  })}
                </div>
              );
            })}
          </Stack>
        </AppShell.Section>
      </AppShell.Navbar>

      <AppShell.Main className={classes.main}>
        <a href="#main" className="skip-link">
          Skip to content
        </a>
        <Box id="main" component="main">
          <Outlet />
        </Box>
      </AppShell.Main>
    </AppShell>
  );
}
