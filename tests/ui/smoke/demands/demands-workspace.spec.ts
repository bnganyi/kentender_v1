import { test, expect } from "@playwright/test";
import {
	loginAsDemandNoScopeAdmin,
	loginAsDemandRequester,
} from "../../helpers/auth";
import {
	assertStitchDeskChrome,
	assertStitchSectionTableChrome,
} from "../../helpers/stitchDeskChrome";

/**
 * DEM-UI-01 Demands workspace — Stitch Desk canvas + live bind.
 * Route: /desk/demands-workspace
 */

const ROOT = '[data-testid="kt-dem-ui01-root"]';

test.describe("DEM-UI-01 Demands Workspace", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsDemandRequester(page);
	});

	test("Stitch regions, summary, filters, and live table render", async ({ page }) => {
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await expect(page.locator(`${ROOT}.kt-stitch-canvas`)).toBeVisible();
		await expect(page.getByRole("heading", { name: "Demands" })).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-create")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-summary")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-queue-my_drafts")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-queue-returned_to_me")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-queue-my_approvals")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-queue-budget_confirmations")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-filters")).toBeVisible();
		await expect(page.locator('[data-kt-dem-filter="entity"]')).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-clear-filters")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-table-wrap")).toBeVisible({ timeout: 15_000 });
		await expect(page.locator("[data-kt-dem-tbody] tr").first()).toBeVisible({ timeout: 15_000 });
		await expect(page.locator("cdn.tailwindcss.com")).toHaveCount(0);
		// Toolbar → title gap must match Budget (~20px), not CL space-y / main padding (~60px+).
		const gap = await page.evaluate(() => {
			const h1 = document.querySelector(".kt-dem-root h1");
			const toolbar = document.querySelector('[data-testid="kt-cl-toolbar"]');
			if (!h1 || !toolbar) return null;
			return Math.round(h1.getBoundingClientRect().top - toolbar.getBoundingClientRect().bottom);
		});
		expect(gap, "toolbar-to-title gap").not.toBeNull();
		expect(gap as number).toBeLessThanOrEqual(28);
		expect(gap as number).toBeGreaterThanOrEqual(8);
	});

	test("Stitch chrome resists Desk button/select bleed", async ({ page }) => {
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-dem-ui01-root",
			primaryCtaTestId: "kt-dem-ui01-create",
			selectSelector: '[data-kt-dem-filter="status"]',
		});
	});

	test("Table thead is primary-fixed blue; table card is square", async ({ page }) => {
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-dem-ui01-table-wrap")).toBeVisible({ timeout: 15_000 });
		await assertStitchSectionTableChrome(page, {
			tableWrapTestId: "kt-dem-ui01-table-wrap",
			roundedControlTestId: "kt-dem-ui01-create",
		});
	});

	test("Create demand routes to DEM-UI-02 form", async ({ page }) => {
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await page.getByTestId("kt-dem-ui01-create").click();
		await expect(page).toHaveURL(/demand-form/, { timeout: 15_000 });
		await expect(page.locator('[data-testid="kt-dem-ui02-root"][data-kt-dem-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByRole("heading", { name: "Create demand" })).toBeVisible();
	});

	test("Queue chip filters table; Clear restores; empty filtered state", async ({ page }) => {
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-dem-ui01-performance-link")).toBeVisible();

		const rowCountBefore = await page.locator("[data-kt-dem-tbody] tr").count();
		expect(rowCountBefore).toBeGreaterThan(0);

		await page.getByTestId("kt-dem-ui01-queue-my_drafts").click();
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 15_000 });
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-dem-active-queue", "my_drafts");

		// Impossible search → empty state (Clear filters only CTA).
		await page.locator('[data-kt-dem-filter="search"]').fill("__dem_ui01_no_match_xyz__");
		await expect(page.getByTestId("kt-dem-ui01-empty")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-dem-ui01-empty")).toContainText(
			/No Demands match these filters/i,
		);
		await expect(page.getByTestId("kt-dem-ui01-empty-clear")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui01-table-wrap")).toBeHidden();
		await expect(page.locator(".kt-dem-ui01-kpi-card")).toHaveCount(0);
		await expect(page.locator("canvas")).toHaveCount(0);

		await page.getByTestId("kt-dem-ui01-empty-clear").click();
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 15_000 });
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-dem-active-queue", "");
		await expect(page.locator('[data-kt-dem-filter="search"]')).toHaveValue("");
		await expect(page.getByTestId("kt-dem-ui01-table-wrap")).toBeVisible({ timeout: 15_000 });
		await expect(page.locator("[data-kt-dem-tbody] tr").first()).toBeVisible({ timeout: 15_000 });
	});

});

test.describe("DEM-UI-01 creation-scope (no Requester assignment)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await page.context().clearCookies();
		await loginAsDemandNoScopeAdmin(page);
	});

	test("Create demand opens blocked form (not a dead control)", async ({ page }) => {
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-dem-ui01-create")).toBeEnabled();
		await page.getByTestId("kt-dem-ui01-create").click();
		await expect(page).toHaveURL(/demand-form/, { timeout: 15_000 });
		await expect(page.locator('[data-testid="kt-dem-ui02-root"][data-kt-dem-live="1"]')).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-dem-ui02-scope-blocked")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-save")).toBeDisabled();
	});
});
