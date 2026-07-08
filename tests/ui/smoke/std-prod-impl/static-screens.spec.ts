import { test, expect } from "@playwright/test";

const ASSET_BASE = "/assets/kentender_procurement/std_prod_impl";

test.describe("STD prod static screens — preview index", () => {
	test("index lists all three screen links", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/index.html`);
		await expect(page.getByRole("heading", { name: /STD Engine Production UI/i })).toBeVisible();
		await expect(page.getByRole("link", { name: "STD Library" })).toBeVisible();
		await expect(page.getByRole("link", { name: "STD Family Detail" })).toBeVisible();
		await expect(page.getByRole("link", { name: "STD Version Detail" })).toBeVisible();
	});
});

test.describe("STD prod static screens — library", () => {
	test("library screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_library.html`);
		await expect(page).toHaveTitle(/STD Library \| KenTender STD Engine/);
		await expect(page.getByRole("heading", { name: "Standard Tender Documents" })).toBeVisible();
		await expect(page.getByText("STD FAMILIES", { exact: true })).toBeVisible();
		await expect(page.getByRole("columnheader", { name: "Family Code" })).toBeVisible();
		await page.getByRole("button", { name: "filter_list Filters" }).click();
		await expect(page.getByRole("heading", { name: "Filters" })).toBeVisible();
	});
});

test.describe("STD prod static screens — family detail", () => {
	test("family detail screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_family_detail.html`);
		await expect(page).toHaveTitle(/STD Family Detail/);
		await expect(page.getByText(/Family Code: KE-PPRA-IT/i)).toBeVisible();
		await expect(page.getByRole("heading", { name: /VERSIONS REPOSITORY/i })).toBeVisible();
		await expect(page.getByText("REVIEW POLICY")).toBeVisible();
	});
});

test.describe("STD prod static screens — version detail", () => {
	test("version detail screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_version_detail.html`);
		await expect(page).toHaveTitle(/STD Version Detail/);
		await expect(page.getByText("ACTIVE VERSION — READ ONLY")).toBeVisible();
		await expect(page.getByRole("heading", { name: /Module Integrity Status/i })).toBeVisible();
		await expect(page.getByText("Operational Integrity")).toBeVisible();
	});
});
