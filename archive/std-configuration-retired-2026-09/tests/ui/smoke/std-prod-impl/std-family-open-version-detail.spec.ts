import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

test.describe("STD prod family version actions → version detail navigation", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("Open Version action navigates to std-version-detail", async ({ page }) => {
		await page.goto("/desk/std-family-detail");
		const familyIframe = page.frameLocator('[data-testid="std-prod-std-family-detail-iframe"]');
		await expect(
			familyIframe.getByText(/Family Code: KE-PPRA-IT/i),
		).toBeVisible({ timeout: 30_000 });

		await familyIframe.locator('button[title="Open Version"]').click();
		await expect(page).toHaveURL(/\/desk\/std-version-detail/, { timeout: 30_000 });

		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.getByText("ACTIVE VERSION — READ ONLY")).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator("#page-std-version-detail .page-head")).toBeHidden();
	});

	test("edit and visibility row actions also navigate to std-version-detail", async ({
		page,
	}) => {
		await page.goto("/desk/std-family-detail");
		const familyIframe = page.frameLocator('[data-testid="std-prod-std-family-detail-iframe"]');

		await familyIframe.locator("tbody tr").nth(1).locator("button").first().click();
		await expect(page).toHaveURL(/\/desk\/std-version-detail/, { timeout: 30_000 });

		await page.goto("/desk/std-family-detail");
		await familyIframe.locator("tbody tr").nth(2).locator("button").first().click();
		await expect(page).toHaveURL(/\/desk\/std-version-detail/, { timeout: 30_000 });
	});
});
