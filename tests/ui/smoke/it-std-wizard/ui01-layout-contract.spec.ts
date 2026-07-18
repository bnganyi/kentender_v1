import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	expectUi01NineCards,
	expectUi01StructuralLayout,
} from "../../helpers/ktClUi01LayoutContract";

/**
 * Structural gate for UI-01 — must pass before claiming Civic Ledger home UX done.
 * Catches the regressions that already shipped twice (crumb, CTA wrap, handoff icon).
 */

const PAGE_SLUG = "it-tender-configuration-overview";
const ROOT = '[data-testid="kt-cl-ui01-root"]';
const NA_CONFIG = "TCFG-SEED-TCFG-NA";

const CFG_TITLES = [
	"Tender Profile",
	"Tender Data Sheet",
	"IT Requirements",
	"Implementation Schedule",
	"System Inventory & Bidder Background",
	"Price Schedule",
	"Evaluation Setup",
	"Forms & Evidence",
	"Contract Values",
];

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
		throw new Error("UI-01 seed failed: " + JSON.stringify(result));
	}
}

test.describe.configure({ mode: "serial" });

test.describe("UI-01 structural layout contract", () => {
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
	});

	test("pins toolbar, next-action row, handoff header, 8-cell strip, nine cards", async ({
		page,
	}) => {
		await page.goto(`/desk/${PAGE_SLUG}/${encodeURIComponent(NA_CONFIG)}`);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expectUi01StructuralLayout(page);
		await expectUi01NineCards(page, CFG_TITLES);
		await expect(page.getByTestId("kt-cl-config-context-std_document")).toContainText(
			/IT Standard Tender Document/i
		);
	});
});
