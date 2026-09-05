import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page } from "@playwright/test";

/**
 * Shared plumbing for the PLN-CHG-001 v1.12 browser specs (decision D13).
 *
 * Fixtures come from `procurement_planning.seeds.playwright_ui_fixtures`:
 * one world on Fiscal Year **2098-2099** with two dedicated Organisation
 * Units, nine actors granted through the AUTH resolver, namespace
 * KENTENDER_PLAYWRIGHT. There is no Procuring Entity to isolate by any more
 * (AUTH-ADR-001 v1.6 §1.1), so every spec file shares the world and the
 * suite runs with **one worker**, each spec `serial`.
 *
 * Need-origin fixtures need genuine accepted Departmental Needs in this
 * world's unit. Planning may not drive Departmental Needs' commands or
 * tables (its architecture guard, D5), so this helper asks NDS's own fixture
 * module for them first (`reset_accepted_needs_for`, which purges the
 * namespace and runs the real NDS commands as this world's Author and HoD)
 * and passes the references into the Planning fixture as `need`/`needs`.
 *
 * The fixture moves the site's single-valued departmental-plan and Needs
 * intake flags onto the fixture year for the run; `restoreSite()` (called
 * from Playwright's globalTeardown and every Make gate) puts them back on
 * the §8 seed's year. The Python suite and Playwright never run together.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";
const NDS_FIXTURES = "kentender_procurement.departmental_needs.seeds.playwright_ui_fixtures";
const NAMESPACE = "KENTENDER_PLAYWRIGHT";

export const PASSWORD = "Test@123";
export const FY = "2098-2099";
export const FY_LABEL = "FY 2098/99";
export const OU_NAME = "Playwright — Procurement Planning";
export const AUTHOR = "pw.pln.author@example.test";
export const HOD = "pw.pln.hod@example.test";
export const PLANNER = "pw.pln.planner@example.test";
export const FINANCE = "pw.pln.finance@example.test";
export const ACCOUNTING_OFFICER = "pw.pln.ao@example.test";
export const STATUTORY = "pw.pln.statutory@example.test";
export const AUDITOR = "pw.pln.auditor@example.test";
export const OUTSIDER = "pw.pln.outsider@example.test";
export const NOBODY = "pw.pln.nobody@example.test";

/** §14.4's exact Need text, on this world's year. */
const NEED_CONTENT = {
	title: "National digital health infrastructure upgrade",
	description: "Procure and implement national digital health infrastructure across priority health facilities.",
	expected_operational_result: "Priority health facilities can use secure and interoperable digital health services.",
	indicative_quantity: 1,
	unit: "Each",
	required_by_date: "2099-03-31",
};

/** §14.8's two Goods sources for the combined item. */
const COMBINED_NEEDS = [
	{ ...NEED_CONTENT, title: "Clinical training laptops for digital health rollout", indicative_quantity: 200, required_by_date: "2099-04-30" },
	{ ...NEED_CONTENT, title: "Clinical deployment laptops for digital health rollout", indicative_quantity: 300, required_by_date: "2099-04-30" },
];

/** Fixtures that project an accepted Need; the helper obtains it from NDS first. */
const NEED_BACKED = new Set([
	"reset_dpp_fixture", "reset_review_fixture", "reset_accepted_fixture", "reset_workbench_fixture",
	"reset_plan_item_fixture", "reset_finance_fixture", "reset_governance_fixture", "reset_statutory_fixture",
	"reset_active_fixture", "reset_publication_failed_fixture",
]);

export function bench(command: string): string {
	try {
		return execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} ${command}`, {
			stdio: "pipe",
			timeout: 300_000,
			encoding: "utf-8",
		});
	} catch (error: any) {
		const stderr = (error?.stderr || "").toString().trim();
		const stdout = (error?.stdout || "").toString().trim();
		throw new Error(`bench ${command} failed\n${stderr || stdout || error?.message}`);
	}
}

function pyKwargs(kwargs: Record<string, unknown>): string {
	// bench execute evals --kwargs as a Python literal; JSON is one once its
	// booleans/null are Python's. Single-quoted for the shell, with any
	// apostrophe in a value closed-escaped-reopened.
	const literal = JSON.stringify(kwargs).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False").replace(/\bnull\b/g, "None");
	return ` --kwargs '${literal.replace(/'/g, "'\\''")}'`;
}

