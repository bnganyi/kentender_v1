import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-10 Downstream Usage — pack §9.3 lineage under workspace shell.
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding downstream usage (BUD-UI-10)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("live table shows pack lineage codes and full KES money", async ({ page }) => {
		await page.goto("/desk/budget-downstream/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-downstream"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-workspace-chrome")).toBeVisible();
		await expect(root.getByTestId("kt-bud-downstream-toolbar")).toBeVisible();
		await expect(root.getByTestId("kt-bud-downstream-table")).toBeVisible();
		await expect(root.getByTestId("kt-bud-downstream-table-footer")).toContainText(/Showing/i);

		const row = root.locator('tr[data-reservation-code="RSV-MOH-0001"]');
		await expect(row).toBeVisible({ timeout: 20_000 });
		await expect(row).toContainText("DMD-MOH-2027-014");
		await expect(row).toContainText("PPI-MOH-2027-021");
		await expect(row).toContainText("TND-MOH-2027-008");
		await expect(row).toContainText("CTR-MOH-2027-005");
		await expect(row).toContainText("KES 145,000,000");
		await expect(row).toContainText("KES 310,000,000");
		await expect(row).toContainText("Partially converted");
		await expect(row).not.toContainText("145M");
		await expect(row).not.toContainText("DM-MOH-2027-042");
		await expect(row.getByTestId("kt-bud-downstream-action")).toContainText(/View reservation/i);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-downstream",
			primaryCtaTestId: "kt-bud-overview-primary",
			secondaryCtaTestId: "kt-bud-view-performance",
			selectSelector: '[data-kt-bud-downstream-filter="status"]',
			headlineSelector: "[data-kt-bud-budget-title]",
		});
	});

	test("View reservation shows in-canvas notice without Message dialog", async ({ page }) => {
		await page.goto("/desk/budget-downstream/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-downstream"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		const row = root.locator('tr[data-reservation-code="RSV-MOH-0001"]');
		await row.getByTestId("kt-bud-downstream-action").click();
		const notice = root.getByTestId("kt-bud-downstream-notice");
		await expect(notice).toBeVisible({ timeout: 10_000 });
		await expect(notice).toContainText(/RSV-MOH-0001|DMD-MOH-2027-014/);
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: /Message/i })).toHaveCount(0);
	});

	test("soft-show rebind keeps live table after tab hop", async ({ page }) => {
		await page.goto("/desk/budget-downstream/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-downstream"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await root.getByTestId("kt-bud-tab-budget-funding-activity").click();
		await page.waitForURL(/budget-funding-activity/, { timeout: 20_000 });
		await expect(
			page
				.locator('[data-testid="kt-bud-activity"][data-kt-bud-live="1"]')
				.filter({ visible: true }),
		).toBeVisible({ timeout: 45_000 });
		await page
			.locator('[data-testid="kt-bud-activity"]')
			.getByTestId("kt-bud-tab-budget-downstream")
			.click();
		await page.waitForURL(/budget-downstream/, { timeout: 20_000 });
		const again = page
			.locator('[data-testid="kt-bud-downstream"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(again).toBeVisible({ timeout: 45_000 });
		await expect(again.locator('tr[data-reservation-code="RSV-MOH-0001"]')).toBeVisible({
			timeout: 20_000,
		});
	});
});
