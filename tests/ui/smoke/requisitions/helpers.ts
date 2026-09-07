import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page } from "@playwright/test";

/**
 * Shared plumbing for the REQ-CHG-001 v1.6 browser specs (tracker REQ-402).
 *
 * Fixtures come from `procurement_requisitions.seeds.playwright_ui_fixtures`:
 * a self-contained world on Fiscal Year **2099-2100**, distinct from both the
 * canonical MOH seed (2027-2028) and Procurement Planning's own Playwright
 * world (2098-2099). Six Requisitions-facing actors (author/hod/hopf/
 * auditor/outsider/nobody) plus four Planning-plumbing actors that build the
 * one eligible Plan Item this world needs — never logged into by a spec.
 *
 * The fixture moves the site's single-valued DPP submission flag onto its
 * own FY for a run; `restoreSite()` (called from Playwright's globalTeardown
 * and every Make gate) puts it back. The Python suite and Playwright never
 * run together (this build's own "wipe-after-authorise" lesson — see the
 * seed module's own docstring).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_requisitions.seeds.playwright_ui_fixtures";

export const PASSWORD = "Test@123";
export const FY = "2099-2100";
export const OU_NAME = "Playwright — Procurement Requisitions";
export const AUTHOR = "pw.req.author@example.test";
export const HOD = "pw.req.hod@example.test";
export const HOPF = "pw.req.hopf@example.test";
export const AUDITOR = "pw.req.auditor@example.test";
export const OUTSIDER = "pw.req.outsider@example.test";
export const NOBODY = "pw.req.nobody@example.test";

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

/**
 * Rebuild one fixture and return its JSON result — specs read every id from
 * here (references are server-generated, never hardcoded).
 */
export function resetFixture<T = Record<string, unknown>>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const output = bench(`execute ${FIXTURES}.${fn}${Object.keys(kwargs).length ? pyKwargs(kwargs) : ""}`);
	return parseResult<T>(fn, output);
}

/** Put the DPP intake flag back on the previously-open year (idempotent). */
export function restoreSite(): void {
	bench(`execute ${FIXTURES}.restore_site`);
}

export async function gotoRequisitions(page: Page, route = ""): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/procurement-requisitions${route}`, { waitUntil: "domcontentloaded" });
}

/** Wait for the page-ready hook, never for networkidle (AGENTS.md §6.4). */
export async function expectReady(page: Page, screen: string): Promise<void> {
	const shell = page.locator('[data-testid="req-shell"]');
	await expect(shell).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
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
		if (message.type() === "error") errors.push(url ? `${text} (${url})` : text);
	});
	page.on("pageerror", (error) => errors.push(String(error)));
	return errors;
}
