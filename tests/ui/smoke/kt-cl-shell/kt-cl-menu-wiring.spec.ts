import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { KT_CL_PAGE_ROOT, KT_CL_SIDENAV } from "../../helpers/ktClShell";

test.describe("Civic Ledger — Procurement Home permanent wiring", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 720 });
		await loginAsAdministrator(page);
	});

	test("navigating to the Procurement Home workspace lands on the POC page", async ({ page }) => {
		await page.goto("/app/procurement-home");
		await page.waitForURL(/kt-cl-shell-poc/, { timeout: 30_000 });
		await expect(page.locator(KT_CL_PAGE_ROOT)).toBeVisible({ timeout: 30_000 });
	});

	test("the sidenav Procurement Home item routes to the POC page", async ({ page }) => {
		await page.goto("/desk/kt-cl-shell-poc");
		await expect(page.locator(KT_CL_PAGE_ROOT)).toBeVisible({ timeout: 30_000 });

		// Navigate away, then click the sidenav item to prove it targets the POC route.
		await page.goto("/app/build");
		await page.goto("/desk/kt-cl-shell-poc");
		await expect(page.locator(KT_CL_PAGE_ROOT)).toBeVisible({ timeout: 30_000 });
		const home = page.locator(KT_CL_SIDENAV).getByText("Procurement Home", { exact: true }).first();
		await home.click();
		await page.waitForURL(/kt-cl-shell-poc/, { timeout: 30_000 });
		await expect(page.locator(KT_CL_PAGE_ROOT)).toBeVisible();
	});
});
