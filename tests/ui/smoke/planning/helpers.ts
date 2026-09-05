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
 * The fixture moves the site's single-valued departmental-plan and Needs
 * intake flags onto the fixture year for the run; `restoreSite()` (called
 * from Playwright's globalTeardown and every Make gate) puts them back on
 * the §8 seed's year. The Python suite and Playwright never run together.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.procurement_planning.seeds.playwright_ui_fixtures";

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

/**
 * Rebuild one fixture and return its JSON result — specs read every id from
 * here (references are server-generated, never hardcoded).
 */
export function resetFixture<T = Record<string, unknown>>(fn: string, kwargs?: Record<string, unknown>): T {
	const args = kwargs ? ` --kwargs "${JSON.stringify(kwargs).replace(/"/g, "'").replace(/true/g, "True").replace(/false/g, "False")}"` : "";
	const output = bench(`execute ${FIXTURES}.${fn}${args}`).trim();
	const line = output.split("\n").pop() || "";
	try {
		// bench prints a Python dict repr; single quotes → JSON
		return JSON.parse(line.replace(/'/g, '"').replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false").replace(/\bNone\b/g, "null")) as T;
	} catch (error) {
		throw new Error(`resetFixture(${fn}): could not parse bench execute output:\n${output}`);
	}
}

/** Put the intake flags back on the seed year (idempotent). */
export function restoreSite(): void {
	bench(`execute ${FIXTURES}.restore_site`);
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
