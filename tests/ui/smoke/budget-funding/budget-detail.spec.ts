import { test, expect } from "@playwright/test";
import {
	loginAsBudgetOfficer,
	loginAsBudgetOtherEntityViewer,
	loginAsBudgetViewer,
} from "../../helpers/auth";

/**
 * BUD-CHG-001 v1.2 — BUD-UI-03 Budget workspace/detail
 * (/app/budget-funding/{budget_id}), against the canonical seeded
 * MOH-BUD-2027-001 baseline (see kentender_budget.seeds.
 * kentender_mvp_v1_portfolio §15.3) — this route reads by explicit id, not
 * the workspace's "current FY" auto-resolve, so it is stable regardless of
 * real wall-clock date.
 */

const MOH_BUDGET = "MOH-BUD-2027-001";

test.describe("Budget detail (BUD-UI-03)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
	});

	test("Overview tab shows positions, context, approval and activation", async ({ page }) => {
		await loginAsBudgetViewer(page);
		await page.goto(`/app/budget-funding/${MOH_BUDGET}`, { waitUntil: "domcontentloaded" });

		await expect(page.getByTestId("budget-detail-header")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("budget-detail-header")).toContainText(MOH_BUDGET);
		await expect(page.getByTestId("budget-detail-header")).toContainText("Active");

		const positions = page.getByTestId("budget-detail-position-cards");
		await expect(positions).toContainText("KES 160,000,000"); // Approved

		// Scoped to the context card's value cell: the rail's CTX-CHG-001 PE chip
		// also carries the entity name page-wide.
		await expect(page.locator("div").filter({ hasText: /^Ministry of Health$/ })).toBeVisible();
		await expect(page.getByText("MOH-FIN-BUD-2027-01 (Demo)")).toBeVisible();
		await expect(page.getByRole("link", { name: /moh-approved-procurement-budget/ })).toBeVisible();
	});

	test("Budget Lines tab lists both lines with totals", async ({ page }) => {
		await loginAsBudgetViewer(page);
		await page.goto(`/app/budget-funding/${MOH_BUDGET}/lines`, { waitUntil: "domcontentloaded" });

		const table = page.getByTestId("budget-detail-lines-table");
		await expect(table).toBeVisible({ timeout: 30_000 });
		await expect(table).toContainText("MOH-BL-DHI-2027");
		await expect(table).toContainText("MOH-BL-HWD-2027");
		await expect(table).toContainText("KES 160,000,000"); // Total approved
	});

	test("Funding Activity tab renders filters and the empty state for an unreserved budget", async ({
		page,
	}) => {
		await loginAsBudgetViewer(page);
		await page.goto(`/app/budget-funding/${MOH_BUDGET}/activity`, { waitUntil: "domcontentloaded" });

		await expect(page.getByTestId("budget-detail-activity-filter-line")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("budget-detail-activity-filter-event")).toBeVisible();
		await expect(page.getByTestId("budget-detail-activity-empty")).toBeVisible();
	});

	test("History tab lists the full lifecycle ledger", async ({ page }) => {
		await loginAsBudgetViewer(page);
		await page.goto(`/app/budget-funding/${MOH_BUDGET}/history`, { waitUntil: "domcontentloaded" });

		const table = page.getByTestId("budget-detail-history-table");
		await expect(table).toBeVisible({ timeout: 30_000 });
		await expect(table).toContainText("Budget version created");
		await expect(table).toContainText("Submitted for review");
		await expect(table).toContainText("Budget version approved and activated");
	});

	test("Officer sees Create revision; Viewer does not", async ({ page }) => {
		await loginAsBudgetOfficer(page);
		await page.goto(`/app/budget-funding/${MOH_BUDGET}`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("budget-detail-create-revision-btn")).toBeVisible({ timeout: 30_000 });

		await loginAsBudgetViewer(page);
		await page.goto(`/app/budget-funding/${MOH_BUDGET}`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("budget-detail-header")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("budget-detail-create-revision-btn")).toHaveCount(0);
	});

	test("Cross-PE Viewer is denied access to another entity's Budget", async ({ page }) => {
		await loginAsBudgetOtherEntityViewer(page);
		await page.goto(`/app/budget-funding/${MOH_BUDGET}`, { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("budget-detail-forbidden")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("budget-detail-forbidden")).toContainText(
			"You do not have access to this Budget.",
		);
	});

	test("Unknown Budget code shows the not-found state", async ({ page }) => {
		await loginAsBudgetViewer(page);
		await page.goto("/app/budget-funding/NO-SUCH-BUDGET-XYZ", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("budget-detail-not-found")).toBeVisible({ timeout: 30_000 });
	});
});
