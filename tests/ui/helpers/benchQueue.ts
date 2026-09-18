import { execSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

/**
 * The background-job queue guard.
 *
 * This bench runs no RQ worker by default. Frappe enqueues a job for ordinary
 * work — `delete_doc` alone enqueues `delete_dynamic_links` — and a Playwright
 * fixture reset deletes a great many documents, so jobs pile up run after run
 * and nothing ever consumes them. Past `MAX_QUEUED_JOBS` (500, plus 50 per
 * site) Frappe's `_check_queue_size` refuses every NEW enqueue with
 * `QueueOverloaded`. From that moment any fixture reset or `restore_site` that
 * deletes a document fails.
 *
 * Three things conspired to make that invisible for a whole session:
 *
 *  1. `bench execute` hides the cause. `frappe/commands/utils.py` tries
 *     `frappe.get_attr(method)(...)` and, on ANY exception, falls back to
 *     `eval(method)` — which raises `NameError: name '<app>' is not defined`.
 *     The real error is gone and the message blames the app.
 *  2. The queue key is bench-namespaced: `rq:queue:<bench>:default`, never
 *     `rq:queue:default`. Checking the latter reports 0 while hundreds of
 *     jobs sit in the former, so "I already drained it" can be flatly wrong.
 *  3. The failure lands in an `afterAll` teardown, which does not abort the
 *     run. Later describe blocks then execute against a world that was never
 *     restored, and their cascading failures read as unrelated product bugs.
 *
 * So: never hardcode the key, never trust a masked NameError, and check
 * before the suite rather than after it.
 */

/** `MAX_QUEUED_JOBS` in `frappe/utils/background_jobs.py`. */
export const FRAPPE_MAX_QUEUED_JOBS = 500;

/**
 * Drain below this before starting. Well under Frappe's ceiling, because a
 * suite adds jobs while it runs — a check that only just passes at the start
 * still fails in the middle, which is exactly how this hid.
 */
export const SAFE_DEPTH = 50;

/**
 * Walk up until the bench identifies itself. Counting `..` segments breaks the
 * moment this file moves or is bundled from somewhere else, and a wrong bench
 * root here would report a healthy queue for a bench nobody is running.
 */
export function benchRoot(): string {
	let dir = __dirname;
	for (let i = 0; i < 12; i += 1) {
		if (fs.existsSync(path.join(dir, "sites", "common_site_config.json"))) return dir;
		const parent = path.dirname(dir);
		if (parent === dir) break;
		dir = parent;
	}
	throw new Error(`could not find a bench (no sites/common_site_config.json above ${__dirname})`);
}

/** Read the queue Redis from the bench's own config; do not assume a port. */
export function queueRedis(): { host: string; port: string } {
	const configPath = path.join(benchRoot(), "sites", "common_site_config.json");
	const raw = JSON.parse(fs.readFileSync(configPath, "utf-8"));
	const url = String(raw.redis_queue || "redis://127.0.0.1:11000");
	const match = url.match(/^redis:\/\/([^:/]+):(\d+)/);
	return { host: match ? match[1] : "127.0.0.1", port: match ? match[2] : "11000" };
}

function redis(args: string): string {
	const { host, port } = queueRedis();
	return execSync(`redis-cli -h ${host} -p ${port} ${args}`, { stdio: "pipe", encoding: "utf-8", timeout: 30_000 }).trim();
}

/**
 * Every queue, by its real key. `KEYS rq:queue:*` rather than a guessed name:
 * the bench namespaces its queues, and the un-namespaced key does not exist.
 */
export function queueDepth(): { total: number; byKey: Record<string, number> } {
	const keys = redis('keys "rq:queue:*"').split("\n").map((k) => k.trim()).filter(Boolean);
	const byKey: Record<string, number> = {};
	let total = 0;
	for (const key of keys) {
		const depth = Number(redis(`llen "${key}"`)) || 0;
		byKey[key] = depth;
		total += depth;
	}
	return { total, byKey };
}

/**
 * RQ's worker TTL is 420s and it refreshes the heartbeat well inside that;
 * anything older is a worker that died without deregistering.
 */
export const WORKER_HEARTBEAT_STALE_SECONDS = 600;

/**
 * Ask RQ who is consuming the queue, not the process table.
 *
 * `bench worker` execs `python -m frappe.utils.bench_helper frappe worker`, so
 * the live process is named `frappe worker` and a `pgrep -f "bench worker"`
 * matches only whatever shell wrapper happens to quote that text — it reports
 * a worker when there is a stale wrapper and none when a worker was started
 * plainly. RQ registers each worker in Redis with a state and a heartbeat,
 * which is both authoritative and true of a worker started any way at all.
 */
export function workerRunning(): boolean {
	try {
		const ids = redis("smembers rq:workers").split("\n").map((id) => id.trim()).filter(Boolean);
		for (const id of ids) {
			const heartbeat = Date.parse(redis(`hget "${id}" last_heartbeat`));
			if (!Number.isFinite(heartbeat)) continue;
			if ((Date.now() - heartbeat) / 1000 < WORKER_HEARTBEAT_STALE_SECONDS) return true;
		}
		return false;
	} catch {
		return false;
	}
}

/** Process everything already queued, then exit. The jobs are inert. */
export function drainQueue(timeoutMs = 300_000): void {
	execSync(`cd "${benchRoot()}" && bench worker --queue default --burst --quiet`, {
		stdio: "pipe",
		timeout: timeoutMs,
	});
}

const MASKED_NAME_ERROR = /NameError: name '([A-Za-z_][A-Za-z0-9_]*)' is not defined/;

/**
 * Turn `bench execute`'s masked failure back into something actionable.
 *
 * A `NameError` naming the app does not mean the module is missing — it means
 * the function threw and `bench execute` swallowed it. Name the real recipe,
 * and where the queue is the likely cause, say so with the actual depth.
 */
export function explainBenchFailure(dottedPath: string, stderr: string): string {
	const masked = stderr.match(MASKED_NAME_ERROR);
	if (!masked) return stderr;

	const app = dottedPath.split(".")[0];
	const lines = [
		stderr.trim(),
		"",
		`^ This NameError is NOT the real error. \`bench execute\` runs`,
		`  \`frappe.get_attr("${dottedPath}")(...)\` first and, on any exception,`,
		`  falls back to \`eval("${dottedPath}")\` — which cannot resolve \`${masked[1]}\``,
		`  and reports that instead. ${app} is fine; the function threw.`,
	];

	try {
		const { total, byKey } = queueDepth();
		if (total >= SAFE_DEPTH) {
			lines.push(
				"",
				`  LIKELY CAUSE: ${total} background jobs are queued and nothing is`,
				`  consuming them. Frappe refuses new enqueues at ${FRAPPE_MAX_QUEUED_JOBS}+`,
				`  (QueueOverloaded), so anything that deletes a document fails.`,
				...Object.entries(byKey).map(([key, depth]) => `    ${key} = ${depth}`),
				`  Fix: cd ${benchRoot()} && bench worker --queue default --burst`,
				`  Then keep one running: nohup bench worker --queue default &`,
			);
		}
	} catch {
		// The diagnosis is a courtesy; never let it replace the original error.
	}

	lines.push(
		"",
		"  To see the real error, call it directly:",
		`    cd ${benchRoot()}/sites && ../env/bin/python -c "import frappe; \\`,
		`      frappe.init(site='<site>'); frappe.connect(); \\`,
		`      from ${dottedPath.split(".").slice(0, -1).join(".")} import *; \\`,
		`      ${dottedPath.split(".").pop()}()"`,
	);
	return lines.join("\n");
}

export type QueueReport = {
	ok: boolean;
	total: number;
	byKey: Record<string, number>;
	worker: boolean;
	drained: boolean;
	message: string;
};

/**
 * Bring the queue to a state a suite can safely run in, and say what was
 * found either way — a silent guard teaches nobody that the trap exists.
 */
export function ensureQueueHealthy({ drain = true }: { drain?: boolean } = {}): QueueReport {
	let { total, byKey } = queueDepth();
	const worker = workerRunning();
	let drained = false;

	if (total >= SAFE_DEPTH && drain) {
		drainQueue();
		drained = true;
		({ total, byKey } = queueDepth());
	}

	const ok = total < SAFE_DEPTH;
	const detail = Object.entries(byKey)
		.filter(([, depth]) => depth > 0)
		.map(([key, depth]) => `${key}=${depth}`)
		.join(", ");

	if (ok) {
		return {
			ok,
			total,
			byKey,
			worker,
			drained,
			message: worker
				? `background queue ${total} job(s); a bench worker is consuming it`
				: `background queue ${total} job(s)${drained ? " after draining" : ""}; no worker running — `
					+ `start one with \`nohup bench worker --queue default &\` so it cannot build up mid-run`,
		};
	}

	return {
		ok,
		total,
		byKey,
		worker,
		drained,
		message:
			`background queue holds ${total} job(s)${drained ? " even after draining" : ""} (${detail}). `
			+ `Frappe refuses new enqueues at ${FRAPPE_MAX_QUEUED_JOBS}+, which breaks every fixture reset `
			+ `and teardown that deletes a document — and \`bench execute\` reports that as a misleading `
			+ `NameError. Run \`bench worker --queue default --burst\` in ${benchRoot()} before retrying.`,
	};
}
