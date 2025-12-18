import { useState, useEffect, useRef } from 'react';

interface UsePollingOptions<T> {
  intervalMs: number;
  enabled: boolean;
  onData?: (data: T) => void;
  onError?: (err: unknown) => void;
}

/**
 * Custom hook for polling data at regular intervals.
 * Prevents race conditions by ensuring only one request is in flight at a time.
 */
export function usePolling<T>(
  fn: () => Promise<T>,
  opts: UsePollingOptions<T>
): { data?: T; error?: unknown; loading: boolean } {
  const [data, setData] = useState<T | undefined>();
  const [error, setError] = useState<unknown>();
  const [loading, setLoading] = useState(false);
  const inFlightRef = useRef(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const execute = async () => {
    // Prevent overlapping requests
    if (inFlightRef.current) {
      return;
    }

    inFlightRef.current = true;
    setLoading(true);
    setError(undefined);

    try {
      const result = await fn();
      setData(result);
      setError(undefined);
      if (opts.onData) {
        opts.onData(result);
      }
    } catch (err) {
      setError(err);
      if (opts.onError) {
        opts.onError(err);
      }
    } finally {
      setLoading(false);
      inFlightRef.current = false;
    }
  };

  useEffect(() => {
    if (!opts.enabled) {
      return;
    }

    // Execute immediately on mount
    execute();

    // Set up interval
    intervalRef.current = setInterval(() => {
      execute();
    }, opts.intervalMs);

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opts.enabled, opts.intervalMs]);

  return { data, error, loading };
}
