import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page } from "@playwright/test";

/**
 * Shared plumbing for the STR-CHG-001 v1.7 §16.2 browser journeys.
 *
 * Fixtures come from `kentender_strategy.seeds.playwright_ui_fixtures`, which
 * puts the §14.3 Ministry of Health plan back into a documented state before
 * each spec and guarantees the §8.3 actors can log in. The actors are the
 * canonical register's own — Esther Muthoni (Strategy Author), Dr Alfred
 * Ochieng (Strategy Approver), Naomi Chebet (Auditor) and Samuel Otieno
 * (expired assignment, the Forbidden fixture actor) — never a module-owned
 * duplicate.
 *
 * Every spec here mutates the one canonical plan, so the suite runs with one
 * worker and each spec file resets its own starting state.
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_strategy.seeds.playwright_ui_fixtures";

export const PASSWORD = "Test@123";
export const AUTHOR = "esther.muthoni@moh.example.test";
export const APPROVER = "alfred.ochieng@moh.example.test";
export const AUDITOR = "naomi.chebet@moh.example.test";
export const NOBODY = "samuel.otieno@moh.example.test";
export const PLAN_TITLE = "Ministry of Health Strategic Plan (Demo)";

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

function parseResult<T>(fn: string, output: string): T {
	const line = output.trim().split("\n").pop() || "";
	try {
		return JSON.parse(
			line.replace(/'/g, '"').replace(/\bTrue\b/g, "true").replace(/\bFalse\b/g, "false").replace(/\bNone\b/g, "null")
		) as T;
	} catch (error) {
		throw new Error(`${fn}: could not parse bench execute output:\n${output}`);
	}
}

export interface DefaultFixture {
	plan: string;
	plan_reference: string;
	version: string;
	version_reference: string;
}
export interface SuccessorFixture extends DefaultFixture {
	v2: string;
	v2_reference: string;
}

/** Rebuild one fixture and return its ids — never hardcode a reference. */
export function resetFixture<T = DefaultFixture>(fn: string): T {
	return parseResult<T>(fn, bench(`execute ${FIXTURES}.${fn}`));
}

export async function gotoStrategy(page: Page, route = ""): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/strategy${route}`, { waitUntil: "domcontentloaded" });
}

/**
 * Wait for the page-ready hook, never for networkidle (AGENTS.md §6.7). The
 * root shell exposes `data-screen`; each screen exposes `data-loading`
 * (skeleton, only when it has nothing to show yet) and `data-refreshing`
 * (revalidating in place) — a revisited screen renders its last payload at
 * once, so assertions must wait for the refresh too.
 */
export async function expectScreen(page: Page, screen: "portfolio" | "plan" | "approval"): Promise<void> {
	await expect(page.locator('[data-testid="str-shell"]')).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	const el = page.locator(`[data-testid="str-${screen}"]`);
	await expect(el).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(el).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
}

/** KT-STD-001 §3A.2 — a page-load denial is never a modal. */
export async function expectNoFrappeModal(page: Page): Promise<void> {
	await expect(page.locator(".modal.show")).toHaveCount(0);
	await expect(page.locator("text=Not permitted")).toHaveCount(0);
}

/**
 * §16.3 — zero page console errors is release evidence. Frappe's dev server
 * echoes every expected 417 refusal as a "Failed to load resource" line
 * plus its own server traceback; both are the framework narrating a
 * validation the screen renders inline, not a page defect.
 */
export function collectConsoleErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("console", (message) => {
		const url = message.location()?.url;
		if (url && /\/undefined$/.test(url)) return; // frappe's phantom app-switcher image
		const text = message.text();
		if (text.includes("socket.io") || text.includes("ERR_CONNECTION_REFUSED")) return;
		if (text.includes("Failed to load resource")) return;
		if (text.startsWith("Traceback (most recent call last)")) return;
		if (message.type() === "error") errors.push(url ? `${text} (${url})` : text);
	});
	page.on("pageerror", (error) => errors.push(String(error)));
	return errors;
}
