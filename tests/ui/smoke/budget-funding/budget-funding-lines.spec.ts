import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-04 / BUD-UI-05 Budget Lines + Line Editor (Pack Phase 3 / Prompt 5).
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding lines (BUD-UI-04 / BUD-UI-05)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("open from Overview tab shows live lines table with seed money", async ({ page }) => {
		await page.goto("/desk/budget-overview/MOH-BUD-0001", { waitUntil: "domcontentloaded" });
		await expect(
			page.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]'),
		).toBeVisible({ timeout: 45_000 });

		await page
			.locator('[data-testid="kt-bud-tab-budget-lines"]')
			.filter({ visible: true })
			.click();
		await page.waitForURL(/\/desk\/budget-lines\/MOH-BUD-0001/, { timeout: 20_000 });

		const root = page
			.locator('[data-testid="kt-bud-lines"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-workspace-chrome")).toBeVisible();
		await expect(root.getByTestId("kt-bud-lines-table")).toBeVisible();
		await expect(root.getByTestId("kt-bud-lines-toolbar")).toBeVisible();
		await expect(root.getByTestId("kt-bud-lines-search")).toBeVisible();
		await expect(root.getByTestId("kt-bud-lines-filter-source")).toBeVisible();
		await expect(root.getByTestId("kt-bud-lines-filter-target")).toBeVisible();
		await expect(root.getByTestId("kt-bud-lines-new")).toBeVisible();
		await expect(root.getByTestId("kt-bud-lines-new")).toHaveText(/New Line/i);
		// New Line must be a filled surface button, not a chromeless text link.
		await expect(root.getByTestId("kt-bud-lines-new")).toHaveCSS(
			"background-color",
			"rgb(238, 237, 243)",
		);
		await expect(root.getByTestId("kt-bud-lines-table-footer")).toBeVisible();
		await expect(root.getByTestId("kt-bud-lines-table-footer")).toContainText(/Showing/i);

		// Filter select chevrons sit inside fixed-width wraps (not outside the box).
		const sourceBox = await root.getByTestId("kt-bud-lines-filter-source").boundingBox();
		const sourceWrap = await root
			.locator('[data-kt-bud-lines-filter-field="source"] .kt-bud-lines-select-wrap')
			.boundingBox();
		expect(sourceBox).toBeTruthy();
		expect(sourceWrap).toBeTruthy();
		expect(Math.abs((sourceBox?.width || 0) - (sourceWrap?.width || 0))).toBeLessThan(2);

		const row1 = root.locator('tr[data-line-code="MOH-BL-0001"]');
		await expect(row1).toBeVisible({ timeout: 20_000 });
		await expect(row1).toContainText("Digital clinical systems infrastructure");
		await expect(row1).toContainText("MOH-BL-0001");
		await expect(row1).toContainText("KES 480,000,000");
		await expect(row1).toContainText("KES 25,000,000");
		await expect(row1).toContainText("Stale");
		await expect(row1).toContainText("Needs attention");
		const action1 = row1.getByTestId("kt-bud-line-action");
		await expect(action1).toHaveText(/Review line/i);
		await action1.hover();
		await expect(action1.locator(".kt-bud-line-action-label")).toHaveCSS(
			"text-decoration-line",
			"underline",
		);
		await expect(action1.locator(".material-symbols-outlined")).toHaveCSS(
			"text-decoration-line",
			"none",
		);

		const row2 = root.locator('tr[data-line-code="MOH-BL-0002"]');
		await expect(row2).toBeVisible();
		await expect(row2).toContainText("Digital health technical capability");
		await expect(row2).toContainText("Unknown");
		await expect(row2).toContainText("Complete");
		await expect(row2.getByTestId("kt-bud-line-action")).toHaveText(/View line/i);

		await expect(root.getByTestId("kt-bud-overview-primary")).toHaveText(/Request revision/i);
		await expect(page.locator("body")).toHaveClass(/kt-cl-shell/);
		await expect(page.locator("body")).toHaveClass(/kt-bud-workspace-active/);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-lines",
			primaryCtaTestId: "kt-bud-overview-primary",
			secondaryCtaTestId: "kt-bud-view-performance",
			headlineSelector: "[data-kt-bud-budget-title]",
		});
	});

	test("Active New Line shows in-canvas notice without Frappe dialog", async ({ page }) => {
		await page.goto("/desk/budget-lines/MOH-BUD-0001", { waitUntil: "domcontentloaded" });
		const root = page
			.locator('[data-testid="kt-bud-lines"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });

		await root.getByTestId("kt-bud-lines-new").click();

		const notice = root.getByTestId("kt-bud-lines-notice");
		await expect(notice).toBeVisible({ timeout: 10_000 });
		await expect(notice).toContainText(/Revision required/i);
		await expect(notice).toContainText(/cannot add lines directly/i);
		await expect(root.getByTestId("kt-bud-lines-notice-cta")).toBeVisible();
		// No vanilla Frappe Message dialog.
		await expect(page.locator(".msgprint, .modal-title:has-text('Revision required')")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: /Revision required/i })).toHaveCount(0);

		await root.getByTestId("kt-bud-lines-notice-dismiss").click();
		await expect(notice).toBeHidden({ timeout: 5_000 });
	});

	test("Active drawer opens read-only without Save", async ({ page }) => {
		await page.goto("/desk/budget-lines/MOH-BUD-0001", { waitUntil: "domcontentloaded" });
		const root = page
			.locator('[data-testid="kt-bud-lines"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });

		await root
			.locator('tr[data-line-code="MOH-BL-0001"] [data-testid="kt-bud-line-action"]')
			.click();

		const drawer = root.getByTestId("kt-bud-line-drawer");
		await expect(drawer).toBeVisible({ timeout: 15_000 });
		await expect(root.getByTestId("kt-bud-line-drawer-scrim")).toBeVisible();
		await expect(root.getByTestId("kt-bud-line-section-funding")).toBeVisible();
		await expect(root.getByTestId("kt-bud-line-section-strategy")).toBeVisible();
		await expect(root.getByTestId("kt-bud-line-section-pvc")).toBeVisible();
		await expect(drawer.locator('[data-kt-bud-line-field="code"]')).toHaveText("MOH-BL-0001");
		await expect(root.getByTestId("kt-bud-line-title")).toHaveValue(
			"Digital clinical systems infrastructure",
		);
		await expect(root.getByTestId("kt-bud-line-save")).toBeHidden();
		await expect(root.getByTestId("kt-bud-line-request-revision")).toBeVisible();

		await root.getByTestId("kt-bud-line-drawer-close").click();
		await expect(drawer).toBeHidden({ timeout: 10_000 });
	});

	test("round-trip Overview keeps shell and lines remount", async ({ page }) => {
		await page.goto("/desk/budget-lines/MOH-BUD-0001", { waitUntil: "domcontentloaded" });
		const lines = page
			.locator('[data-testid="kt-bud-lines"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(lines).toBeVisible({ timeout: 45_000 });
		await expect(page.locator("body")).toHaveClass(/kt-cl-shell/);

		await lines.getByTestId("kt-bud-tab-budget-overview").click();
		await page.waitForURL(/\/desk\/budget-overview\/MOH-BUD-0001/, { timeout: 20_000 });
		const overview = page
			.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(overview).toBeVisible({ timeout: 45_000 });
		await expect(page.locator("body")).toHaveClass(/kt-cl-shell/);

		await overview.getByTestId("kt-bud-tab-budget-lines").click();
		await page.waitForURL(/\/desk\/budget-lines\/MOH-BUD-0001/, { timeout: 20_000 });
		const linesAgain = page
			.locator('[data-testid="kt-bud-lines"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(linesAgain).toBeVisible({ timeout: 45_000 });
		await expect(linesAgain.locator('tr[data-line-code="MOH-BL-0001"]')).toContainText(
			"KES 480,000,000",
		);
	});
});
