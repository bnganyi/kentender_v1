import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-12 Audit History — pack ledger under workspace shell.
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding audit history (BUD-UI-12)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("live table shows pack codes and full KES money", async ({ page }) => {
		await page.goto("/desk/budget-audit/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-audit"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-workspace-chrome")).toBeVisible();
		await expect(root.locator("[data-kt-bud-budget-title]")).toContainText(
			/Ministry of Health Procurement Budget/i,
		);
		await expect(root.locator("[data-kt-bud-budget-status]")).toContainText(/Active/i);
		// Stitch: Export is the header action — not Request revision / View performance.
		await expect(root.getByTestId("kt-bud-audit-export")).toBeVisible();
		await expect(root.getByTestId("kt-bud-overview-primary")).toHaveCount(0);
		await expect(root.getByTestId("kt-bud-view-performance")).toHaveCount(0);
		await expect(root.getByTestId("kt-bud-audit-toolbar")).toBeVisible();
		await expect(root.getByTestId("kt-bud-audit-toolbar").getByTestId("kt-bud-audit-export")).toHaveCount(
			0,
		);
		await expect(root.getByTestId("kt-bud-audit-table")).toBeVisible();
		await expect(root.getByTestId("kt-bud-audit-table-footer")).toContainText(/Showing/i);

		await expect(root.locator('tr[data-record-code="RSV-MOH-0001"]').first()).toBeVisible({
			timeout: 20_000,
		});
		await expect(root.locator('tr[data-record-code="MOH-BUD-0001"]').first()).toBeVisible();
		await expect(root).toContainText("KES 455,000,000");
		await expect(root).toContainText("KES 145,000,000");
		await expect(root).not.toContainText("455M");
		await expect(root).not.toContainText("RSV-2023-01");
		await expect(root.getByTestId("kt-bud-audit-action").first()).toContainText(/View/i);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-audit",
			primaryCtaTestId: "kt-bud-audit-export",
			primaryCtaStyle: "bordered",
			selectSelector: '[data-kt-bud-audit-filter="event_type"]',
			headlineSelector: "[data-kt-bud-budget-title]",
		});
	});

	test("event filter narrows rows; View notice without Message dialog", async ({ page }) => {
		await page.goto("/desk/budget-audit/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-audit"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });

		await root.getByTestId("kt-bud-audit-filter-event").selectOption("Funding reserved");
		await expect(root.locator('[data-testid="kt-bud-audit-row"]')).toHaveCount(1, {
			timeout: 20_000,
		});
		await expect(root.locator('tr[data-record-code="RSV-MOH-0001"]')).toBeVisible();
		await expect(root).toContainText("KES 455,000,000");

		await root.getByTestId("kt-bud-audit-action").click();
		const notice = root.getByTestId("kt-bud-audit-notice");
		await expect(notice).toBeVisible({ timeout: 10_000 });
		await expect(notice).toContainText(/RSV-MOH-0001|Funding reserved/);
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: /Message/i })).toHaveCount(0);
	});

	test("soft-show rebind keeps live table after tab hop", async ({ page }) => {
		await page.goto("/desk/budget-audit/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-audit"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await root.getByTestId("kt-bud-tab-budget-overview").click();
		await page.waitForURL(/budget-overview/, { timeout: 20_000 });
		await expect(
			page
				.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]')
				.filter({ visible: true }),
		).toBeVisible({ timeout: 45_000 });
		await page
			.locator('[data-testid="kt-bud-overview"]')
			.getByTestId("kt-bud-tab-budget-audit")
			.click();
		await page.waitForURL(/budget-audit/, { timeout: 20_000 });
		const again = page
			.locator('[data-testid="kt-bud-audit"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(again).toBeVisible({ timeout: 45_000 });
		await expect(again.locator('tr[data-record-code="RSV-MOH-0001"]').first()).toBeVisible({
			timeout: 20_000,
		});
	});
});
