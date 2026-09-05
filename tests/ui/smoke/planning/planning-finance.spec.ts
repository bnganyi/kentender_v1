import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	FINANCE,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.12 Phase 5 (Slice C) — PLN-UI-10: the one plan-level
 * funding confirmation task over Budget's real `check_plan_affordability`
 * contract, in a real browser. No reservation exists anywhere in this path.
 */

type FinanceState = { task: string; plan_reference: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("PLN-UI-10 Plan funding confirmation", () => {
	test.afterAll(() => restoreSite());

	test("the Finance Confirmation Officer confirms the affordability statement and the workbench reads Confirmed", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");

		// PLN-DES-10 exact composition on the live statement
		await expect(page.locator(".kt-page-kicker")).toHaveText("PLAN FUNDING CONFIRMATION");
		await expect(page.locator('[data-testid="fnt-badge"]')).toHaveText("Awaiting Finance");
		await expect(page.locator('[data-testid="fnt-summary"] label')).toHaveText(["Plan Items", "Plan value", "Procurement Budget Lines used", "Reserved share"]);
		await expect(page.locator('[data-testid="fnt-summary"]')).toContainText("KES 80,000,000");
		await expect(page.locator('[data-testid="fnt-as-at"]')).toContainText("Position as at");
		await expect(page.locator('[data-testid="fnt-as-at"]')).toContainText("EAT");
		const table = page.locator('[data-testid="fnt-affordability"] table');
		await expect(table.locator("thead th")).toHaveText([
			"Procurement Budget Line", "Funding source", "Approved", "Planned in this Plan", "Within approved", "Reserved", "Committed", "Currently available",
		]);
		await expect(page.locator('[data-testid="fnt-line-0"]')).toContainText("Digital health infrastructure programme");
		await expect(page.locator('[data-testid="fnt-line-0"]')).toContainText("KES 100,000,000");
		await expect(page.locator('[data-testid="fnt-line-0"]')).toContainText("Yes");
		await expect(page.locator('[data-testid="fnt-within-approved"]')).toHaveText(
			"The consolidated plan is within the approved budget on every Procurement Budget Line."
		);
		await expect(page.locator('[data-testid="fnt-quiet-line"]')).toContainText("It reserves no funds");
		await expect(page.locator("text=Available after confirmation")).toHaveCount(0);

		await page.locator('[data-testid="fnt-confirm"]').click();
		await expectReady(page, "workspace");

		// the Planner's workbench now reads Confirmed and offers submission
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-readiness-plan-funding-confirmed"] .kt-status')).toHaveText("Confirmed");
		await expect(page.locator('[data-testid="pln-submit-consolidated"]')).toBeEnabled();
		await expect(page.locator('[data-testid="pln-request-funding"]')).toBeDisabled();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("return to planner requires a reason and sends the Version back", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");
		await page.locator('[data-testid="fnt-return"]').click();
		const dialog = page.locator('[data-testid="fnt-return-dialog"]');
		await expect(dialog).toBeVisible();
		const confirm = page.locator('[data-testid="fnt-return-confirm"]');
		await expect(confirm).toBeDisabled();
		await page.locator('[data-testid="fnt-return-reason"]').fill("Reconcile the planned total against the approved line before resubmitting.");
		await expect(confirm).toBeEnabled();
		await confirm.click();
		await expectReady(page, "workspace");

		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-funding-notice"]')).toContainText("Plan funding returned by Finance");
		await expect(page.locator('[data-testid="pln-request-funding"]')).toBeEnabled();
		await expect(page.locator('[data-testid="pln-submit-consolidated"]')).toBeDisabled();
	});

	test("the requesting Planner reads the task without decision controls; a departmental link masks", async ({ page }) => {
		const state = resetFixture<FinanceState>("reset_finance_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");
		await expect(page.locator('[data-testid="fnt-affordability"]')).toBeVisible();
		await expect(page.locator('[data-testid="fnt-confirm"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="fnt-return"]')).toHaveCount(0);
	});
});
