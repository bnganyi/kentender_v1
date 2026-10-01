import { execSync } from "node:child_process";
import path from "node:path";

import { Browser, BrowserContext, expect, Page } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * AWD-CHG-001 v0.4 plan OD-B — the Award browser worlds, from
 * `award.seeds.playwright_ui_fixtures`: each stage is built from the synthetic
 * upstream sources by the real Award commands as the real personas, in about
 * a second (no tender, bid, opening or evaluation). `restoreAwardWorld()`
 * removes every browser-world row and clears the test clock.
 */
const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";
const FIXTURES = "kentender_procurement.award.seeds.playwright_ui_fixtures";

export const PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";
export const CHARLES = "charles.mutiso@moh.example.test";
export const AMINA = "amina.hassan@moh.example.test";
export const MARY = "mary.wanjiku@afyadigital.example";
export const DAVID = "david.ouma@afyadigital.example";
export const DANIEL = "daniel.otieno@moh.example.test";
export const NAOMI = "naomi.chebet@moh.example.test";
export const EVIDENCE = "docs/mvp-1-r1/16_award/evidence/v0_4";

export type AwardWorld = { stage: string; award: string; tender_reference: string; instant: string; notice: string; notices: Record<string, string>; requests: string[] };

export function awdFixture<T = AwardWorld>(fn: string, kwargs: Record<string, unknown> = {}): T {
	const args = Object.keys(kwargs).length ? ` --kwargs '${JSON.stringify(kwargs).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False")}'` : "";
	const output = execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ${FIXTURES}.${fn}${args}`, { stdio: "pipe", timeout: 300_000, encoding: "utf-8" });
	return JSON.parse(output.trim().split("\n").pop() || "{}") as T;
}

export const awardWorld = (stage: string) => awdFixture("reset_award_fixture", { stage });
export const restoreAwardWorld = () => awdFixture("restore_site");

let current: BrowserContext | null = null;

/** One browser session per person (a fresh context each time). */
export async function as(browser: Browser, user: string, width = 1440, height = 1024): Promise<Page> {
	if (current) await current.close();
	const context = await browser.newContext({ baseURL: process.env.UI_BASE_URL || "http://127.0.0.1:8000" });
	current = context;
	const page = await context.newPage();
	await page.setViewportSize({ width, height });
	await login(page, user, PASSWORD);
	return page;
}

export async function closeSession(): Promise<void> {
	if (current) await current.close();
	current = null;
}

/** The Award page-ready hook: the named screen is drawn and nothing is in flight. */
export async function expectScreen(page: Page, screen: string): Promise<void> {
	const root = page.locator('[data-testid="awd-root"]');
	await expect(root).toHaveAttribute("data-screen", screen, { timeout: 30_000 });
	await expect(root).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(root).toHaveAttribute("data-pending", "false", { timeout: 30_000 });
}

/** The shared next step: its kind and headline, as the server answered. */
export async function expectNextStep(page: Page, kind: string, headline: string | RegExp): Promise<void> {
	const step = page.locator('[data-testid="awd-root"] [data-testid="awd-guidance"] [data-kt="next-step"]');
	await expect(step).toHaveAttribute("data-kind", kind, { timeout: 30_000 });
	await expect(step.locator('[data-testid="kt-next-step-headline"]')).toHaveText(headline);
}

/** The journey markers, in order, as "Done", "Current", "Blocked", "Not started". */
export async function expectJourney(page: Page, markers: string[]): Promise<void> {
	const stages = page.locator('[data-testid="awd-guidance"] ol.kt-journey li .kt-journey-state');
	await expect(stages).toHaveCount(5);
	for (let i = 0; i < markers.length; i += 1) await expect(stages.nth(i)).toContainText(markers[i]);
}

/** Desk home → Procurement → Tender Management → Awards (the workspace). */
export async function openAwardsFromMenu(page: Page): Promise<void> {
	await page.goto("/app", { waitUntil: "domcontentloaded" });
	await page.getByText("Procurement", { exact: true }).first().click();
	const awards = page.locator('a[href="/desk/award"]:visible, a[href="/app/award"]:visible');
	if (!(await awards.count())) await page.locator("text=Tender Management").first().click();
	await awards.first().click();
	await expectScreen(page, /^workspace/ as unknown as string);
}

export function collectConsoleErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on("console", (msg) => {
		if (msg.type() !== "error") return;
		const text = msg.text();
		const url = (msg.location() && msg.location().url) || "";
		if (/socket\.io|\/socket|undefined$|favicon/.test(url) || /socket\.io/.test(text)) return;
		errors.push(text);
	});
	page.on("pageerror", (e) => errors.push(e.message));
	return errors;
}
