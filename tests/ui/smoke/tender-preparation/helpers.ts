import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page } from "@playwright/test";

/**
 * Shared plumbing for the TPR-CHG-001 v0.6 browser specs.
 *
 * Fixtures come from `tender_preparation.seeds.playwright_ui_fixtures`, which
 * extends Procurement Requisitions' own Playwright world (FY 2099-2100) with
 * six Tender-facing actors. Each spec rebuilds its own opening state through
 * the real commands and reads every id from the fixture result. The Python
 * suite and Playwright never run together on the site.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.tender_preparation.seeds.playwright_ui_fixtures";

export const PASSWORD = "Test@123";
export const OFFICER = "pw.tpr.officer@example.test";
export const HOPF = "pw.tpr.hopf@example.test";
export const BOTH = "pw.tpr.both@example.test";
export const AUDITOR = "pw.tpr.auditor@example.test";
export const OUTSIDER = "pw.tpr.outsider@example.test";
export const NOBODY = "pw.tpr.nobody@example.test";

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
	} catch {
		throw new Error(`${fn}: could not parse bench execute output:\n${output}`);
	}
}

export function resetFixture<T = Record<string, any>>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const output = bench(`execute ${FIXTURES}.${fn}${Object.keys(kwargs).length ? pyKwargs(kwargs) : ""}`);
	return parseResult<T>(fn, output);
}

export function restoreSite(): void {
	bench(`execute ${FIXTURES}.restore_site`);
}

export async function gotoTenderPreparation(page: Page, route = ""): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/tender-preparation${route}`, { waitUntil: "domcontentloaded" });
}

/** Wait for the page-ready hook, never for networkidle (AGENTS.md §6.4). */
export async function expectReady(page: Page, screen: string): Promise<void> {
	const shell = page.locator('[data-testid="tpr-shell"]');
	await expect(shell).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(shell).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
}

/** Zero page-specific console errors is release evidence (AGENTS.md §6.7). */
export function collectConsoleErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("console", (message) => {
		const url = message.location()?.url;
		if (url && /\/undefined$/.test(url)) return;
		const text = message.text();
		if (text.includes("socket.io") || text.includes("ERR_CONNECTION_REFUSED")) return;
		if (text.includes("Failed to load resource")) return;
		if (message.type() === "error") errors.push(url ? `${text} (${url})` : text);
	});
	page.on("pageerror", (error) => errors.push(String(error)));
	return errors;
}

/** AGENTS.md §6.10 — no default Frappe "Message" dialog may appear. */
export async function expectNoMessageDialog(page: Page): Promise<void> {
	await expect(page.locator(".modal-dialog .modal-title", { hasText: /^Message$/ })).toHaveCount(0);
}
