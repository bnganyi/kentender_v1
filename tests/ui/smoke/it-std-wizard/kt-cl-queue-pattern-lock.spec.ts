import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	expectKtClFilterBarLayout,
	expectKtClPageSizeWired,
	expectKtClQueueTableFooter,
	expectKtClToolbarChrome,
} from "../../helpers/ktClQueueContract";

/**
 * Civic Ledger queue contract — UI-00 is the reference surface.
 * New CL queue/list pages must add a similar spec and join `make ui-civic-ledger-queue-gate`.
 */

const UI00 = "/desk/it-tender-configuration-dashboard";
const ROOT = '[data-testid="kt-cl-ui00-root"]';

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
	if (!result || !(result as { ready_packages?: string[] }).ready_packages) {
		throw new Error("UI-00 seed failed: " + JSON.stringify(result));
	}
}

test.describe.configure({ mode: "serial" });

test.describe("Civic Ledger queue pattern lock (UI-00 reference)", () => {
	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		await page.setViewportSize({ width: 1280, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await page.close();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 900 });
		await loginAsAdministrator(page);
		await page.goto(UI00);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	});

	test("toolbar chrome + page header contract", async ({ page }) => {
		await expectKtClToolbarChrome(page, {
			currentCrumb: /Tender Management/i,
			pageTitle: /Tender Configurations/i,
			ancestorLink: /Dashboard/i,
		});
	});

	test("filter bar layout contract", async ({ page }) => {
		await expect(page.getByTestId("kt-cl-ui00-table")).toBeVisible({ timeout: 15_000 });
		await expectKtClFilterBarLayout(page, {
			sampleFilterKey: "std_family",
			sameRowFilterKey: "procurement_method",
		});
	});

	test("queue table footer: Rows per page left of pager", async ({ page }) => {
		await expectKtClQueueTableFooter(page);
	});

	test("Rows per page is wired to dashboard page_size", async ({ page }) => {
		await expectKtClQueueTableFooter(page);
		await expectKtClPageSizeWired(page, {
			methodIncludes: "get_tender_configurations_dashboard",
			selectValue: "10",
		});
	});
});
