import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-06 Check and Reserve — Stitch modal (available + insufficient).
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Check and Reserve (BUD-UI-06)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("available state shows full KES, pack line code, Reserve enabled", async ({ page }) => {
		await page.goto("/desk/budget-check-reserve", { waitUntil: "domcontentloaded" });
		const root = page.locator('[data-testid="kt-bud-check-reserve"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-check-reserve-title")).toContainText(
			"Check and reserve funding",
		);
		await expect(root.getByTestId("kt-bud-check-reserve-context")).toBeVisible();
		await expect(root.getByTestId("kt-bud-check-reserve-decision-available")).toBeVisible();
		await expect(root.getByTestId("kt-bud-check-reserve-reserve")).toBeEnabled();
		await expect(root).toContainText("KES 50,000,000");
		await expect(root).toContainText("KES 80,000,000");
		await expect(root).not.toContainText("80M");
		await expect(root).toContainText("MOH-BL-HWD-2027");
		await expect(root).toContainText(/will not create additional funding holds/i);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-check-reserve",
			primaryCtaTestId: "kt-bud-check-reserve-reserve",
			selectSelector: '[data-kt-bud-cr-filter="budget_line"]',
			headlineSelector: '[data-testid="kt-bud-check-reserve-title"]',
		});
	});

	test("insufficient state disables Reserve and shows shortfall", async ({ page }) => {
		await page.goto("/desk/budget-check-reserve/insufficient", {
			waitUntil: "domcontentloaded",
		});
		const root = page.locator('[data-testid="kt-bud-check-reserve"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-check-reserve-decision-insufficient")).toBeVisible({
			timeout: 20_000,
		});
		await expect(root.getByTestId("kt-bud-check-reserve-reserve-disabled")).toBeDisabled();
		await expect(root.getByTestId("kt-bud-check-reserve-select-line")).toBeVisible();
		await expect(root.getByTestId("kt-bud-check-reserve-return")).toBeVisible();
		await expect(root).toContainText("KES 455,000,000");
		await expect(root).toContainText(/Shortfall/i);
		await expect(root).not.toContainText("455M");
		await expect(root).toContainText("MOH-BL-DHI-2027");
		await expect(page.locator(".msgprint")).toHaveCount(0);
	});

	test("line change re-checks; Cancel closes without Message dialog", async ({ page }) => {
		await page.goto("/desk/budget-check-reserve", { waitUntil: "domcontentloaded" });
		const root = page.locator('[data-testid="kt-bud-check-reserve"][data-kt-bud-live="1"]');
		await expect(root).toBeVisible({ timeout: 45_000 });

		const lineSelect = root.locator('[data-kt-bud-cr-filter="budget_line"]');
		await lineSelect.selectOption("MOH-BL-DHI-2027");
		const again = page.locator('[data-testid="kt-bud-check-reserve"][data-kt-bud-live="1"]');
		await expect(again).toBeVisible({ timeout: 20_000 });
		// 50M request against MOH-BL-DHI-2027 (25M available) → insufficient
		await expect(again.getByTestId("kt-bud-check-reserve-decision-insufficient")).toBeVisible({
			timeout: 20_000,
		});

		// Insufficient panel exposes Return (Cancel lives only on the available panel).
		await again.getByTestId("kt-bud-check-reserve-return").click();
		await expect(page.getByTestId("kt-bud-check-reserve-host")).toBeHidden({ timeout: 10_000 });
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: /Message/i })).toHaveCount(0);
	});
});
