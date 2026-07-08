import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const STD_LIBRARY_ASSET = "/assets/kentender_procurement/std_prod_impl/std_library.html";

test.describe("STD prod Official STD Library Desk wiring", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("desk route loads static library design in iframe", async ({ page }) => {
		await page.goto("/desk/std-library");
		await expect(page.locator(".page-head")).toBeHidden();
		const iframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(iframe.getByRole("heading", { name: "Standard Tender Documents" })).toBeVisible({
			timeout: 30_000,
		});
		await expect(iframe.getByText("STD FAMILIES", { exact: true })).toBeVisible();
	});

	test("procurement sidebar Official STD Library opens std-library page", async ({ page }) => {
		await page.goto("/desk/procurement-home");
		const configurationSection = page.locator(".sidebar-item-container").filter({ hasText: "Configuration" });
		await configurationSection.getByRole("button").first().click();
		await page.getByRole("link", { name: "Official STD Library", exact: true }).click();
		await expect(page).toHaveURL(/\/desk\/std-library/);
		const iframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(iframe.getByRole("heading", { name: "Standard Tender Documents" })).toBeVisible({
			timeout: 30_000,
		});
	});

	test("retired placeholder route remains available", async ({ page }) => {
		await page.goto("/desk/std-module-retired");
		await expect(page.getByTestId("std-module-retired")).toBeVisible({ timeout: 30_000 });
	});
});

test.describe("STD prod static asset direct access", () => {
	test("library asset still loads without Desk shell", async ({ page }) => {
		await page.goto(STD_LIBRARY_ASSET);
		await expect(page.getByRole("heading", { name: "Standard Tender Documents" })).toBeVisible();
	});
});
