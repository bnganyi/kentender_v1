/**
 * PLN-CHG-001 v1.27 / BUD-CHG-001 v1.11 — the over-budget hand-off, driven in
 * the browser by the actors who hold each step (KT-STD-001 v1.8 §3B.7's
 * thinner browser check, and the §7.7 hand-off register end to end).
 *
 * The Planner meets an update that one budget line cannot carry, hands the
 * fix to the Budget Officer from the plan itself, and waits; the Budget
 * Officer finds the request in My Work and on the Budget workspace and
 * declines it with a reason; the Planner is back where the decision leaves
 * them — blocked, with the request fix offered again and a "Continue plan
 * update" item in My Work. Every screen is checked for the next step and the
 * tracker agreeing, and for zero console errors.
 */
import { expect, test, type Page } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUTHOR,
	BUDGET_OFFICER,
	FY,
	OU_NAME,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	resetFixture,
	restoreSite,
} from "./helpers";

test.describe.configure({ timeout: 240_000 });

type OverBudget = { plan_reference: string };

// The test world's roles are site-wide, so My Work also lists the live dev
// plan's items; every assertion is scoped to this world's plan or year.
async function myWork(page: Page, tab: "assigned" | "waiting") {
	await page.goto("/app/my-work", { waitUntil: "domcontentloaded" });
	await page.locator(`[data-tab="${tab}"]`).click();
	return page.locator(".kt-mw-row");
}

test.describe("Over budget: the Planner asks, the Budget Officer decides", () => {
	test.afterAll(() => restoreSite());

	test("request, wait, decline, and the Planner's way forward", async ({ page }) => {
		const state = resetFixture<OverBudget>("reset_update_over_budget_fixture");
		const errors = collectConsoleErrors(page);

		// 1. The Planner meets the blocked update and asks for the revision.
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		const block = page.locator(".kt-next-step-block");
		await expect(block).toContainText("Over budget by KES 2,000,000");
		await expect(page.locator(".kt-journey-stage.is-blocked")).toContainText("Preparation");
		await block.getByRole("button", { name: /^Request budget revision from / }).click();

		// 2. It waits on the Budget Officer, named, in place — and after a reload.
		const line = page.locator(".kt-page-head .kt-next-step");
		await expect(line).toContainText("(Budget Officer) to revise the budget line");
		await expect(block).toHaveCount(0);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(line).toContainText("(Budget Officer) to revise the budget line");
		let rows = await myWork(page, "waiting");
		await expect(rows.filter({ hasText: "Waiting for the budget revision" }).filter({ hasText: state.plan_reference })).toHaveCount(1);
		await expect(rows.filter({ hasText: "Waiting for the budget revision" }).filter({ hasText: state.plan_reference })).toContainText("Preparation");

		// 3. The Budget Officer: the item in My Work, the row on the workspace,
		// and the decline with a reason.
		await login(page, BUDGET_OFFICER, PASSWORD);
		rows = await myWork(page, "assigned");
		await expect(rows.filter({ hasText: "for the plan update" }).filter({ hasText: FY })).toHaveCount(1);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		const fy = page.locator('[data-testid="budget-fy-filter"]').first();
		await expect(fy).toBeVisible();
		await fy.selectOption(FY);
		const request = page.locator('[data-testid="budget-revision-request"]');
		await expect(request).toHaveCount(1);
		await expect(request).toContainText("so it is over by KES 2,000,000");
		await request.locator('[data-testid="budget-revision-decline"]').click();
		const dialog = page.locator('[data-testid="budget-decline-dialog"]');
		const confirm = dialog.locator('[data-testid="budget-decline-confirm"]');
		await expect(confirm).toBeDisabled();
		await dialog.locator('[data-testid="budget-decline-reason"]').fill("No further allocation is available on this line this year.");
		await expect(confirm).toBeEnabled();
		await confirm.click();
		await expect(dialog).toHaveCount(0);
		await expect(request).toHaveCount(0);

		// 4. The Planner: blocked again with the decline, its reason and the
		// departmental path leading — no second budget request on the same
		// amounts (owner decision 26 Sep 2026) — and the outcome as their own
		// My Work item.
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(block).toContainText("Over budget by KES 2,000,000");
		await expect(block).toContainText("No further allocation is available on this line this year.");
		await expect(block.getByRole("button", { name: /^Request departmental plan update from / })).toHaveClass(/kt-btn-primary/);
		await expect(block.getByRole("button", { name: /^Request budget revision/ })).toHaveCount(0);
		rows = await myWork(page, "assigned");
		await expect(rows.filter({ hasText: "Continue plan update" }).filter({ hasText: state.plan_reference })).toHaveCount(1);
		rows = await myWork(page, "waiting");
		await expect(rows.filter({ hasText: "Waiting for the budget revision" }).filter({ hasText: state.plan_reference })).toHaveCount(0);

		// 5. The departmental correction route (owner decision 26 Sep 2026):
		// the Planner asks the department, waits on it by name, and the
		// department finds the request in My Work and on its own plan.
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await block.getByRole("button", { name: /^Request departmental plan update from / }).click();
		await expect(line).toContainText(`Waiting for ${OU_NAME} to update its departmental plan`);
		await expect(page.locator(".kt-journey-stage").first()).toContainText(OU_NAME);
		rows = await myWork(page, "waiting");
		await expect(rows.filter({ hasText: "Waiting for the departmental plan update" }).filter({ hasText: state.plan_reference })).toHaveCount(1);

		await login(page, AUTHOR, PASSWORD);
		rows = await myWork(page, "assigned");
		const ask = rows.filter({ hasText: `Update ${OU_NAME} departmental plan` }).filter({ hasText: "over budget by KES 2,000,000" });
		await expect(ask).toHaveCount(1);
		await ask.locator("[data-open]").click();
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="pln-dpp-update-request"]')).toContainText("is over by KES 2,000,000");
		await expect(page.locator(".kt-page-head .kt-next-step")).toContainText("Update this plan as Procurement asked");
		await expect(page.locator('[data-testid="pln-dpp-create-update"]')).toBeVisible();

		expect(errors, "console errors").toEqual([]);
	});
});
