import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { gotoKtClShellPoc, KT_CL_PAGE_ROOT } from "../../helpers/ktClShell";

// Closeout evidence: fresh-context 1280px captures of the ported screen and the
// component gallery. Saved to test-results/ for the writeup.
test.describe("Civic Ledger — visual evidence @evidence", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 900 });
		await loginAsAdministrator(page);
	});

	test("capture POC page", async ({ page }) => {
		await gotoKtClShellPoc(page);
		await expect(page.locator('[data-testid="kt-cl-data-table"]')).toBeVisible();
		await page.waitForTimeout(600);
		await page.screenshot({ path: "test-results/kt-cl-poc-1280.png", fullPage: true });
	});

	test("capture component gallery", async ({ page }) => {
		await page.goto("/desk/kt-cl-components");
		await expect(page.locator('[data-testid="kt-cl-gallery"]')).toBeVisible({ timeout: 30_000 });
		await page.waitForTimeout(600);
		await page.screenshot({ path: "test-results/kt-cl-gallery-1280.png", fullPage: true });
	});
});
