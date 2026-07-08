import { useCallback, useRef, useState } from "react";

export type OperationInFlightApi = {
	/** True while an async operation started via `run` is still running. */
	isRunning: boolean;
	/**
	 * Invokes `fn` at most once until it settles; concurrent calls are ignored (duplicate publish / export guard).
	 * @returns whether the operation was started (false if already running).
	 */
	run: (fn: () => Promise<void>) => Promise<boolean>;
	reset: () => void;
};

/**
 * Prevents duplicate submissions while a long operation is in flight (pack §19 — publication, export, etc.).
 */
export function useOperationInFlight(): OperationInFlightApi {
	const [isRunning, setIsRunning] = useState(false);
	const lock = useRef(false);

	const reset = useCallback(() => {
		lock.current = false;
		setIsRunning(false);
	}, []);

	const run = useCallback(async (fn: () => Promise<void>): Promise<boolean> => {
		if (lock.current) {
			return false;
		}
		lock.current = true;
		setIsRunning(true);
		try {
			await fn();
			return true;
		} finally {
			lock.current = false;
			setIsRunning(false);
		}
	}, []);

	return { isRunning, run, reset };
}
