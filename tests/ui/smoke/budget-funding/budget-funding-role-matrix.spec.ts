import { test, expect, Page } from "@playwright/test";
import {
	loginAsBudgetAuthority,
	loginAsBudgetOfficer,
	loginAsBudgetOfficerAuthority,
	loginAsBudgetOtherEntity,
	loginAsBudgetReviewer,
	loginAsBudgetViewer,
} from "../../helpers/auth";

/**
 * BUD-SUP-002 — focused UI role matrix (capability gating).
 * Server enforcement is covered by kentender_budget.tests.test_budget_role_matrix.
 */

test.describe.configure({ mode: "serial" });

async function openReview(page: Page, code: string) {
	await page.goto(`/desk/budget-review/${code}`, { waitUntil: "domcontentloaded" });
	return page.locator('[data-testid="kt-bud-review"]').filter({ visible: true });
}

test.describe("Budget Funding role matrix (BUD-SUP-002)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
	});

	test("Viewer: Funding Performance + export; Draft review denied", async ({ page }) => {
		await loginAsBudgetViewer(page);
		await page.goto("/desk/budget-funding-performance", {
			waitUntil: "domcontentloaded",
		});
		const perf = page.locator(
			'[data-testid="kt-bud-performance"][data-kt-bud-live="1"]',
		);
		await expect(perf).toBeVisible({ timeout: 45_000 });
		await expect(perf.getByTestId("kt-bud-performance-export")).toBeVisible();

		const review = await openReview(page, "MOH-BUD-0004");
		await expect(review).toHaveAttribute("data-kt-bud-error", "1", { timeout: 45_000 });
		await expect(review).toHaveAttribute("data-kt-bud-live", "0");
		// Fixture chrome may still paint Submit; live bind never enables it for Viewer.
		await expect(review.getByTestId("kt-bud-review-submit")).toBeDisabled();
	});

	test("Officer: Draft submit chrome; no review/activate; Active read-only; export hidden", async ({
		page,
	}) => {
		await loginAsBudgetOfficer(page);
		const draft = await openReview(page, "MOH-BUD-0004");
		await expect(draft).toHaveAttribute("data-kt-bud-live", "1", { timeout: 45_000 });
		await expect(draft.getByTestId("kt-bud-review-submit")).toBeVisible();
		await expect(draft.getByTestId("kt-bud-review-return")).toBeHidden();
		await expect(draft.getByTestId("kt-bud-review-mark")).toBeHidden();
		await expect(draft.getByTestId("kt-bud-review-activate")).toBeHidden();

		await page.goto("/desk/budget-overview/MOH-BUD-0001", {
			waitUntil: "domcontentloaded",
		});
		const overview = page
			.locator('[data-testid="kt-bud-overview"][data-kt-bud-live="1"]')
			.filter({ visible: true });
		await expect(overview).toBeVisible({ timeout: 45_000 });
		await expect(overview.locator("[data-kt-bud-budget-title]")).not.toHaveText("—");
		// Active workspace primary is Request revision — not direct baseline edit.
		await expect(overview.getByTestId("kt-bud-overview-primary")).toContainText(
			/revision/i,
		);

		await page.goto("/desk/budget-funding-performance", {
			waitUntil: "domcontentloaded",
		});
		const perf = page.locator(
			'[data-testid="kt-bud-performance"][data-kt-bud-live="1"]',
		);
		await expect(perf).toBeVisible({ timeout: 45_000 });
		const exportBtn = perf.getByTestId("kt-bud-performance-export");
		await expect(exportBtn).toHaveClass(/hidden/);
		await expect(exportBtn).toBeDisabled();
		await expect(exportBtn).toHaveAttribute("aria-hidden", "true");
	});

	test("Reviewer: Return on Submitted; Activate disabled; Submit hidden", async ({ page }) => {
		await loginAsBudgetReviewer(page);
		const root = await openReview(page, "MOH-BUD-0002");
		await expect(root).toHaveAttribute("data-kt-bud-live", "1", { timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-review-submit")).toBeHidden();
		await expect(root.getByTestId("kt-bud-review-return")).toBeVisible();
		await expect(root.getByTestId("kt-bud-review-return")).toBeEnabled();
		// Prep pins reviewed_by for AC-018 dual case → Mark is correctly hidden.
		await expect(root.getByTestId("kt-bud-review-mark")).toBeHidden();
		await expect(root.getByTestId("kt-bud-review-activate")).toBeVisible();
		await expect(root.getByTestId("kt-bud-review-activate")).toBeDisabled();
	});

	test("Authority: Activate enabled on reviewed Submitted (not self-submitter)", async ({
		page,
	}) => {
		await loginAsBudgetAuthority(page);
		const root = await openReview(page, "MOH-BUD-0002");
		await expect(root).toHaveAttribute("data-kt-bud-live", "1", { timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-review-submit")).toBeHidden();
		await expect(root.getByTestId("kt-bud-review-activate")).toBeVisible();
		// Prep: submitted_by=dual, reviewed_by=reviewer → Authority may activate.
		await expect(root.getByTestId("kt-bud-review-activate")).toBeEnabled();
	});

	test("Dual Officer+Authority: AC-018 Activate locked when self-submitter", async ({
		page,
	}) => {
		await loginAsBudgetOfficerAuthority(page);
		const root = await openReview(page, "MOH-BUD-0002");
		await expect(root).toHaveAttribute("data-kt-bud-live", "1", { timeout: 45_000 });
		await expect(root.getByTestId("kt-bud-review-activate")).toBeVisible();
		await expect(root.getByTestId("kt-bud-review-activate")).toBeDisabled();
		await expect(root.locator("[data-kt-bud-review-activate-lock]")).toBeVisible();
	});

	test("Other-entity Officer: PE-MOH review denied", async ({ page }) => {
		await loginAsBudgetOtherEntity(page);
		const root = await openReview(page, "MOH-BUD-0001");
		await expect(root).toHaveAttribute("data-kt-bud-error", "1", { timeout: 45_000 });
		await expect(root).toHaveAttribute("data-kt-bud-live", "0");
	});
});
