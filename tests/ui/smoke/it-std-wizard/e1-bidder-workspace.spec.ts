import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * E1 NSSF PoC — hybrid electronic bidder workspace (Administrator Desk demo).
 * Route: /desk/it-electronic-bidder-workspace/<configuration_id>
 */

const PAGE_SLUG = "it-electronic-bidder-workspace";
const CONFIG = "TCFG-E1-NSSF-ERP";

async function seedE1(page: import("@playwright/test").Page) {
	await page.waitForFunction(() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined");
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.seed_e1_nssf_for_tests",
			args: { clear: 1 },
		});
		return r.message || r;
	});
	if (!result || !(result as { configuration_id?: string }).configuration_id) {
		throw new Error("E1 seed failed: " + JSON.stringify(result));
	}
	await loginAsAdministrator(page);
}

test.describe.configure({ mode: "serial" });

test.describe("E1 electronic bidder workspace PoC", () => {
	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedE1(page);
		await page.close();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
	});

	test("workspace loads 10 sections and matrix/price counts", async ({ page }) => {
		await page.goto(`/desk/${PAGE_SLUG}/${CONFIG}`);
		await expect(page.getByTestId("kt-eb-workspace")).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-eb-config-ref")).toContainText(CONFIG);
		const navButtons = page.locator("[data-testid='kt-eb-section-nav'] button");
		await expect(navButtons).toHaveCount(10);
		await page.locator("[data-section-key='technical_compliance_matrix']").click();
		await expect(page.getByTestId("kt-eb-section-count")).toContainText("190");
		await page.locator("[data-section-key='price_schedule']").click();
		await expect(page.getByTestId("kt-eb-price-count")).toContainText("22");
	});

	test("fill → submit & seal → receipt; sealed blocks edit", async ({ page }) => {
		await page.goto(`/desk/${PAGE_SLUG}/${CONFIG}`);
		await expect(page.getByTestId("kt-eb-workspace")).toBeVisible({ timeout: 45_000 });
		await page.getByTestId("kt-eb-fill").click();
		await expect(page.getByTestId("kt-eb-status")).toBeVisible();
		await page.getByTestId("kt-eb-submit").click();
		await expect(page.getByTestId("kt-eb-receipt")).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId("kt-eb-receipt")).toContainText("EBD-");
		await expect(page.getByTestId("kt-eb-status")).toContainText("Sealed");
		await expect(page.getByTestId("kt-eb-submit")).toBeDisabled();
		await expect(page.getByTestId("kt-eb-fill")).toBeDisabled();
	});
});
