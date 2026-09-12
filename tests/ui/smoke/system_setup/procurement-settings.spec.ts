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
 * Writes are limited to the "Playwright test funding source" entry (purged
 * by the gate's teardown) and the reminder threshold (restored to its
 * previous value in the same test). No rule Version is created here: the
 * new-version dialog is opened and cancelled; the register commands are
 * proven in kentender_core.tests.test_procurement_settings.
 */
const TAB = "/app/system-setup#procurement-settings";
const TEST_SOURCE = "Playwright test funding source";

async function openTab(page: Page, ready: string) {
	await page.goto(TAB, { waitUntil: "domcontentloaded" });
	await page.waitForSelector(ready, { timeout: 20_000 });
}

test.describe("System setup — Procurement settings", () => {
	test("Administrator adds, disables and re-enables a funding source; every change is re-read from the server", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await openTab(page, '[data-testid="kt-procset-sources"]');

		const row = page.locator(`[data-testid="kt-procset-source-${TEST_SOURCE}"]`);
		if ((await row.count()) === 0) {
			await page.click('[data-testid="kt-procset-source-add"]');
			await page.waitForSelector('[data-testid="kt-procset-source-editor"]');
			expect(page.url()).toContain("#procurement-settings/new-source");
			await page.fill('[data-testid="kt-fs-name"]', TEST_SOURCE);
			await page.click('[data-testid="kt-fs-save"]');
			await page.waitForSelector(`[data-testid="kt-procset-source-${TEST_SOURCE}"]`);
		}
		// Disable, then re-enable: the list re-renders from the server each time.
		await page.click(`[data-testid="kt-procset-source-edit-${TEST_SOURCE}"]`);
		await page.waitForSelector('[data-testid="kt-fs-enabled"]');
		const wasEnabled = await page.isChecked('[data-testid="kt-fs-enabled"]');
		await page.setChecked('[data-testid="kt-fs-enabled"]', !wasEnabled);
		await page.click('[data-testid="kt-fs-save"]');
		await page.waitForSelector(`[data-testid="kt-procset-source-${TEST_SOURCE}"]`);
		await expect(row).toContainText(wasEnabled ? "No" : "Yes");
		await page.click(`[data-testid="kt-procset-source-edit-${TEST_SOURCE}"]`);
		await page.waitForSelector('[data-testid="kt-fs-enabled"]');
		await page.setChecked('[data-testid="kt-fs-enabled"]', wasEnabled);
		await page.click('[data-testid="kt-fs-save"]');
		await page.waitForSelector(`[data-testid="kt-procset-source-${TEST_SOURCE}"]`);
		await expect(row).toContainText(wasEnabled ? "Yes" : "No");

		// The referenced canonical source explains it cannot be renamed.
		await page.click('[data-testid="kt-procset-source-edit-Government of Kenya"]');
		await page.waitForSelector('[data-testid="kt-fs-name"]');
		await expect(page.locator('[data-testid="kt-procset-source-editor"]')).toContainText("cannot be renamed");
		await page.click('[data-testid="kt-fs-cancel"]');
		await page.waitForSelector('[data-testid="kt-procset-sources"]');
		expect(errors, "console errors").toEqual([]);
	});

	test("rule and profile Versions are read-only, the new-version dialog opens and cancels, sub-paths survive reload and back/forward", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await openTab(page, '[data-testid="kt-procset-rules"]');

		await page.click('[data-testid="kt-procset-rule-view-MPR-OPEN-TENDER-V1"]');
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]');
		expect(page.url()).toContain("#procurement-settings/rule/MPR-OPEN-TENDER-V1");
		await expect(page.locator('[data-testid="kt-procset-rule-title"]')).toContainText("Method eligibility — Open Tender — Version 1");
		await expect(page.locator('[data-testid="kt-procset-rule-verification"]')).toHaveText("Pending");
		expect(await page.locator('[data-testid="kt-procset-rule-card"] input').count()).toBe(0);

		await page.click('[data-testid="kt-procset-rule-new-version"]');
		await page.waitForSelector('[data-testid="kt-procset-new-version"]');
		await expect(page.locator('[data-testid="kt-nv-effective-from"]')).toHaveValue("2027-07-01");
		await page.keyboard.press("Escape");
		await expect(page.locator('[data-testid="kt-procset-new-version"]')).toHaveCount(0);

		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]');
		await page.goBack();
		await page.waitForSelector('[data-testid="kt-procset-rules"]');
		await page.goForward();
		await page.waitForSelector('[data-testid="kt-procset-rule-card"]');
		await page.click('[data-testid="kt-procset-rule-back"]');
		await page.waitForSelector('[data-testid="kt-procset-profiles"]');

		await page.click('[data-testid="kt-procset-profile-view-SPR-OPEN-TENDER-GOODS-V1"]');
		await page.waitForSelector('[data-testid="kt-procset-profile-table"]');
		await expect(page.locator('[data-testid="kt-procset-profile-title"]')).toHaveText("Open Tender — goods");
		expect(await page.locator('[data-testid="kt-procset-profile-table"] tbody tr').count()).toBe(7);
		await expect(page.locator('[data-testid="kt-procset-profile-notice"]')).toContainText("cannot support Plan submission");
		await expect(page.locator('[data-testid="kt-procset-profile-delivery-default"]')).toHaveText("Not set");
		expect(errors, "console errors").toEqual([]);
	});

	test("the reminder threshold saves and is restored", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await openTab(page, '[data-testid="kt-procset-reminder"]');
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
