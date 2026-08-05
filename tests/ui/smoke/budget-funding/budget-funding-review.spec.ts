import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-11 Readiness and Review — checklist + workflow under workspace shell.
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding readiness review (BUD-UI-11)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("Draft checklist shows issue cards and Submit stays blocked", async ({ page }) => {
		await page.goto("/desk/budget-review/MOH-BUD-0004", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-review"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-workspace-chrome")).toBeVisible();
		await expect(root.locator("[data-kt-bud-budget-title]")).not.toHaveText("—");
		await expect(root.locator("[data-kt-bud-budget-title]")).not.toBeEmpty();
		await expect(root.getByTestId("kt-bud-review-header")).toBeVisible();
		await expect(root.getByTestId("kt-bud-review-status-chip")).toContainText(/Draft/i);
		await expect(root.locator('[data-kt-bud-review-group][data-status="issue"]').first()).toBeVisible({
			timeout: 20_000,
		});
		await expect(root.getByTestId("kt-bud-review-submit")).toBeDisabled();
		await expect(root.getByTestId("kt-bud-review-activate")).toBeHidden();
		await expect(root.getByTestId("kt-bud-review-footer")).toContainText(
			/does not constitute statutory budget approval/i,
		);

		await root.getByTestId("kt-bud-review-run").click();
		const notice = root.getByTestId("kt-bud-review-notice");
		await expect(notice).toBeVisible({ timeout: 10_000 });
		await expect(notice).toContainText(/Readiness check complete|Checklist/i);
		await expect(page.locator(".msgprint")).toHaveCount(0);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-review",
			primaryCtaTestId: "kt-bud-overview-primary",
			secondaryCtaTestId: "kt-bud-view-performance",
			headlineSelector: "[data-kt-bud-budget-title]",
		});
	});

	test("Submitted return modal requires reason without Message dialog", async ({ page }) => {
		await page.goto("/desk/budget-review/MOH-BUD-0002", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-review"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-review-status-chip")).toContainText(/Under review/i);
		await expect(root.getByTestId("kt-bud-review-return")).toBeVisible();
		await expect(root.getByTestId("kt-bud-review-mark")).toBeVisible();
		await expect(root.getByTestId("kt-bud-review-activate")).toBeVisible();

		await root.getByTestId("kt-bud-review-return").click();
		const modal = root.getByTestId("kt-bud-review-reason-modal");
		await expect(modal).toBeVisible({ timeout: 10_000 });
		await root.getByTestId("kt-bud-review-reason-confirm").click();
		await expect(root.locator('[data-kt-bud-error="comment"]')).toBeVisible();
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: /Message/i })).toHaveCount(0);

		await root.getByTestId("kt-bud-review-reason-comment").fill(
			"Return for missing operational clarification before activation.",
		);
		await root.getByTestId("kt-bud-review-reason-confirm").click();
		await expect(modal).toBeHidden({ timeout: 20_000 });
		await expect(root.getByTestId("kt-bud-review-status-chip")).toContainText(/Returned/i, {
			timeout: 20_000,
		});
	});

	test("Active shows activation record and no Activate CTA", async ({ page }) => {
		await page.goto("/desk/budget-review/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-review"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-review-status-chip")).toContainText(/Active/i);
		await expect(root.getByTestId("kt-bud-review-activation")).toBeVisible();
		await expect(root.getByTestId("kt-bud-review-activation")).toContainText(/Activated by/i);
		await expect(root.getByTestId("kt-bud-review-activate")).toBeHidden();
		await expect(root.getByTestId("kt-bud-review-submit")).toBeHidden();
	});

	test("soft-show rebind keeps live checklist after tab hop", async ({ page }) => {
		await page.goto("/desk/budget-review/MOH-BUD-0004", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-review"][data-kt-bud-live="1"]')
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
			.getByTestId("kt-bud-tab-budget-review")
			.click();
		await page.waitForURL(/budget-review/, { timeout: 20_000 });
		const again = page
			.locator('[data-testid="kt-bud-review"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(again).toBeVisible({ timeout: 45_000 });
		await expect(again.locator('[data-kt-bud-review-group]').first()).toBeVisible({
			timeout: 20_000,
		});
	});
});
