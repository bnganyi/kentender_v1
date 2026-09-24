import { test, expect, Page } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";
import { systemManager } from "./helpers";

/**
 * CFG-CHG-002 v0.14 §10.6 (tracker CFG14-5D) — the Procurement rules list and
 * a saved rule's detail in a real browser, on the canonical site. Structure
 * is the fidelity gate's job; this proves behaviour: the list's separate
 * Source check and Details columns and its filters, a direct link to a
 * saved detail that survives reload, a real rename re-read from the server
 * (restored), the rename dialog's focus and Escape, the failed-read state,
 * a second setup role, and the narrow layout.
 *
 * Writes: the Reservation rules display name, restored in the same test.
 */
const SECTION = "/app/system-setup#procurement-settings/procurement-rules";
const LIST = '[data-testid="kt-procset-rules"]';
const CARD = '[data-testid="kt-procset-rule-card"]';
const VERSION_READ = "**/api/method/kentender_core.api.procurement_settings_api.get_regulatory_reference_version";
// Bounded like a reload: the shared dev server restarts whenever any app's
// Python changes, and the first request after that is slow.
const SERVER = { timeout: 20_000 };

async function reservation(page: Page): Promise<{ version: string; name: string }> {
	const response = await page.request.get("/api/method/kentender_core.api.procurement_settings_api.get_procurement_settings");
	const set = ((await response.json()).message?.reference_sets || []).find((row: any) => row.reference_kind === "Reservation rules");
	expect(set?.version?.name, "a current Reservation rules version").toBeTruthy();
	return { version: set.version.name, name: set.display_name };
}

async function openList(page: Page): Promise<string[]> {
	const errors = collectPageErrors(page);
	await page.goto(SECTION, { waitUntil: "domcontentloaded" });
	await page.waitForSelector(LIST, SERVER);
	return errors;
}

test.describe.serial("System setup — Procurement rules", () => {
	test("the list shows Source check and Details as separate columns, and the filters narrow it in place", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openList(page);
		await expect(page.locator(`${LIST} th`)).toHaveText(["Rule", "Applies from", "Applies until", "Version", "Source check", "Details", "Action"]);
		const rows = page.locator(`${LIST} tbody tr[data-testid^="kt-procset-rule-"]`);
		expect(await rows.count()).toBeGreaterThan(1);
		// Every row states its details as one of the two server answers.
		for (const text of await page.locator('[data-testid^="kt-procset-rule-details-"]').allTextContents()) {
			expect(["Details missing", "Details complete"]).toContain(text);
		}
		await page.selectOption('[data-testid="kt-procset-rule-kind"]', "Reservation rules");
		await expect(rows).toHaveCount(1);
		await page.fill('[data-testid="kt-procset-rule-search"]', "no rule is called this");
		await expect(page.locator('[data-testid="kt-procset-rules-none-match"]')).toBeVisible();
		// Absent: a combined Ready badge, or any approval control.
		await expect(page.getByText(/^(Ready|Approve|Submit for approval)$/)).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("a saved rule opens by its link, survives reload, and keeps the section links", async ({ page }) => {
		await loginAsAdministrator(page);
		const { version, name } = await reservation(page);
		const errors = collectPageErrors(page);
		await page.goto(`${SECTION}/${version}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-procset-rule-title"]')).toHaveText(name, SERVER);
		await expect(page.locator('[data-testid="kt-procset-rule-kind"]')).toHaveText("Reservation rules");
		await expect(page.locator(`${CARD} .kt-section > h6`)).toHaveText(["Rule details", "When this rule applies", "Sources and interpretation", "Usage and history"]);
		await expect(page.locator(`${CARD} input`)).toHaveCount(0);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-procset-rule-title"]')).toHaveText(name, SERVER);
		await page.click('[data-testid="kt-procset-link-procurement-rules"]');
		await page.waitForSelector(LIST);
		expect(new URL(page.url()).hash).toBe("#procurement-settings/procurement-rules");
		expect(errors, "console errors").toEqual([]);
	});

	test("Edit rule name renames in place, is re-read from the server, and Escape closes it", async ({ page }) => {
		await loginAsAdministrator(page);
		const { version, name } = await reservation(page);
		const errors = collectPageErrors(page);
		await page.goto(`${SECTION}/${version}`, { waitUntil: "domcontentloaded" });
		await page.waitForSelector(CARD, SERVER);
		const title = page.locator('[data-testid="kt-procset-rule-title"]');
		const renamed = `${name} (Playwright)`;
		try {
			await page.locator('[data-testid="kt-procset-rule-rename"]').focus();
			await page.keyboard.press("Enter");
			await expect(page.locator('[data-testid="kt-procset-rule-rename-input"]')).toBeFocused();
			await page.keyboard.press("Escape");
			await expect(page.locator('[data-testid="kt-procset-rule-rename-dialog"]')).toHaveCount(0);

			await page.click('[data-testid="kt-procset-rule-rename"]');
			await page.fill('[data-testid="kt-procset-rule-rename-input"]', renamed);
			await page.click('[data-testid="kt-procset-rule-rename-save"]');
			await expect(page.locator('[data-testid="kt-procset-rule-rename-dialog"]')).toHaveCount(0, SERVER);
			await expect(title).toHaveText(renamed, SERVER);
			// Still on the same version's detail; nothing navigated away.
			expect(new URL(page.url()).hash).toBe(`#procurement-settings/procurement-rules/${version}`);
			await page.reload({ waitUntil: "domcontentloaded" });
			await expect(title).toHaveText(renamed, SERVER);
		} finally {
			await page.click('[data-testid="kt-procset-rule-rename"]');
			await page.fill('[data-testid="kt-procset-rule-rename-input"]', name);
			await page.click('[data-testid="kt-procset-rule-rename-save"]');
			await expect(title).toHaveText(name, SERVER);
		}
		await expect(page.locator(".modal.show")).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("a failed read of the detail is shown in place, never a Frappe pop-up", async ({ page }) => {
		await loginAsAdministrator(page);
		const { version } = await reservation(page);
		await page.route(VERSION_READ, (route) => route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "Exception" }) }));
		await page.goto(`${SECTION}/${version}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-procset-rule-error"]')).toBeVisible(SERVER);
		await page.waitForTimeout(400);
		await expect(page.locator(".modal.show")).toHaveCount(0);
		await page.unroute(VERSION_READ);
	});

	test("a System Manager reads the rules and a saved rule with the same screen", async ({ page }) => {
		const { user, password } = systemManager();
		await login(page, user, password);
		const errors = await openList(page);
		await page.locator('[data-testid^="kt-procset-rule-view-"]').first().click();
		await page.waitForSelector(CARD, SERVER);
		await expect(page.locator('[data-testid="kt-procset-rule-new-version"]')).toBeVisible();
		expect(errors, "console errors").toEqual([]);
	});

	test("at 400px the detail's groups stack and nothing scrolls sideways", async ({ page }) => {
		await loginAsAdministrator(page);
		const { version } = await reservation(page);
		await page.setViewportSize({ width: 400, height: 900 });
		await page.goto(`${SECTION}/${version}`, { waitUntil: "domcontentloaded" });
		await page.waitForSelector(CARD, SERVER);
		const lefts = await page.locator(`${CARD} .kt-section`).evaluateAll((els) => els.slice(0, 2).map((el) => el.getBoundingClientRect().left));
		expect(lefts[0]).toBe(lefts[1]);
		const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
		expect(overflow, "horizontal overflow at 400px").toBeLessThanOrEqual(1);
	});
});
