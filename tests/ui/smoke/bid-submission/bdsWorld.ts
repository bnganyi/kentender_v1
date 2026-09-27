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

/**
 * The supplier Account worlds (slices 11.3–11.4), from
 * `supplier_accounts.seeds.playwright_ui_fixtures`: this world's own people on
 * the test password, one board state per reset.
 */
const ACCOUNT_FIXTURES = "kentender_suppliers.supplier_accounts.seeds.playwright_ui_fixtures";
const MAILBOX = "kentender_procurement.bid_submission.test_services.mailbox";

function benchExecute<T>(method: string, kwargs: Record<string, unknown> = {}): T {
	const args = Object.keys(kwargs).length ? ` --kwargs '${JSON.stringify(kwargs).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False")}'` : "";
	const output = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${method}${args}`, { stdio: "pipe", timeout: 600_000, encoding: "utf-8" });
	return JSON.parse(output.trim().split("\n").pop() || "null") as T;
}

export function accountFixture<T = Record<string, string>>(fn: string, kwargs: Record<string, unknown> = {}): T {
	return benchExecute<T>(`${ACCOUNT_FIXTURES}.${fn}`, kwargs);
}

export function restoreAccountWorld(): void {
	accountFixture("restore_site");
}

/** The newest message the Test Mailbox kept for `to` (a test environment only). */
export function latestTestMessage(to: string): { to: string; subject: string; link: string } | null {
	return benchExecute(`${MAILBOX}.latest`, { to });
}

export function clearTestMessages(to: string): void {
	benchExecute(`${MAILBOX}.clear`, { to });
}
