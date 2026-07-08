import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

test.describe("STD prod library Open → family detail navigation", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("Open action on library table navigates to std-family-detail", async ({ page }) => {
		await page.goto("/desk/std-library");
		const libraryIframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(
			libraryIframe.getByRole("heading", { name: "Standard Tender Documents" }),
		).toBeVisible({ timeout: 30_000 });

		await libraryIframe.getByRole("button", { name: "Open" }).first().click();
		await expect(page).toHaveURL(/\/desk\/std-family-detail/, { timeout: 30_000 });

		const familyIframe = page.frameLocator('[data-testid="std-prod-std-family-detail-iframe"]');
		await expect(
			familyIframe.getByText(/Family Code: KE-PPRA-IT/i),
		).toBeVisible({ timeout: 30_000 });
		await expect(page.locator("#page-std-family-detail .page-head")).toBeHidden();
	});
});
