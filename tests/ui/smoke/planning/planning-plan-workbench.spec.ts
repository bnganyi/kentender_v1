import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	HOD,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.12 Phase 4 (Slice B) — PLN-UI-07/08/09: the Annual Plan
 * workbench, Form Plan Items formation and the Plan Item editor with its live
 * baseline computation, in a real browser on the D13 world (the fixture
 * drives the real §8.2 commands to one accepted, unallocated entry —
 * PLN-DES-07's exact opening state).
 */

type PlanState = { plan_reference: string; plan_item_id?: string };

test.describe.configure({ mode: "serial" });

async function gotoPlan(page: import("@playwright/test").Page, reference: string): Promise<void> {
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.goto(`/app/annual-procurement-plan/${reference}`, { waitUntil: "domcontentloaded" });
	await expectReady(page, "plan");
}

test.describe("PLN-UI-07/08/09 Annual Plan workbench and Plan Item editor", () => {
	test.afterAll(() => restoreSite());

	test("single-source formation opens straight to the editor; the baseline recomputes live and the save reflects on the workbench", async ({ page }) => {
		const state = resetFixture<PlanState>("reset_workbench_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlan(page, state.plan_reference);

		// PLN-DES-07 exact composition
		await expect(page.locator(".kt-page-kicker")).toHaveText("ANNUAL PROCUREMENT PLAN");
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Draft");
		const strip = page.locator('[data-testid="pln-plan-summary-strip"]');
		await expect(strip.locator("label")).toHaveText(["Accepted departmental entries", "Allocated", "Plan Items", "Plan value", "Reserved share"]);
		await expect(strip).toContainText("KES 0");
		await expect(page.locator('[data-testid="pln-reserved-share"]')).toContainText("0% of plan value");
		await expect(page.locator('[data-testid="pln-unallocated-sources"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="pln-unallocated-sources"]')).toContainText("1 entry available");
		await expect(page.locator('[data-testid="pln-plan-items"] h3')).toHaveText("No Plan Items yet");
		await expect(page.locator('[data-testid="pln-readiness"] tbody tr')).toHaveCount(9);
		await expect(page.locator('[data-testid="pln-readiness-plan-funding-confirmed"] .kt-status')).toHaveText("Not started");
		await expect(page.locator('[data-testid="pln-request-funding"]')).toBeDisabled();
		await expect(page.locator('[data-testid="pln-submit-consolidated"]')).toBeDisabled();

		// PLN-DES-08: one source, no formation choice, straight to the editor
		await page.locator('[data-testid="pln-form-items"]').click();
		await expect(page.locator('[data-testid="pln-form-dialog"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-form-mode-each"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-form-confirm"]')).toHaveText(/Create 1 Plan Item/);
		await page.locator('[data-testid="pln-form-confirm"]').click();
		await expectReady(page, "plan-item");

		// PLN-DES-09 — read-only source, selects, computed schedule
		await expect(page.locator(".kt-page-title")).toHaveText("National digital health infrastructure upgrade");
		await expect(page.locator('[data-testid="ppi-badge"]')).toHaveText("Proposed");
		await expect(page.locator('[data-testid="ppi-source"]')).toContainText("KES 80,000,000");
		await expect(page.locator('[data-testid="ppi-price-index"]')).toHaveText("Market price index: not published for this category.");
		const method = page.locator('[data-testid="ppi-method"]');
		await expect(method).toHaveValue("Open Tender");
		await expect(method.locator("option", { hasText: "Low Value Procurement" })).toHaveCount(0);
		await expect(page.locator('[data-testid="ppi-value-band"]')).not.toHaveText("");
		await expect(page.locator('[data-testid="ppi-periods"]')).toHaveCount(0); // closed by default

		const objectiveSelect = page.locator('[data-testid="ppi-objective"]');
		await objectiveSelect.selectOption({ index: 1 });
		await page.locator('[data-testid="ppi-title"]').fill("Digital health infrastructure package");
		await page.locator('[data-testid="ppi-target-date"]').fill("2098-09-01");
		const bidOpening = page.locator('[data-testid="ppi-baseline-bid_opening"] td').nth(1);
		await expect(bidOpening).toHaveText("22 Sep 2098"); // 21-day governed tendering period, computed live
		await expect(page.locator('[data-testid="ppi-baseline-delivery_completion"]')).toContainText("from the authorised Requisition");
		await page.locator('[data-testid="ppi-adjust-periods"]').click();
		await page.locator('[data-testid="ppi-tendering_period_days"]').fill("14");
		await expect(bidOpening).toHaveText("15 Sep 2098");
		await page.locator('[data-testid="ppi-save"]').click();
		await expect(page.locator(".kt-page-title")).toHaveText("Digital health infrastructure package", { timeout: 30_000 });
		await expect(page.locator('[data-testid="ppi-periods-summary"]')).toHaveText("Adjusted from the governed defaults");

		// back on the workbench the item is listed and readiness moved on
		await page.locator(".pln-footer-bar button", { hasText: "Back to Annual Plan" }).click();
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-plan-items"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="pln-plan-items"]')).toContainText("Digital health infrastructure package");
		await expect(page.locator('[data-testid="pln-readiness-every-plan-item-has-a-strategic-objective"] .kt-status')).toHaveText("Complete");
		await expect(page.locator('[data-testid="pln-unallocated-sources"] tbody tr')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-form-items"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-request-funding"]')).toBeEnabled();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a period below its governed floor is refused on save with the field marked (PLN-AC-114)", async ({ page }) => {
		const state = resetFixture<PlanState>("reset_plan_item_fixture");
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await page.locator('[data-testid="ppi-target-date"]').fill("2098-09-01");
		await page.locator('[data-testid="ppi-adjust-periods"]').click();
		await page.locator('[data-testid="ppi-standstill_period_days"]').fill("10");
		await page.locator('[data-testid="ppi-save"]').click();
		const error = page.locator('[data-testid="ppi-error"]');
		await expect(error).toBeVisible();
		await expect(error).toContainText(/standstill/i);
	});

	test("dissolving a formed item returns the source to the unallocated pool", async ({ page }) => {
		const state = resetFixture<PlanState>("reset_plan_item_fixture");
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await page.locator('[data-testid="ppi-dissolve"]').click();
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-unallocated-sources"]')).toContainText("National digital health infrastructure upgrade");
		await expect(page.locator('[data-testid="pln-plan-items"] h3')).toHaveText("No Plan Items yet");
	});

	test("a combined item shows its sources table and requires the aggregation reason", async ({ page }) => {
		const state = resetFixture<PlanState>("reset_combined_item_fixture");
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await expect(page.locator('[data-testid="ppi-sources"] tbody tr')).toHaveCount(2);
		await expect(page.locator('[data-testid="ppi-sources"]')).toContainText("2 sources · 500 each · KES 120,000,000");
		await expect(page.locator('[data-testid="ppi-aggregation-indicator"]')).toHaveValue("Aggregated into this package");
		await expect(page.locator('[data-testid="ppi-aggregation"]')).toBeVisible();
	});

	test("a non-planner deep link masks as not-found", async ({ page }) => {
		const state = resetFixture<PlanState>("reset_workbench_fixture");
		await login(page, HOD, PASSWORD);
		await gotoPlan(page, state.plan_reference);
		await expect(page.locator('[data-testid="pln-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-form-items"]')).toHaveCount(0);
	});
});
