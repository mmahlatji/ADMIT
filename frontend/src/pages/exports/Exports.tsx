import { useState } from "react";
import { Alert, Button, Group, Select, Stack, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { CircleAlert, Download } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { api } from "../../lib/api";

// Adjust the range as the program needs — earliest intake year to
// current year, newest first.
const CURRENT_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: 6 }, (_, i) => String(CURRENT_YEAR - i));

export default function Exports() {
  const [year, setYear] = useState<string | null>(String(CURRENT_YEAR));
  const [exporting, setExporting] = useState(false);

  async function runExport() {
    if (!year) return;
    setExporting(true);
    try {
      const { blob, filename = `Decisions - ${year}.xlsx` } =
        await api.requestBlob(`/exports/decisions?year=${year}`);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 100);

      notifications.show({
        color: "green",
        title: `${year} export downloaded`,
        message: filename,
      });
    } catch (err) {
      notifications.show({
        color: "red",
        title: "Export failed",
        message: err instanceof Error ? err.message : "Something went wrong",
        autoClose: false,
      });
    } finally {
      setExporting(false);
    }
  }

  return (
    <Stack gap="lg">
      <PageHeader
        title="Exports"
        description="Download the decisions export for a given year."
      />

      <Alert
        color="attention"
        variant="light"
        icon={<CircleAlert size={18} />}
        title="Apply decision rules first"
      >
        Make sure any saved decision rules have been applied before exporting -
        this pulls whatever decisions are on file right now, not any rules
        queued up after the fact.
      </Alert>

      <Group align="flex-end">
        <Select
          label="Year"
          data={YEARS}
          value={year}
          onChange={setYear}
          allowDeselect={false}
          w={160}
        />
        <Button
          onClick={runExport}
          loading={exporting}
          disabled={!year}
          leftSection={<Download size={16} />}
        >
          Export {year ?? ""}
        </Button>
      </Group>

      <Text size="xs" c="dimmed">
        Recent years are stamped with today's date since that data can still
        change; older years export under just the year, since they're settled.
      </Text>
    </Stack>
  );
}
