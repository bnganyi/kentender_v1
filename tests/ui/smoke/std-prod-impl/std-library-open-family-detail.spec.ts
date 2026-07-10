import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectStdProdPageLoads } from "../../helpers/stdProdNavigation";

test.describe("STD prod library Open → family/version navigation", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("Open action on library table navigates to registered version detail for single-version family", async ({
		page,
	}) => {
		await page.goto("/desk/std-library");
		const libraryIframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(
			libraryIframe.getByRole("heading", { name: "Standard Tender Documents" }),
		).toBeVisible({ timeout: 30_000 });

		await libraryIframe.getByRole("button", { name: "Open" }).first().click();
		await expectStdProdPageLoads(page, {
			route: "std-version-detail",
			testid: "std-prod-std-version-detail",
		});
		await expect(page.locator("#page-std-version-detail .page-head")).toBeHidden();
	});
});
