// Every list endpoint takes skip and limit and answers with a bare array: no
// total, no next link, nothing that says whether more exist. A single request
// with a big limit therefore cannot tell a complete answer from a truncated
// one, which is how the pages here ended up capped at 500 and silently hiding
// anything past it. Asking page by page until a short page comes back is the
// only way to know the set is complete.

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";

const PAGE_SIZE = 200;

// Not an expectation, a brake. Nothing in this system should approach it, and
// hitting it is reported rather than quietly dropped, because quietly dropping
// rows is the exact fault this module exists to remove.
const MAX_ITEMS = 20000;

export type AllPages<T> = { items: T[]; truncated: boolean };

export async function fetchAllPages<T>(
  path: string,
  pageSize = PAGE_SIZE,
): Promise<AllPages<T>> {
  const items: T[] = [];
  const separator = path.includes("?") ? "&" : "?";

  for (let skip = 0; ; skip += pageSize) {
    const page = await api.request<T[]>(
      `${path}${separator}skip=${skip}&limit=${pageSize}`,
    );
    items.push(...page);

    // A page shorter than asked for is the end. A full one only means there
    // might be more, so it costs one extra empty request to be certain.
    if (page.length < pageSize) return { items, truncated: false };
    if (items.length >= MAX_ITEMS) return { items, truncated: true };
  }
}

/**
 * useResource's shape, but for a list that has to be complete. Pass null as the
 * path to skip fetching.
 */
export function useAllPages<T>(path: string | null, pageSize = PAGE_SIZE) {
  const [data, setData] = useState<T[] | null>(null);
  const [loading, setLoading] = useState(path !== null);
  const [error, setError] = useState<string | null>(null);
  const [truncated, setTruncated] = useState(false);
  const requestCount = useRef(0);

  const load = useCallback(async () => {
    // Same guard as useResource: a slow first request must not overwrite a
    // newer one when the path changes mid-flight. It matters more here, since
    // one load is several round trips rather than one.
    const requestCountId = ++requestCount.current;

    if (path === null) {
      setData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const result = await fetchAllPages<T>(path, pageSize);
      if (requestCountId === requestCount.current) {
        setData(result.items);
        setTruncated(result.truncated);
        setError(null);
      }
    } catch (e) {
      if (requestCountId === requestCount.current) {
        setError(e instanceof Error ? e.message : "Something went wrong");
      }
    } finally {
      if (requestCountId === requestCount.current) {
        setLoading(false);
      }
    }
  }, [path, pageSize]);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, reload: load, setData, truncated };
}
