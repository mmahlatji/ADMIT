import { Box, Stack, Text, Title } from "@mantine/core";
import classes from "./AuthLayout.module.css";

export default function AuthLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className={classes.page}>
      <aside className={classes.aside}>
        <div className={classes.asideContent}>
          <div className={classes.wordmark}>ADMIT</div>
          <div className={classes.rule} />
          <Text size="sm" opacity={0.85}>
            University of Cape Town
            <br />
            Department of Computer Science
          </Text>
        </div>
        <div className={classes.asideContent}>
          <Text size="lg" fw={700} mb="xs">
            Postgraduate admissions, on one record.
          </Text>
          <Text size="sm" opacity={0.8}>
            Applications arrive in waves, from several systems, in sheets that
            do not agree with each other. ADMIT reconciles them and keeps a
            record of what changed and why.
          </Text>
        </div>
      </aside>

      <div className={classes.form}>
        <div className={classes.formInner}>
          <Stack gap="xl">
            <div className={classes.mobileBrand}>ADMIT</div>
            <Box>
              <Title order={1}>{title}</Title>
              <Text c="dimmed" size="sm" mt={4}>
                {subtitle}
              </Text>
            </Box>
            {children}
          </Stack>
        </div>
      </div>
    </div>
  );
}
