import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-02 Funding Performance — standalone Stitch Desk management page.
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding Performance (BUD-UI-02)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("live root shows KPIs, pack codes, full KES, tables, Export, disclaimer", async ({
		page,
	}) => {
		await page.goto("/desk/budget-funding-performance", {
			waitUntil: "domcontentloaded",
		});
		const root = page.locator('[data-testid="kt-bud-performance"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-performance-title")).toContainText(
			"Funding Performance",
		);
		await expect(root.getByTestId("kt-bud-performance-export")).toBeVisible();
		await expect(root.getByTestId("kt-bud-performance-filters")).toBeVisible();
		await expect(root.getByTestId("kt-bud-performance-kpis")).toBeVisible();
		await expect(root.getByTestId("kt-bud-performance-coverage-table")).toBeVisible();
		await expect(root.getByTestId("kt-bud-performance-exceptions-table")).toBeVisible();
		await expect(root.getByTestId("kt-bud-performance-disclaimer")).toContainText(
			/Strategy alignment shows intended support/i,
		);

		await expect(root).toContainText("KES 560,000,000");
		await expect(root).toContainText("KES 145,000,000");
		await expect(root).toContainText("KES 310,000,000");
		await expect(root).not.toContainText("560M");
		await expect(root).not.toContainText("MOH-ST-04");
		await expect(root).toContainText("MOH-TGT-0001");

		await expect(root.getByTestId("kt-bud-performance-coverage-row").first()).toBeVisible({
			timeout: 20_000,
		});
		await expect(root.getByTestId("kt-bud-performance-exception-row").first()).toBeVisible();
		await expect(root.getByTestId("kt-bud-performance-coverage-action").first()).toContainText(
			/View Details/i,
		);
		await expect(root.getByTestId("kt-bud-performance-exception-action").first()).toContainText(
			/Review finance sync/i,
		);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-performance",
			primaryCtaTestId: "kt-bud-performance-export",
			primaryCtaStyle: "bordered",
			selectSelector: '[data-kt-bud-perf-filter="fiscal_period"]',
			headlineSelector: '[data-testid="kt-bud-performance-title"]',
		});
	});

	test("target filter narrows coverage; exception action without Message dialog", async ({
		page,
	}) => {
		await page.goto("/desk/budget-funding-performance", {
			waitUntil: "domcontentloaded",
		});
		let root = page.locator('[data-testid="kt-bud-performance"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 45_000 });

		// Exception action first (unfiltered — stale EXP is seed-backed).
		await root.getByTestId("kt-bud-performance-exception-action").first().click();
		const notice = root.getByTestId("kt-bud-performance-notice");
		await expect(notice).toBeVisible({ timeout: 10_000 });
		await expect(notice).toContainText(/finance sync|stale/i);
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: /Message/i })).toHaveCount(0);

		const targetFilter = root.locator('[data-kt-bud-perf-filter="primary_target"]');
		await expect(targetFilter.locator('option[value="MOH-TGT-0001"]')).toHaveCount(1, {
			timeout: 15_000,
		});
		await targetFilter.selectOption("MOH-TGT-0001");
		// Filter rebind flips data-kt-bud-live to 0 then 1 — re-query live root.
		root = page.locator('[data-testid="kt-bud-performance"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 20_000 });
		await expect(
			root.locator(
				'[data-testid="kt-bud-performance-coverage-row"][data-target-code="MOH-TGT-0001"]',
			),
		).toBeVisible({ timeout: 20_000 });
		await expect(root).toContainText("MOH-TGT-0001");
	});

	test("portfolio CTA lands on live Funding Performance", async ({ page }) => {
		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(
			page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]'),
		).toBeVisible({ timeout: 45_000 });
		await page.getByTestId("kt-bud-open-performance").click();
		await page.waitForURL(/\/desk\/budget-funding-performance/, { timeout: 20_000 });
		await expect(
			page.locator('[data-testid="kt-bud-performance"][data-kt-bud-live="1"]'),
		).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-bud-stub")).toHaveCount(0);
	});

	test("soft-show rebind keeps live root after portfolio hop", async ({ page }) => {
		await page.goto("/desk/budget-funding-performance", {
			waitUntil: "domcontentloaded",
		});
		const root = page.locator('[data-testid="kt-bud-performance"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root).toContainText("MOH-TGT-0001");

		await page.goto("/desk/budget-funding", { waitUntil: "domcontentloaded" });
		await expect(
			page.locator('[data-testid="kt-bud-portfolio"][data-kt-bud-live="1"]'),
		).toBeVisible({ timeout: 45_000 });

		await page.goto("/desk/budget-funding-performance", {
			waitUntil: "domcontentloaded",
		});
		const again = page.locator('[data-testid="kt-bud-performance"][data-kt-bud-live="1"]');
		await expect(again).toBeVisible({ timeout: 45_000 });
		await expect(again).toContainText("KES 560,000,000");
		await expect(again.getByTestId("kt-bud-performance-coverage-row").first()).toBeVisible({
			timeout: 20_000,
		});
	});
});
