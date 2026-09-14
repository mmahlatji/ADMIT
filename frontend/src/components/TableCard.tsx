import { Card, Table } from "@mantine/core";

/**
 * The house wrapper for every data table.
 *
 * A bare <Table> inside a Card clips: the card hides its overflow and the page
 * body does not scroll sideways, so on a narrow screen the right-hand columns
 * become unreachable rather than merely awkward. ScrollContainer gives the
 * table its own axis and keeps the sticky header working.
 */
export default function TableCard({
  minWidth = 720,
  children,
}: {
  /** Width below which the table starts scrolling instead of squashing. */
  minWidth?: number | string;
  children: React.ReactNode;
}) {
  return (
    <Card padding={0}>
      <Table.ScrollContainer minWidth={minWidth} type="native">
        {children}
      </Table.ScrollContainer>
    </Card>
  );
}
