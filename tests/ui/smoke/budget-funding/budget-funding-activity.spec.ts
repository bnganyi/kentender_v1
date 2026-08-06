import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-07 Funding Activity (Pack Phase 3 / Prompt 7 / §9.3 seed).
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding activity (BUD-UI-07)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("live strip and chronological rows with seed money", async ({ page }) => {
		await page.goto("/desk/budget-funding-activity/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-activity"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-workspace-chrome")).toBeVisible();
		await expect(root.getByTestId("kt-bud-activity-strip")).toBeVisible();
		await expect(root.getByTestId("kt-bud-activity-toolbar")).toBeVisible();
		// Search left, filters right.
		const searchBox = await root.getByTestId("kt-bud-activity-search-wrap").boundingBox();
		const typeBox = await root.getByTestId("kt-bud-activity-filter-type").boundingBox();
		expect(searchBox).toBeTruthy();
		expect(typeBox).toBeTruthy();
		expect((searchBox?.x || 0) < (typeBox?.x || 0)).toBeTruthy();
		await expect(root.getByTestId("kt-bud-activity-table")).toBeVisible();
		await expect(root.getByTestId("kt-bud-activity-table-footer")).toBeVisible();
		await expect(root.getByTestId("kt-bud-activity-table-footer")).toContainText(/Showing/i);

		await expect(root.locator('[data-kt-bud-activity-bal="reserved"]')).toHaveText(
			"KES 145,000,000",
		);
		await expect(root.locator('[data-kt-bud-activity-bal="committed"]')).toHaveText(
			"KES 310,000,000",
		);
		await expect(root.locator('[data-kt-bud-activity-bal="actual"]')).toHaveText(
			"KES 180,000,000",
		);
		await expect(root.locator('[data-kt-bud-activity-bal="outstanding"]')).toHaveText(
			"KES 130,000,000",
		);

		const rsv = root.locator('tr[data-activity-code="RSV-MOH-0001"]');
		await expect(rsv).toBeVisible({ timeout: 20_000 });
		await expect(rsv).toContainText("Funding reservation");
		await expect(rsv).toContainText("National digital health infrastructure upgrade");
		await expect(rsv).toContainText("DMD-MOH-2027-014");
		await expect(rsv).toContainText("KES 455,000,000");
		await expect(rsv).toContainText("Partially converted");
		await expect(rsv).toContainText("KES 145,000,000");
		await expect(rsv.getByTestId("kt-bud-activity-action")).toHaveText(/View reservation/i);

		const com = root.locator('tr[data-activity-code="COM-MOH-0001"]');
		await expect(com).toBeVisible();
		await expect(com).toContainText("Contract commitment");
		await expect(com).toContainText("Digital health infrastructure implementation contract");
		await expect(com).toContainText("CTR-MOH-2027-005");
		await expect(com).toContainText("KES 310,000,000");

		const exp = root.locator('tr[data-activity-code="EXP-MOH-0001"]');
		await expect(exp).toBeVisible();
		await expect(exp).toContainText("Actual expenditure snapshot");
		await expect(exp).toContainText("Finance system");
		await expect(exp).toContainText("KES 180,000,000");
		await expect(exp).toContainText("Stale");
		await expect(exp).not.toContainText("KES 0");

		// Filter select width matches wrap (chevron inside).
		const typeWrap = await root
			.locator('[data-kt-bud-activity-filter-field="type"] .kt-bud-activity-select-wrap')
			.boundingBox();
		expect(typeWrap).toBeTruthy();
		expect(Math.abs((typeBox?.width || 0) - (typeWrap?.width || 0))).toBeLessThan(2);

		const action = rsv.getByTestId("kt-bud-activity-action");
		await action.hover();
		await expect(action.locator(".kt-bud-activity-action-label")).toHaveCSS(
			"text-decoration-line",
			"underline",
		);
		await expect(action.locator(".material-symbols-outlined")).toHaveCSS(
			"text-decoration-line",
			"none",
		);

		await expect(root.getByTestId("kt-bud-overview-primary")).toHaveText(/Request revision/i);
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-activity",
			primaryCtaTestId: "kt-bud-overview-primary",
			secondaryCtaTestId: "kt-bud-view-performance",
			assertPrimaryHover: true,
			selectSelector: '[data-kt-bud-activity-filter="activity_type"]',
			headlineSelector: "[data-kt-bud-budget-title]",
		});
	});

	test("View opens in-canvas notice without Frappe dialog", async ({ page }) => {
		await page.goto("/desk/budget-funding-activity/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-activity"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });

		await root
			.locator('tr[data-activity-code="RSV-MOH-0001"] [data-testid="kt-bud-activity-action"]')
			.click();

		const notice = root.getByTestId("kt-bud-activity-notice");
		await expect(notice).toBeVisible({ timeout: 10_000 });
		await expect(notice).toContainText(/RSV-MOH-0001|DMD-MOH-2027-014/i);
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: /Message/i })).toHaveCount(0);

		await root.getByTestId("kt-bud-activity-notice-dismiss").click();
		await expect(notice).toBeHidden({ timeout: 5_000 });
	});

	test("type filter narrows rows", async ({ page }) => {
		await page.goto("/desk/budget-funding-activity/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-activity"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });

		await root.getByTestId("kt-bud-activity-filter-type").selectOption("commitment");
		await expect(root.locator('tr[data-activity-code="COM-MOH-0001"]')).toBeVisible();
		await expect(root.locator('tr[data-activity-code="RSV-MOH-0001"]')).toHaveCount(0);
		await expect(root.locator('tr[data-activity-code="EXP-MOH-0001"]')).toHaveCount(0);
	});
});
