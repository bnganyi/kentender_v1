import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

test.describe("STD module retirement placeholder", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("desk route shows retirement notice", async ({ page }) => {
		await page.goto("/desk/std-module-retired");
		await expect(page.getByTestId("std-module-retired")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByText("STD Module POC — Archived")).toBeVisible();
	});

	test("governance workspace catalogue shortcut still opens retirement placeholder", async ({ page }) => {
		await page.goto("/desk/governance-%26-configuration");
		await page.getByRole("link", { name: /Official STD Library — Catalogue/i }).click();
		await expect(page).toHaveURL(/std-module-retired/);
		await expect(page.getByTestId("std-module-retired")).toBeVisible({ timeout: 30_000 });
	});
});
