import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page } from "@playwright/test";

/**
 * Shared plumbing for the TPR-CHG-001 v0.8 Tenders browser specs.
 *
 * Fixtures come from `tenders.seeds.playwright_ui_fixtures`, which extends
 * the Requisitions Playwright world (FY 2099-2100): the one authorised
 * handoff is built through Requisitions' real commands, then every Tenders
 * state through the Tenders commands as the fixture actors with the §13.3
 * clock injected. `restoreSite()` (globalTeardown and every Make gate)
 * removes the Tenders rows and puts the Requisitions world back.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.tenders.seeds.playwright_ui_fixtures";

export const PASSWORD = "Test@123";
export const OFFICER = "pw.tnd.officer@example.test";
export const HOPF = "pw.req.hopf@example.test";
export const AO = "pw.tnd.ao@example.test";
export const BOTH = "pw.tnd.both@example.test";
export const AUDITOR = "pw.req.auditor@example.test";
export const OUTSIDER = "pw.req.outsider@example.test";
export const NOBODY = "pw.req.nobody@example.test";

export function bench(command: string): string {
	try {
		return execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} ${command}`, { stdio: "pipe", timeout: 600_000, encoding: "utf-8" });
	} catch (error: any) {
		const stderr = (error?.stderr || "").toString().trim();
		const stdout = (error?.stdout || "").toString().trim();
		throw new Error(`bench ${command} failed\n${stderr || stdout || error?.message}`);
	}
}

function pyKwargs(kwargs: Record<string, unknown>): string {
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

export type FixtureState = { tender?: string; tender_reference?: string; handoff?: string; addendum?: string; inquiry?: string; publication?: string; record_version?: number; overall_status?: string; [k: string]: unknown };

/** Rebuild one fixture and return its JSON result — specs read every id from here. */
export function resetFixture<T = FixtureState>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const output = bench(`execute ${FIXTURES}.${fn}${Object.keys(kwargs).length ? pyKwargs(kwargs) : ""}`);
	return parseResult<T>(fn, output);
}

export function restoreSite(): void {
	bench(`execute ${FIXTURES}.restore_site`);
}

export async function gotoTenders(page: Page, route = ""): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/tenders${route}`, { waitUntil: "domcontentloaded" });
}

/** Wait for the page-ready hook, never for networkidle (AGENTS.md §6.4). */
export async function expectReady(page: Page, screen: string): Promise<void> {
	const shell = page.locator('[data-testid="tnd-shell"]');
	await expect(shell).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-pending", "false", { timeout: 30_000 });
}

/** After a command: wait for the pending gate to clear and the reload to land. */
export async function expectSettled(page: Page): Promise<void> {
	const shell = page.locator('[data-testid="tnd-shell"]');
	await expect(shell).toHaveAttribute("data-pending", "false", { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
}

/** Zero page-specific console errors is release evidence (AGENTS.md §6.7). */
export function collectConsoleErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("console", (message) => {
		const url = message.location()?.url;
		if (url && /\/undefined$/.test(url)) return; // frappe's phantom app-switcher image
		const text = message.text();
		if (text.includes("socket.io") || text.includes("ERR_CONNECTION_REFUSED")) return;
		if (text.includes("Failed to load resource")) return;
		// A server refusal the screen renders inline (TendersError → HTTP 417):
		// Frappe's request.js still prints the traceback to the console. It is
		// the expected outcome of the refusal path, not a page defect.
		if (text.includes("TendersError")) return;
		if (message.type() === "error") errors.push(url ? `${text} (${url})` : text);
	});
	page.on("pageerror", (error) => errors.push(String(error)));
	return errors;
}

/** Fail a screen's next `frappe.call` to the given method with a 500 — the forced-failure state. */
export async function failNextCall(page: Page, methodSuffix: string): Promise<void> {
	await page.route(`**/api/method/kentender_procurement.tenders.api.${methodSuffix}`, async (route) => {
		await route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "Exception", exception: "Exception: forced failure" }) });
		await page.unroute(`**/api/method/kentender_procurement.tenders.api.${methodSuffix}`);
	});
}

/** The boards' segmented and radio controls hide their <input>; click the owning label. */
export async function pick(page: Page, testid: string): Promise<void> {
	await page.locator(`label:has([data-testid="${testid}"])`).click();
}
