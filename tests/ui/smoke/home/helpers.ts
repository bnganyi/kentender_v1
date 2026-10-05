import { execSync } from "node:child_process";
import * as path from "node:path";

import { expect, Page } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectConsoleErrors } from "../planning/helpers";

/**
 * HOME-CHG-001 v0.6 plan Phase 5 — shared by the Home specs.
 *
 * Every expectation in these specs was read from the SEED-002 world as it was seeded on 5 Oct 2026, at the
 * world's own clock (18 June 2027, 10:00 EAT). The specs are read-only: opening Home, paging it and following a
 * row's route write nothing, so no world is reset. If the seed world changes, re-read the rows (the Home read for
 * each persona) before changing an expectation, never the other way round.
 * Run on the test site: scripts/test-site.sh run npx playwright test tests/ui/smoke/home --workers=1
 */
export const PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";
export const CHARLES = "charles.mutiso@moh.example.test"; // Head of Procurement Function
export const AMINA = "amina.hassan@moh.example.test"; // Accounting Officer
export const BRIAN = "brian.wafula@moh.example.test"; // Procurement Officer
export const PETER = "peter.kimani@moh.example.test"; // Head of User Department (three units)
export const NAOMI = "naomi.chebet@moh.example.test"; // Auditor
export const DANIEL = "daniel.otieno@moh.example.test"; // Technical Operator
export const JOSPHAT = "josphat.mwangi@moh.example.test"; // Budget Officer: nothing in his queues at this instant

/**
 * Put the site's test clock on the seed world's as-at instant (SEED-002 §A1). Other modules' browser fixtures clear
 * the clock when they finish, and Home reads it for every date it shows, so each Home spec sets it before it runs.
 * A site that is not a test environment ignores the call and reads the real clock.
 */
export function putWorldClock(): void {
	const bench = path.resolve(__dirname, "../../../../../..");
	execSync(`cd "${bench}" && bench --site ${process.env.UI_SITE || "kentender.midas.com"} execute kentender_core.seeds.canonical.set_as_at`, {
		stdio: "pipe",
		timeout: 120_000,
	});
}

export const root = (page: Page) => page.locator('[data-testid="kt-home-root"]');
export const region = (page: Page, id: string) => page.locator(`#${id}`);
export const rows = (page: Page, id: string) => page.locator(`#${id} [data-testid="kt-home-row"]`);

/** The visible text of a locator with whitespace collapsed (rows lay their text out in separate inline elements). */
export async function flat(locator: ReturnType<Page["locator"]>): Promise<string> {
	return ((await locator.innerText()) || "").replace(/\s+/g, " ").trim();
}

export async function waitForHome(page: Page): Promise<void> {
	await expect(root(page)).toBeVisible({ timeout: 60_000 });
	await expect(page.locator('[data-testid="kt-home-loading"]')).toHaveCount(0, { timeout: 60_000 });
}

/** Sign in, open a neutral module page, then reach Home the way a person does: the sidebar's Home item. */
export async function openHomeFromMenu(page: Page, user: string): Promise<string[]> {
	const errors = collectConsoleErrors(page);
	await login(page, user, PASSWORD);
	await page.goto("/desk/departmental-needs", { waitUntil: "domcontentloaded" });
	const item = page.locator(".standard-sidebar-item").filter({ hasText: /^\s*Home\s*$/ }).first();
	await expect(item).toBeVisible({ timeout: 60_000 });
	await expect(item).not.toContainText("Planned"); // Home is built: no Planned badge
	await item.click();
	await waitForHome(page);
	await expect(page).toHaveURL(/\/desk\/home$/);
	return errors;
}
