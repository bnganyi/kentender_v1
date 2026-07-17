import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const GALLERY = '[data-testid="kt-cl-gallery"]';

test.describe("Civic Ledger component gallery", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1280, height: 720 });
		await loginAsAdministrator(page);
	});

	test("renders every component from the library", async ({ page }) => {
		await page.goto("/desk/kt-cl-components");
		await expect(page.locator(GALLERY)).toBeVisible({ timeout: 30_000 });

		// Each documented section is present.
		for (const id of ["buttons", "breadcrumbs", "status-chips", "kpi-cards", "calendar", "data-table", "top-bar"]) {
			await expect(page.locator(`[data-testid="kt-cl-gallery-section"][data-section="${id}"]`)).toBeVisible();
		}

		// Representative component instances render.
		await expect(
			page.locator('[data-section="status-chips"] [data-testid="kt-cl-status-chip"]'),
		).toHaveCount(4);
		await expect(page.locator('[data-testid="kt-cl-kpi-card"]')).toHaveCount(3);
		await expect(page.locator('[data-testid="kt-cl-calendar"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-cl-data-table"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-cl-toolbar"]')).toBeVisible();

		// Scoped tokens apply inside the gallery too (primary #000b1d).
		const chip = page.locator('[data-testid="kt-cl-status-chip"][data-tone="approved"]').first();
		const dotColor = await chip
			.locator("span")
			.first()
			.evaluate((el) => getComputedStyle(el).backgroundColor);
		expect(dotColor).toBe("rgb(0, 11, 29)");
	});
});
