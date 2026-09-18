import { Alert, Group, Pagination, Text } from "@mantine/core";

export const ROWS_PER_PAGE = 50;

/**
 * Paging for a table whose rows are all already in hand.
 *
 * The count is the honest one: it is the whole filtered set, not the slice on
 * screen, so "of 812" means there really are 812.
 */
export default function Pager({
  page,
  onChange,
  totalItems,
  pageSize = ROWS_PER_PAGE,
  truncated = false,
}: {
  page: number;
  onChange: (page: number) => void;
  totalItems: number;
  pageSize?: number;
  /** Set when the fetch hit its ceiling, so the total above is a floor. */
  truncated?: boolean;
}) {
  const pages = Math.ceil(totalItems / pageSize);
  const from = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, totalItems);

  return (
    <>
      {truncated && (
        <Alert color="attention" variant="light">
          There are more records than this page will load at once, so what
          follows is the first {totalItems} of them rather than all of them.
        </Alert>
      )}
      <Group justify="space-between" wrap="wrap" gap="xs">
        <Text size="sm" c="dimmed">
          {totalItems === 0
            ? "Nothing to show"
            : `Showing ${from} to ${to} of ${totalItems}`}
        </Text>
        {pages > 1 && (
          <Pagination
            value={page}
            onChange={onChange}
            total={pages}
            size="sm"
            withEdges
          />
        )}
      </Group>
    </>
  );
}
