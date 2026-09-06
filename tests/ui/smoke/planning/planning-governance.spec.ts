import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	ACCOUNTING_OFFICER,
	PASSWORD,
	PLANNER,
	STATUTORY,
	collectConsoleErrors,
	expectReady,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.12 Phase 5 (Slice C) — PLN-UI-11/12: Accounting Officer
 * adoption, the statutory approval resolved from the Site Procuring Entity's
 * route, the two PLN-DES-15 return dialogs and the auto-publication that
 * follows approval, in a real browser.
 */

type GovernanceState = { task: string; plan_reference: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("PLN-UI-11/12 Annual Plan decisions", () => {
	test.afterAll(() => restoreSite());

	test("the Accounting Officer adopts, the statutory approver approves, and the Plan activates", async ({ page }) => {
		const state = resetFixture<GovernanceState>("reset_governance_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");

		// PLN-DES-11 exact composition from the immutable snapshot
		await expect(page.locator(".kt-page-kicker")).toContainText("ACCOUNTING OFFICER ADOPTION");
		await expect(page.locator('[data-testid="pgt-badge"]')).toHaveText("Awaiting Accounting Officer");
		await expect(page.locator('[data-testid="pgt-items"] thead th')).toHaveText([
			"Plan Item", "Department", "Source origin", "Quantity", "Strategic Objective", "Method", "Reservation", "Value", "Completion", "Funding",
		]);
		const row = page.locator('[data-testid="pgt-items"] tbody tr');
		await expect(row).toHaveCount(1);
		await expect(row).toContainText("Digital health infrastructure package");
		await expect(row).toContainText("Open Tender");
		await expect(row.locator(".kt-status")).toHaveText("Within budget");
		await expect(page.locator('[data-testid="pgt-caption"]')).toHaveText("1 Plan Item · KES 80,000,000");
		await expect(page.locator('[data-testid="pgt-advisory-line"]')).toContainText("No contract splitting advisory.");
		await expect(page.locator('[data-testid="pgt-statement"]')).toContainText("I adopt the complete consolidated Annual Procurement Plan Version 1");
		await expect(page.locator('[data-testid="pgt-authority"]')).toHaveCount(0);
		await page.locator('[data-testid="pgt-confirm"]').click();
		await expectReady(page, "workspace");

		// PLN-DES-12 — the statutory approver's own task
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		const action = page.locator('[data-testid="pln-action-row"]');
		await expect(action.locator(".pln-ready-headline")).toHaveText("Approve the Annual Procurement Plan");
		await action.locator("button").click();
		await expectReady(page, "governance");
		await expect(page.locator(".kt-page-kicker")).toContainText("STATUTORY APPROVAL");
		await expect(page.locator('[data-testid="pgt-badge"]')).toHaveText("Awaiting statutory approval");
		const authority = page.locator('[data-testid="pgt-authority"]');
		await expect(authority.locator("label")).toHaveText(["Capacity", "Accounting Officer adoption"]);
		await expect(authority).toContainText("Cabinet Secretary");
		await expect(authority).toContainText("Playwright Accounting Officer");
		await expect(page.locator('[data-testid="pgt-statement"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pgt-resolution"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pgt-confirm"]')).toHaveText("Approve Annual Procurement Plan");
		await page.locator('[data-testid="pgt-confirm"]').click();
		await expectReady(page, "workspace");

		// approval published and activated the Plan (§5.2)
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-plan-summary"]')).toHaveText("· Annual Plan · Active Version 1");
		await expect(page.locator('[data-testid="pln-schedule-health"]')).toHaveText("· 0 of 1 item behind baseline");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Accounting Officer return preserves the submission and the workbench shows the correction Draft", async ({ page }) => {
		const state = resetFixture<GovernanceState>("reset_governance_fixture");
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		await page.locator('[data-testid="pgt-return"]').click();
		const dialog = page.locator('[data-testid="pgt-return-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Return Plan Version for correction?");
		await expect(dialog).toContainText("The submitted Version 1 remains unchanged. State the correction required.");
		const confirm = page.locator('[data-testid="pgt-return-confirm"]');
		await expect(confirm).toBeDisabled();
		await page.locator('[data-testid="pgt-return-reason"]').fill("Confirm the planned contract-signing date against the delivery completion date.");
		await expect(confirm).toBeEnabled();
		await confirm.click();
		await expectReady(page, "workspace");

		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator(".pln-quiet-ref")).toContainText("Version 2");
		await expect(page.locator('[data-testid="pln-plan-badge"]')).toHaveText("Draft");
		await expect(page.locator('[data-testid="pln-plan-items"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="pln-submit-consolidated"]')).toHaveText("Submit corrected Plan");
	});

	test("the statutory return dialog carries its own copy", async ({ page }) => {
		const state = resetFixture<GovernanceState>("reset_statutory_fixture");
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		await page.locator('[data-testid="pgt-return"]').click();
		const dialog = page.locator('[data-testid="pgt-return-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Return adopted Plan Version for correction?");
		await expect(dialog).toContainText("The Accounting-Officer-adopted Version 1 remains unchanged. State the correction required.");
		await expect(dialog.locator("label")).toHaveText(["Correction required"]);
		await expect(dialog.locator("textarea")).toHaveCount(1);
	});

	test("a Planner's deep link to the governance review route reads without decision controls", async ({ page }) => {
		const state = resetFixture<GovernanceState>("reset_governance_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		await expect(page.locator('[data-testid="pgt-items"]')).toBeVisible();
		await expect(page.locator('[data-testid="pgt-confirm"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pgt-return"]')).toHaveCount(0);
	});
});
