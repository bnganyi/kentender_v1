#!/usr/bin/env node
/**
 * `make ui-queue-check` — the same guard the UI suites run in globalSetup,
 * by hand, without needing Playwright.
 *
 * Reports the real queue depth (enumerating `rq:queue:*`, because the key is
 * bench-namespaced and the un-namespaced one does not exist) and exits non-zero
 * when a suite would be unsafe to start. `--fix` drains it first.
 *
 * Built through esbuild rather than a TypeScript runner so this stays free of
 * a new dependency, and into this directory rather than a temp one, because
 * the helper locates the bench by walking up from its own file.
 */
const fs = require("node:fs");
const path = require("node:path");

const source = path.join(__dirname, "benchQueue.ts");
const built = path.join(__dirname, ".queueCheck.build.cjs");

function main() {
	require("esbuild").buildSync({
		entryPoints: [source],
		bundle: true,
		platform: "node",
		format: "cjs",
		outfile: built,
		logLevel: "silent",
	});
	const queue = require(built);
	const fix = process.argv.includes("--fix");
	const report = queue.ensureQueueHealthy({ drain: fix });

	for (const [key, depth] of Object.entries(report.byKey)) {
		console.log(`  ${key} = ${depth}`);
	}
	console.log(report.ok ? `OK: ${report.message}` : `PROBLEM: ${report.message}`);
	if (!report.ok && !fix) {
		console.log("  Re-run with FIX=1 to drain: make ui-queue-check FIX=1");
	}
	if (!report.worker) {
		console.log(
			`  No bench worker is running. Jobs accumulate DURING a suite, so draining once is not enough:\n`
			+ `    cd ${queue.benchRoot()} && nohup bench worker --queue default > /tmp/rq-worker.log 2>&1 &`
		);
	}
	process.exitCode = report.ok ? 0 : 1;
}

try {
	main();
} finally {
	fs.rmSync(built, { force: true });
}
