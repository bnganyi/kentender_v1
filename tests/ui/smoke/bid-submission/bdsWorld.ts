import { execSync } from "node:child_process";
import path from "node:path";

/**
 * BDS-CHG-001 v0.8 plan Phase 11 — the Bid Submission browser worlds, from
 * `bid_submission.seeds.playwright_ui_fixtures` (built on the Tenders test
 * Tender, with this world's own namespaced suppliers and the test password).
 */
const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.bid_submission.seeds.playwright_ui_fixtures";

export function bdsFixture<T = Record<string, string>>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const args = Object.keys(kwargs).length ? ` --kwargs '${JSON.stringify(kwargs).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False")}'` : "";
	const output = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${FIXTURES}.${fn}${args}`, { stdio: "pipe", timeout: 600_000, encoding: "utf-8" });
	return JSON.parse(output.trim().split("\n").pop() || "{}") as T;
}

export function restoreBdsWorld(): void {
	bdsFixture("restore_site");
}
