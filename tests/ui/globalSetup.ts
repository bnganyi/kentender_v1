import { ensureQueueHealthy } from "./helpers/benchQueue";

/**
 * Checked before a single test runs, because the failure it prevents is one
 * that reads as a product defect.
 *
 * This bench consumes no background jobs unless a worker is running, and every
 * fixture reset enqueues more. Once the queue passes Frappe's ceiling, resets
 * and teardowns start failing — and `bench execute` reports that as a
 * `NameError` naming the app, so the run looks like broken code rather than a
 * full queue. A failed teardown does not abort Playwright either, so the
 * following describe blocks run against a world nobody restored and produce
 * cascading failures that look like unrelated bugs.
 *
 * Drain first, say what was found, and refuse to start if it cannot be
 * cleared — a suite that runs anyway spends half an hour producing findings
 * that are not real.
 */
export default async function globalSetup(): Promise<void> {
	let report;
	try {
		report = ensureQueueHealthy();
	} catch (error: any) {
		// Never block a run because the guard itself could not look: say so.
		// eslint-disable-next-line no-console
		console.warn(`[queue guard] could not check the background queue: ${(error?.message || error).toString().trim()}`);
		return;
	}

	if (!report.ok) {
		throw new Error(`[queue guard] ${report.message}`);
	}
	// eslint-disable-next-line no-console
	console.log(`[queue guard] ${report.message}`);
}
