import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";

type Resource<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  /** For applying a server response to one row without refetching the list. */
  setData: React.Dispatch<React.SetStateAction<T | null>>;
};

/**
 * The load/loading/error/refetch cycle every page was writing out by hand.
 * Pass null as the path to skip fetching (a detail view with nothing selected).
 */
export function useResource<T>(path: string | null): Resource<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(path !== null);
  const [error, setError] = useState<string | null>(null);
  const requestCount = useRef(0)

  const load = useCallback(async () => {
    // the call claims this current value and serves as the guard
    // The guard stops a slow first request from overwriting a newer one when
    // the path changes mid-flight.
    const requestCountId = ++requestCount.current 

    if (path === null) {
      setData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const result = await api.request<T>(path)
      if (requestCountId === requestCount.current) {
        setData(result);
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
  }, [path]);

  useEffect(() => {
    load()
  }, [load]);

  return { data, loading, error, reload: load, setData };
}
