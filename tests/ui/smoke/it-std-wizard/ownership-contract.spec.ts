import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectInventoryOwnershipSurface } from "../../helpers/itWizardOwnershipContract";

const INVENTORY_ROUTE = "/desk/it-tender-configuration-system-inventory";
const SEED_CODE = "ITCFG-DASH-SEED-001";

test.describe("IT Wizard Screen Ownership contract", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			localStorage.removeItem("_page:it-tender-configuration-system-inventory");
		});
	});

	test("system inventory shows source-backed summaries without magical fixtures", async ({ page }) => {
		await page.goto(`${INVENTORY_ROUTE}?configuration_id=${SEED_CODE}`, {
			waitUntil: "domcontentloaded",
		});
		const inventory = page.frameLocator('[data-testid="it-wizard-system-inventory-iframe"]');
		await expect(inventory.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expectInventoryOwnershipSurface(inventory);
		await expect(inventory.locator("[data-itw-inv-summary-host]")).toContainText(/Head Office Users|Not configured/);
		await expect(inventory.locator("[data-itw-inv-security-host]")).toContainText(
			/SECRET|CONFIDENTIAL|Not configured|Source:/,
		);
	});
});
