import { execSync } from "node:child_process";
import path from "node:path";

import { expect, Page } from "@playwright/test";

/**
 * BOP-CHG-001 v0.10 plan Phase 8 — the Bid Opening browser worlds, from
 * `bid_opening.seeds.playwright_ui_fixtures` (on the Bid Submission world's
 * Tenders test Tender: Afya (Test)'s bid submitted). Each reset runs the real
 * Bid Opening commands as their actors up to a stage; `restoreBopWorld()`
 * removes the world, its people and what the browser pass wrote.
 */
const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.bid_opening.seeds.playwright_ui_fixtures";

export const PASSWORD = "Test@123";
export const AO = "pw.tnd.ao@example.test";
export const CHAIR = "pw.req.hopf@example.test";
export const MEMBER = "pw.tnd.officer@example.test";
export const INDEPENDENT = "pw.bop.independent@example.test";
export const AUDITOR = "pw.req.auditor@example.test";

export type OpeningWorld = { stage: string; tender: string; tender_reference: string; instant: string; independent: string; independent_name: string };

export function bopFixture<T = OpeningWorld>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const args = Object.keys(kwargs).length ? ` --kwargs '${JSON.stringify(kwargs).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False")}'` : "";
	const output = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${FIXTURES}.${fn}${args}`, { stdio: "pipe", timeout: 600_000, encoding: "utf-8" });
	return JSON.parse(output.trim().split("\n").pop() || "{}") as T;
}

export const openingWorld = (stage: string) => bopFixture("reset_opening_fixture", { stage });
export const restoreBopWorld = () => bopFixture("restore_site");

export async function gotoOpening(page: Page, reference: string, sub = ""): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/tenders/${reference}/opening${sub ? `/${sub}` : ""}`, { waitUntil: "domcontentloaded" });
}

/** The opening's page-ready hook: the screen is drawn and nothing is in flight. */
export async function expectScreen(page: Page, screen: string): Promise<void> {
	const root = page.locator('[data-testid="bop-root"]');
	await expect(root).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(root).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(root).toHaveAttribute("data-pending", "false", { timeout: 30_000 });
}

/** The shared next step: its kind and headline as the server answered. */
export async function expectNextStep(page: Page, kind: string, headline: string | RegExp): Promise<void> {
	const step = page.locator('[data-testid="bop-guidance"] [data-kt="next-step"]');
	await expect(step).toHaveAttribute("data-kind", kind);
	await expect(step.locator('[data-testid="kt-next-step-headline"]')).toHaveText(headline);
}

/** Zero page console errors is release evidence (AGENTS.md §6.7). */
export function collectConsoleErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("console", (message) => {
		const url = message.location()?.url;
		if (url && /\/undefined$/.test(url)) return;
		const text = message.text();
		if (text.includes("socket.io") || text.includes("ERR_CONNECTION_REFUSED") || text.includes("Failed to load resource")) return;
		if (message.type() === "error") errors.push(url ? `${text} (${url})` : text);
	});
	page.on("pageerror", (error) => errors.push(String(error)));
	return errors;
}
