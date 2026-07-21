import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * PUB-A2 Publications queue.
 * Route: /desk/publications
 */

const ROOT = '[data-testid="kt-cl-pub-a2-root"]';

test.describe("PUB-A2 Publications Queue", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
	});

	test("root, tabs, and table host render", async ({ page }) => {
		await page.goto("/desk/publications");
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-cl-pub-a2-tabs")).toBeVisible();
		await expect(page.getByTestId("kt-cl-page-header")).toBeVisible();
		await expect(page.getByTestId("kt-cl-page-title")).toHaveText(/Publications/i);
		await expect(page.getByTestId("kt-cl-page-subtitle")).toBeVisible();
		await expect(page.getByTestId("kt-cl-ui00-tab-awaiting_setup")).toBeVisible();
		await expect(page.getByTestId("kt-cl-ui00-tab-awaiting_setup")).toHaveText(/Awaiting Setup\s*\(\d+\)/);
		await expect(page.getByTestId("kt-cl-ui00-tab-ready_to_publish")).toBeVisible();
		await expect(page.getByTestId("kt-cl-ui00-tab-published")).toBeVisible();
		await expect(page.getByTestId("kt-cl-ui00-tab-all")).toBeVisible();
		const summaryCard = page.locator('[data-testid="kt-cl-queue-summary-card"][data-layout="bento"]').first();
		await expect(summaryCard).toBeVisible();
		// Table wrapper or empty state both satisfy the queue shell.
		const table = page.getByTestId("kt-cl-pub-a2-table");
		const empty = page.getByTestId("kt-cl-pub-a2-empty");
		await expect(table.or(empty)).toBeVisible({ timeout: 15_000 });
	});
});
