import { useState } from "react";
import {
  Alert,
  Button,
  Group,
  MultiSelect,
  Select,
  Stack,
  Text,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { CircleAlert, Download } from "lucide-react";
import PageHeader from "../../components/PageHeader";
import { api } from "../../lib/api";
import { currentIntakeYear } from "../../lib/intake";
import { APPLICATION_STATUSES } from "../../types/api";

// Adjust the range as the program needs, earliest intake year to the one
// being applied for now, newest first. That top entry matters: the cycle a
// convenor is currently working is next year's intake, so the list has to
// reach it.
const CURRENT_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: 6 }, (_, i) =>
  String(currentIntakeYear() - i),
);

export default function Exports() {
  const [year, setYear] = useState<string | null>(String(CURRENT_YEAR));
  // Empty means the settled decisions the API exports by default. Naming
  // stages here is how the earlier ones in the pipeline get exported at all.
  const [stages, setStages] = useState<string[]>([]);
  const [exporting, setExporting] = useState(false);

  async function runExport() {
    if (!year) return;
    setExporting(true);
    try {
      const query = new URLSearchParams({ year });
      for (const stage of stages) query.append("status", stage);

      const { blob, filename = `Decisions - ${year}.xlsx` } =
        await api.requestBlob(`/exports/decisions?${query}`);
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
        description="Download an applicant list for a given intake year. By default that is the settled decisions, but any stage of the pipeline can be exported."
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
          label="Intake year"
          description="The year the intake starts, not the year people applied."
          data={YEARS}
          value={year}
          onChange={setYear}
          allowDeselect={false}
          w={160}
        />
        <MultiSelect
          label="Stages"
          placeholder={stages.length === 0 ? "Settled decisions" : undefined}
          description="Leave empty for accepted, denied and conditional offers"
          data={APPLICATION_STATUSES as unknown as string[]}
          value={stages}
          onChange={setStages}
          clearable
          w={360}
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
