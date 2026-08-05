import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * BUD-UI-09 Budget Revision Review — dedicated page (not Revisions tab).
 */

test.describe.configure({ mode: "serial" });

test.describe("Budget Funding revision review (BUD-UI-09)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	test("list Submitted row opens dedicated review page with Stitch regions", async ({
		page,
	}) => {
		await page.goto("/desk/budget-revisions/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const list = page
			.locator('[data-testid="kt-bud-revisions"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(list).toBeVisible({ timeout: 45_000 });

		const row = list.locator('tr[data-revision-code="BR-MOH-0002"]');
		await expect(row).toBeVisible({ timeout: 20_000 });
		await expect(row).toHaveAttribute("data-open-action", "review");
		const reviewAction = row.getByTestId("kt-bud-rev-list-action");
		await expect(reviewAction).toContainText(/Review revision/i);
		await reviewAction.click();
		await page.waitForURL(/budget-revision-review/, { timeout: 20_000 });

		const root = page
			.locator('[data-testid="kt-bud-revision-review"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-rev-review-back")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-review-details")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-review-groups")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-review-financial")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-review-strategy")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-review-downstream")).toBeVisible();
		await expect(root.getByTestId("kt-bud-rev-review-footer")).toBeVisible();
		await expect(root.locator("[data-kt-bud-rev-review-code]")).toHaveText("BR-MOH-0002");
		await expect(root.locator("[data-kt-bud-rev-review-additions]")).toContainText(
			"KES 5,000,000",
		);
		await expect(page.getByText(/BR-2027-042/)).toHaveCount(0);
		await expect(page.getByText(/KES 45\.2M/)).toHaveCount(0);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-bud-revision-review",
			primaryCtaTestId: "kt-bud-rev-review-apply",
			headlineSelector: ".kt-bud-rev-review-title",
		});
	});

	test("Return opens reason modal; empty confirm shows error without Message dialog", async ({
		page,
	}) => {
		await page.goto("/desk/budget-revision-review/BR-MOH-0002", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-revision-review"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-rev-review-comment")).toHaveCount(0);
		await root.getByTestId("kt-bud-rev-review-return").click();
		const modal = root.getByTestId("kt-bud-rev-reason-modal");
		await expect(modal).toBeVisible({ timeout: 10_000 });
		await expect(modal.locator("[data-kt-bud-rev-reason-title]")).toContainText(
			/Return budget revision/i,
		);
		await root.getByTestId("kt-bud-rev-reason-confirm").click();
		await expect(modal.locator('[data-kt-bud-error="comment"]')).toBeVisible({
			timeout: 10_000,
		});
		await expect(modal.locator('[data-kt-bud-error="comment"]')).not.toHaveText("");
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: /Message/i })).toHaveCount(0);
	});

	test("Back to Revisions returns to list", async ({ page }) => {
		await page.goto("/desk/budget-revision-review/BR-MOH-0002", {
			waitUntil: "domcontentloaded",
		});
		const root = page
			.locator('[data-testid="kt-bud-revision-review"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		await root.getByTestId("kt-bud-rev-review-back").click();
		await page.waitForURL(/budget-revisions/, { timeout: 20_000 });
		await expect(
			page
				.locator('[data-testid="kt-bud-revisions"][data-kt-bud-live="1"]')
				.filter({ visible: true }),
		).toBeVisible({ timeout: 45_000 });
	});

	test("Apply from review soft-shows list with Applied status and View action", async ({
		page,
	}) => {
		// Mount Revisions first so return from review hits soft-show (not a cold page load).
		await page.goto("/desk/budget-revisions/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const list = page
			.locator('[data-testid="kt-bud-revisions"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(list).toBeVisible({ timeout: 45_000 });
		const row = list.locator('tr[data-revision-code="BR-MOH-0002"]');
		await expect(row).toBeVisible({ timeout: 20_000 });
		await expect(row).toContainText("Pending Review");
		await expect(row.getByTestId("kt-bud-rev-list-action")).toContainText(/Review revision/i);
		await row.getByTestId("kt-bud-rev-list-action").click();
		await page.waitForURL(/budget-revision-review/, { timeout: 20_000 });

		const root = page
			.locator('[data-testid="kt-bud-revision-review"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(root).toBeVisible({ timeout: 45_000 });
		const apply = root.getByTestId("kt-bud-rev-review-apply");
		await expect(apply).toBeEnabled({ timeout: 15_000 });
		await apply.click();
		await page.waitForURL(/budget-revisions/, { timeout: 20_000 });

		const listAgain = page
			.locator('[data-testid="kt-bud-revisions"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(listAgain).toBeVisible({ timeout: 45_000 });
		const appliedRow = listAgain.locator('tr[data-revision-code="BR-MOH-0002"]');
		await expect(appliedRow).toBeVisible({ timeout: 20_000 });
		await expect(appliedRow).toContainText("Applied");
		await expect(appliedRow).toHaveAttribute("data-open-action", "view");
		await expect(appliedRow.getByTestId("kt-bud-rev-list-action")).toContainText(
			/View revision/i,
		);
	});
});
