import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * Budget & Funding portfolio (BUD-UI-01) — Stitch Desk shell + live bind.
 * Requires MOH-BUD-2027-2028..0003 seed (moh_mvp_v1_portfolio).
 * Chrome contract also covered by stitch-desk-chrome.spec.ts (shared baseline gate).
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding portfolio (BUD-UI-01)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("portfolio loads with Stitch regions and live rows", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByTestId("kt-bud-summary-strip")).toBeVisible();
		await expect(page.locator('[data-kt-bud-count="active"]')).toBeVisible();
		await expect(page.locator('[data-kt-bud-count="awaiting_review"]')).toBeVisible();
		await expect(page.locator('[data-kt-bud-count="returned"]')).toBeVisible();
		await expect(page.locator('[data-kt-bud-count="funding_exceptions"]')).toBeVisible();
		await expect(page.getByRole("heading", { name: "Budget & Funding" })).toBeVisible();
		await expect(page.getByRole("button", { name: /Register approved budget/i })).toBeVisible();
		await expect(page.getByRole("button", { name: /View funding performance/i })).toBeVisible();
		await expect(page.locator("[data-kt-bud-budgets-tbody]")).toBeVisible();
		await expect(page.getByText("MOH-BUD-2027-2028")).toBeVisible({ timeout: 20_000 });
		await expect(page.getByText("MOH-BUD-0002")).toBeVisible();
		await expect(page.getByText("MOH-BUD-2026-2027")).toBeVisible();
		await expect(page.locator("cdn.tailwindcss.com")).toHaveCount(0);
	});

	test("Stitch chrome resists Desk button/select bleed", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-portfolio",
			primaryCtaTestId: "kt-bud-register-budget",
			secondaryCtaTestId: "kt-bud-open-performance",
			selectSelector: '[data-kt-bud-filter="status"]',
		});
	});

	test("filter search field stays wide (not icon-sized Win98 box)", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const geometry = await page.evaluate(() => {
			const filters = document.querySelector(
				'[data-testid="kt-bud-pf-filters"]',
			) as HTMLElement | null;
			const search = document.querySelector(
				'[data-kt-bud-filter="search"]',
			) as HTMLElement | null;
			const status = document.querySelector(
				'[data-kt-bud-filter="status"]',
			) as HTMLElement | null;
			const fBox = filters?.getBoundingClientRect();
			const sBox = search?.getBoundingClientRect();
			const stBox = status?.getBoundingClientRect();
			return {
				filtersWidth: fBox?.width || 0,
				searchWidth: sBox?.width || 0,
				statusWidth: stBox?.width || 0,
				filtersDir: filters ? getComputedStyle(filters).flexDirection : "",
			};
		});
		expect(geometry.filtersDir).toBe("row");
		// Collapsed regression was ~58px (icon + padding only).
		expect(geometry.searchWidth).toBeGreaterThan(240);
		expect(geometry.searchWidth).toBeGreaterThan(geometry.statusWidth);
		expect(geometry.searchWidth / geometry.filtersWidth).toBeGreaterThan(0.35);
	});

	test("Register CTA navigates to live register form", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await page.getByTestId("kt-bud-register-budget").click();
		await page.waitForURL(/\/desk\/budget-register/, { timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-bud-register"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByRole("heading", { name: "Register approved budget" })).toBeVisible();
	});

	test("Funding Performance CTA navigates to live performance page", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await page.getByTestId("kt-bud-open-performance").click();
		await page.waitForURL(/\/desk\/budget-funding-performance/, { timeout: 20_000 });
		await expect(
			page.locator('[data-testid="kt-bud-performance"][data-kt-bud-live="1"]'),
		).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-bud-stub")).toHaveCount(0);
	});

	test("status filter reduces visible budget rows", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByText("MOH-BUD-2027-2028")).toBeVisible({ timeout: 20_000 });
		const statusFilter = page.locator('[data-kt-bud-filter="status"]');
		await statusFilter.selectOption({ label: "Active" });
		await expect(page.getByText("MOH-BUD-2027-2028")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByText("MOH-BUD-0002")).toHaveCount(0);
		await expect(page.getByText("MOH-BUD-2026-2027")).toHaveCount(0);
	});

	test("strip counts and money match MOH seed / Stitch", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator('[data-kt-bud-count="active"]')).toHaveText("1");
		await expect(page.locator('[data-kt-bud-count="awaiting_review"]')).toHaveText("1");
		await expect(page.locator('[data-kt-bud-count="returned"]')).toHaveText("0");
		await expect(page.locator('[data-kt-bud-count="funding_exceptions"]')).toHaveText("2");
		await expect(page.getByText("KES 560M")).toBeVisible();
		await expect(page.getByText("KES 105M")).toBeVisible();
		await expect(page.getByText("KES 0", { exact: true })).toBeVisible();
		await expect(page.getByText("Not active")).toBeVisible();
		// Revised Budget column: full title, bare mono code (no Ref: / tag icon).
		await expect(
			page.getByText("Ministry of Health Procurement Budget FY 2027/28", { exact: true }),
		).toBeVisible();
		await expect(page.locator('[data-kt-bud-ref="MOH-BUD-2027-2028"]')).toHaveText("MOH-BUD-2027-2028");
		await expect(page.getByText(/Ref:\s*MOH-BUD/)).toHaveCount(0);
		await expect(page.getByTestId("kt-bud-table-footer")).toBeVisible();
		await expect(page.getByTestId("kt-bud-table-footer")).toContainText(/Showing 3 of 3/);
		await expect(page.getByTestId("kt-bud-table-footer")).toContainText("Rows per page");
		// Page-size select: Material expand_more only — not SVG + Material double chevron.
		const pageSizeGlyph = await page.locator("[data-kt-footer-page-size]").evaluate((el) => {
			const cs = getComputedStyle(el);
			const sib = el.nextElementSibling;
			return {
				bgImage: cs.backgroundImage || "",
				material:
					!!sib &&
					sib.classList.contains("material-symbols-outlined") &&
					(sib.textContent || "").trim() === "expand_more",
			};
		});
		expect(pageSizeGlyph.material).toBeTruthy();
		expect(pageSizeGlyph.bgImage === "none" || pageSizeGlyph.bgImage === "").toBeTruthy();
	});

	test("empty search shows empty state with Register CTA", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await page.locator('[data-kt-bud-filter="search"]').fill("NO-SUCH-BUDGET-ZZZ");
		await expect(page.getByTestId("kt-bud-empty")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByText(/No procurement budget has been registered/i)).toBeVisible();
		await expect(page.getByTestId("kt-bud-empty-register")).toBeVisible();
	});

	test("row Open navigates to overview stub with budget ref", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByText("MOH-BUD-2027-2028")).toBeVisible({ timeout: 20_000 });
		await page
			.locator('tr[data-budget-code="MOH-BUD-2027-2028"] [data-kt-bud-action="open"]')
			.click();
		await page.waitForURL(/\/desk\/budget-overview\/MOH-BUD-2027-2028/, { timeout: 20_000 });
		await expect(page.getByTestId("kt-bud-stub")).toBeVisible({ timeout: 20_000 });
	});

	test("Budget Management workspace redirects to portfolio", async ({ page }) => {
		await page.goto("/desk/budget-management", { waitUntil: "domcontentloaded" });
		await page.waitForURL(/\/desk\/budget-funding/, { timeout: 30_000 });
		await expect(page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
	});
});
