import { test, expect, Page } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";

/**
 * PLN-CHG-001 v1.18 §10.11 C01–C04 / §11.6 — the Procurement settings tab
 * (Planning tracker PLN18-106): Administrator maintains funding sources,
 * reads rule and schedule profile Versions, sets the reminder threshold; a
 * business user is refused with the setup Forbidden state; sub-paths survive
 * reload and back/forward; a server failure is an actionable state.
 *
 * Funding sources have their own journey since the v0.14 re-port
 * (system-setup-funding-sources.spec.ts). Writes here are limited to the
 * reminder threshold (restored to its previous value in the same test). No rule Version is created here: the
 * new-version dialog is opened and cancelled; the register commands are
 * proven in kentender_core.tests.test_procurement_settings.
 */
const TAB = "/app/system-setup#procurement-settings";
const TEST_SOURCE = "Playwright test funding source";

async function openTab(page: Page, ready: string, section = "") {
	await page.goto(TAB + section, { waitUntil: "domcontentloaded" });
	await page.waitForSelector(ready, { timeout: 20_000 });
}

test.describe("System setup — Procurement settings", () => {
	test("rule and profile Versions are read-only, the method editor opens and cancels, sub-paths survive reload and back/forward", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await openTab(page, '[data-testid="kt-procset-rules"]', "/procurement-rules");

		await page.click('[data-testid="kt-procset-rule-view-MPR-OPEN-TENDER-V1"]');
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]');
		expect(page.url()).toContain("#procurement-settings/procurement-rules/MPR-OPEN-TENDER-V1");
		await expect(page.locator('[data-testid="kt-procset-rule-title"]')).toContainText("Method eligibility — Open Tender — Version 1");
		await expect(page.locator('[data-testid="kt-procset-rule-verification"]')).toHaveText("Source check needed");
		expect(await page.locator('[data-testid="kt-procset-rule-card"] input').count()).toBe(0);

		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]');
		await page.goBack();
		await page.waitForSelector('[data-testid="kt-procset-rules"]');
		await page.goForward();
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]');

		// §4.6 — a correction is a whole new Version, so "Create new version"
		// is its own screen with the current rule copied in, conditions and
		// all. Nothing is saved here: Cancel returns to the read-only detail.
		await page.click('[data-testid="kt-procset-rule-new-version"]');
		await page.waitForSelector('[data-testid="kt-procset-method-editor"]');
		expect(page.url()).toContain("#procurement-settings/procurement-rules/MPR-OPEN-TENDER-V1/new-version");
		// The seeded window starts at the first fiscal year the site seeds
		// (site_setup.PROFILE_EFFECTIVE), so a reseeded site always has its
		// rules in force on the day you open it.
		await expect(page.locator('[data-testid="kt-mve-from"]')).toHaveValue("2026-07-01");
		await expect(page.locator('[data-testid="kt-mve-method"]')).toHaveText("Open Tender");
		await expect(page.locator('[data-testid="kt-mve-id-0"]')).toHaveValue("G-VALUE");
		// Every condition is editable here and nowhere else, and one can be
		// added or removed — the dialog this replaced could do neither.
		expect(await page.locator('[data-testid^="kt-mve-condition-"]').count()).toBe(3);
		await page.click('[data-testid="kt-mve-add"]');
		expect(await page.locator('[data-testid^="kt-mve-condition-"]').count()).toBe(4);
		await page.click('[data-testid="kt-mve-remove-3"]');
		expect(await page.locator('[data-testid^="kt-mve-condition-"]').count()).toBe(3);
		// The reason for the change is required before it can be saved.
		await expect(page.locator('[data-testid="kt-mve-save"]')).toBeDisabled();
		await expect(page.locator('[data-testid="kt-mve-blocked"]')).toContainText("Say why this version replaces the earlier one");
		await page.click('[data-testid="kt-mve-cancel"]');
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]');
		expect(page.url()).toContain("#procurement-settings/procurement-rules/MPR-OPEN-TENDER-V1");

		// Back returns to the rules section; schedules are their own section.
		await page.click('[data-testid="kt-procset-rule-back"]');
		await page.waitForSelector('[data-testid="kt-procset-rules"]');
		expect(new URL(page.url()).hash).toBe("#procurement-settings/procurement-rules");
		await page.click('[data-testid="kt-procset-link-schedule-profiles"]');
		await page.waitForSelector('[data-testid="kt-procset-profiles"]');

		await page.click('[data-testid="kt-procset-profile-view-SPR-OPEN-TENDER-GOODS-V1"]');
		await page.waitForSelector('[data-testid="kt-procset-profile-table"]');
		await expect(page.locator('[data-testid="kt-procset-profile-title"]')).toHaveText("Open Tender — goods");
		// §10.9 — the milestones and the intervals between them are two tables.
		expect(await page.locator('[data-testid^="kt-procset-milestone-"]').count()).toBe(7);
		expect(await page.locator('[data-testid^="kt-procset-interval-"]').count()).toBe(6);
		await expect(page.locator('[data-testid="kt-procset-profile-notice"]')).toContainText("cannot support Plan submission");
		await expect(page.locator('[data-testid="kt-procset-profile-delivery-default"]')).toHaveText("Not set");
		expect(errors, "console errors").toEqual([]);
	});

	test("the reminder threshold saves and is restored", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await openTab(page, '[data-testid="kt-procset-reminder"]', "/reminders");
		const before = await page.inputValue('[data-testid="kt-reminder-days"]');
		const changed = String(Number(before) === 9 ? 8 : 9);
		await page.fill('[data-testid="kt-reminder-days"]', changed);
		await page.click('[data-testid="kt-reminder-save"]');
		await page.waitForSelector('[data-testid="kt-reminder-success"]');
		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-procset-reminder"]');
		await expect(page.locator('[data-testid="kt-reminder-days"]')).toHaveValue(changed);
		await page.fill('[data-testid="kt-reminder-days"]', before);
		await page.click('[data-testid="kt-reminder-save"]');
		await page.waitForSelector('[data-testid="kt-reminder-success"]');
		expect(errors, "console errors").toEqual([]);
	});

	test("a business user is refused with the setup Forbidden state, and a server failure is an actionable error state", async ({ page }) => {
		const errors = collectPageErrors(page);
		await login(page, process.env.UI_PLN_PLANNER_USER || "", process.env.UI_PLN_PLANNER_PASSWORD || "");
		await page.goto(TAB, { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-setup-forbidden"]', { timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-setup-forbidden"]')).toContainText("System setup");
		expect(await page.locator('[data-testid="kt-procset"]').count()).toBe(0);
		expect(await page.locator(".modal:visible").count()).toBe(0);

		await loginAsAdministrator(page);
		await page.route("**/api/method/kentender_core.api.procurement_settings_api.get_procurement_settings", (route) =>
			route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exc_type: "Exception" }) })
		);
		await page.goto(TAB, { waitUntil: "domcontentloaded" });
		await expect(page.getByRole("heading", { name: "Procurement settings could not be loaded" })).toBeVisible({ timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-procset-retry"]')).toBeVisible();
		expect(await page.locator(".modal:visible").count()).toBe(0);
		await page.unroute("**/api/method/kentender_core.api.procurement_settings_api.get_procurement_settings");
		await page.click('[data-testid="kt-procset-retry"]');
		await page.waitForSelector('[data-testid="kt-procset-sources"]');
		expect(errors.filter((e) => !/500|Internal Server Error/.test(e)), "console errors").toEqual([]);
	});
});