function parseResult<T>(fn: string, output: string): T {
	const line = output.trim().split("\n").pop() || "";
	try {
		return JSON.parse(line.replace(/'/g, '"').replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false").replace(/\bNone\b/g, "null")) as T;
	} catch (error) {
		throw new Error(`${fn}: could not parse bench execute output:\n${output}`);
	}
}

let worldEnsured = false;

/** Build the Planning world once per process (units, actors, flags). */
function ensureWorld(): void {
	if (worldEnsured) return;
	bench(`execute ${FIXTURES}.ensure_world`);
	worldEnsured = true;
}

/** Ask NDS for accepted Needs in this world's unit, driven by this world's Author and HoD. */
function acceptedNeeds(needs: Record<string, unknown>[]): string[] {
	const out = bench(
		`execute ${NDS_FIXTURES}.reset_accepted_needs_for${pyKwargs({
			organisation_unit_name: OU_NAME, financial_year: FY, author: AUTHOR, reviewer: HOD,
			needs, namespace: NAMESPACE,
		})}`
	);
	return parseResult<{ needs: string[] }>("reset_accepted_needs_for", out).needs;
}

/**
 * Rebuild one fixture and return its JSON result — specs read every id from
 * here (references are server-generated, never hardcoded).
 */
export function resetFixture<T = Record<string, unknown>>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const args = { ...kwargs };
	if (NEED_BACKED.has(fn)) {
		ensureWorld();
		args.need = acceptedNeeds([NEED_CONTENT])[0];
	} else if (fn === "reset_combined_item_fixture") {
		ensureWorld();
		args.needs = acceptedNeeds(COMBINED_NEEDS);
	}
	const output = bench(`execute ${FIXTURES}.${fn}${Object.keys(args).length ? pyKwargs(args) : ""}`);
	return parseResult<T>(fn, output);
}

/** Put the intake flags back on the seed year and drop NDS's fixture Needs (idempotent). */
export function restoreSite(): void {
	bench(`execute ${NDS_FIXTURES}.purge_fixture_needs${pyKwargs({ namespace: NAMESPACE })}`);
	bench(`execute ${FIXTURES}.restore_site`);
	worldEnsured = false;
}

export async function gotoPlanning(page: Page, route = ""): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/procurement-planning${route}`, { waitUntil: "domcontentloaded" });
}

export async function gotoDpp(page: Page, reference: string, route = ""): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/departmental-procurement-plan/${reference}${route}`, { waitUntil: "domcontentloaded" });
}

/** §16 — wait for the page-ready hook, never for networkidle. */
export async function expectReady(page: Page, screen: string): Promise<void> {
	const shell = page.locator('[data-testid="pln-shell"]');
	await expect(shell).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
}

/** The fixture year is the only year with intake open, so it resolves as the default. */
export async function expectFixtureYear(page: Page): Promise<void> {
	await expect(page.locator('[data-testid="pln-fy-select"]')).toHaveValue(FY);
}

/** §16.3 — zero page-specific console errors is release evidence. */
export function collectConsoleErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("console", (message) => {
		const url = message.location()?.url;
		if (url && /\/undefined$/.test(url)) return; // frappe's phantom app-switcher image
		const text = message.text();
		if (text.includes("socket.io") || text.includes("ERR_CONNECTION_REFUSED")) return;
		if (text.includes("Failed to load resource")) return;
		if (message.type() === "error") errors.push(url ? `${text} (${url})` : text);
	});
	page.on("pageerror", (error) => errors.push(String(error)));
	return errors;
}
