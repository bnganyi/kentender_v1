import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const SEED = "ITCFG-DASH-SEED-003";
const ROUTE = "it-tender-configuration-price-schedule";

test.describe("IT Wizard Price Schedule Desk wiring", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("hydrates seeded lines and binds native drawer without Not configured source chrome", async ({
		page,
	}) => {
		await page.evaluate((route) => {
			localStorage.removeItem(`_page:${route}`);
		}, ROUTE);
		await page.goto(`/desk/${ROUTE}?configuration_id=${SEED}`, {
			waitUntil: "domcontentloaded",
		});
		const frame = page.frameLocator('[data-testid="it-wizard-price-schedule-iframe"]');
		await expect(frame.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 45_000,
		});
		await expect(frame.locator("[data-itw-table-body]")).toContainText("Core Platform Supply");
		await expect(frame.locator("[data-itw-price-drawer]")).toHaveAttribute(
			"data-itw-price-drawer-open",
			"0",
		);
		await expect(frame.locator("body")).not.toContainText("Source: Not configured");

		await frame.locator('[data-itw-code="PL-SUPPLY-001"] [data-itw-edit]').click();
		await expect(frame.locator("[data-itw-price-drawer]")).toHaveAttribute(
			"data-itw-price-drawer-open",
			"1",
		);
		await expect(frame.locator('[data-itw-price-field="title"]')).toHaveValue(
			"Core Platform Supply",
		);
		await expect(frame.locator('[data-itw-price-field="quantity"]')).toHaveValue("1");
		await expect(frame.locator('[data-itw-price-field="unit_of_measure"]')).toHaveValue("LOT");
		await expect(frame.locator('[data-itw-price-source="inventory_item_code"]')).toContainText(
			"System Inventory",
		);
		await expect(frame.locator('[data-itw-price-owned="1"]').first()).toBeVisible();
		await expect(frame.locator("[data-itw-price-drawer]")).not.toContainText(
			"Source: Not configured",
		);

		await frame.locator("[data-itw-price-drawer-cancel]").click();
		await expect(frame.locator("[data-itw-price-drawer]")).toHaveAttribute(
			"data-itw-price-drawer-open",
			"0",
		);
	});
});
