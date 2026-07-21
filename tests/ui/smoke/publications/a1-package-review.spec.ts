import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * PUB-A1 Electronic Tender Package Review.
 * Route: /desk/it-tender-package-review/<configuration_id>
 */

const PAGE_SLUG = "it-tender-package-review";
const ROOT = '[data-testid="kt-cl-pub-a1-root"]';
const CONFIG = "TCFG-SEED-TCFG-RP";

async function seedUi00(page: import("@playwright/test").Page) {
	await page.waitForFunction(() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined");
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.seed_ui00_dashboard_for_tests",
			args: { clear: 1 },
		});
		return r.message || r;
	});
	if (!result || !(result as { configurations?: string[] }).configurations) {
		throw new Error("PUB-A1 seed failed: " + JSON.stringify(result));
	}
	await loginAsAdministrator(page);
}

async function prepareForPackageReview(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.evaluate(async (id) => {
		// @ts-expect-error frappe on desk
		await frappe.call({
			method: "kentender_procurement.tender_configurations.generate_tender_configuration_document_preview",
			args: { configuration_id: id },
		});
	}, configId);
}

test.describe.configure({ mode: "serial" });

test.describe("PUB-A1 Electronic Tender Package Review", () => {
	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await page.close();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
	});

	test("sections visible; confirm present; no Send wording", async ({ page }) => {
		await seedUi00(page);
		await prepareForPackageReview(page);
		await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(CONFIG)}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 15_000 });

		await expect(page.getByTestId("kt-cl-pub-a1-context-strip")).toBeVisible();
		const stripTitle = (await page.getByTestId("kt-cl-pub-a1-strip-title").innerText()).trim();
		expect(stripTitle.length).toBeGreaterThan("Tender Title".length);
		await expect(page.getByTestId("kt-cl-pub-a1-layout")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a1-readiness")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a1-bidder")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a1-document")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a1-issues")).toBeVisible();
		await expect(page.getByTestId("kt-cl-pub-a1-footer")).toBeVisible();
		// Fresh seed shows Confirm; leftover confirmed package shows Continue to Setup.
		const confirmOrContinue = page
			.getByTestId("kt-cl-pub-a1-confirm")
			.or(page.getByTestId("kt-cl-pub-a1-continue-setup"))
			.or(page.getByTestId("kt-cl-pub-a1-continue-setup-footer"));
		await expect(confirmOrContinue.first()).toBeVisible();
		await expect(confirmOrContinue.first()).toHaveText(
			/Confirm Tender Package|Continue to Publication Setup/i
		);

		const body = await page.locator(ROOT).innerText();
		expect(body).not.toMatch(/Send to Publication Workflow/i);
	});
});
