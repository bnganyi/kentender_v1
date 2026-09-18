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

// Sequential, but not serial: these run on one worker because the fixtures
// are one shared world, and each test rebuilds its own. Aborting the rest of
// the file because one test failed hides every other result behind it.
test.describe.configure({ timeout: 180_000 });

test.describe("PLN-UI-11/12 Annual Plan decisions", () => {
	test.afterAll(() => restoreSite());

	test("the Accounting Officer adopts, the statutory approver approves, and the Plan activates", async ({ page }) => {
		const state = resetFixture<GovernanceState>("reset_governance_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");

		// PLN-DES-11 exact composition from the immutable snapshot
		await expect(page.locator('[data-testid="rev-context"]')).toContainText("Awaiting Accounting Officer");
		const row = page.locator('[data-testid="rev-purchase-row"]');
		await expect(row).toHaveCount(1);
		await expect(row).toContainText("Digital health infrastructure package");
		await expect(page.locator('[data-testid="rev-caption"]')).toContainText("KES 80,000,000");
		// §10.10 — the decision summary and the checks come before the
		// decision; nothing is expanded, and no advisory has its own line.
		await expect(page.locator('[data-testid="rev-summary"]')).toBeVisible();
		await expect(page.locator('[data-testid="rev-plan-checks"]')).toBeVisible();
		// §10.10 — the statement says what the control does, in the second
		// person, rather than putting words in the decider's mouth.
		await expect(page.locator('[data-testid="rev-statement"]')).toContainText("you adopt the complete plan shown here");
		await expect(page.locator('[data-testid="rev-accountability"]')).toHaveCount(0);
		await page.locator('[data-testid="rev-confirm"]').click();
		await expectReady(page, "workspace");

		// PLN-DES-12 — the statutory approver's own task
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		const action = page.locator('[data-testid="pln-action"]');
		await expect(action.locator(".pln-ready-headline")).toHaveText("Approve the Annual Procurement Plan");
		await action.locator("button").click();
		await expectReady(page, "governance");
		await expect(page.locator('[data-testid="rev-context"]')).toContainText("Awaiting statutory approval");
		const authority = page.locator('[data-testid="rev-accountability"]');
		await expect(authority).toContainText("Cabinet Secretary");
		await expect(authority).toContainText("Playwright Accounting Officer");
		await expect(page.locator('[data-testid="rev-statement"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="rev-resolution"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="rev-confirm"]')).toHaveText("Approve Annual Procurement Plan");
		await page.locator('[data-testid="rev-confirm"]').click();
		await expectReady(page, "workspace");

		// approval published and activated the Plan (§5.2)
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		// §10.3 — the plan in force is its own row, and it offers the progress
		// of what has been procured against it.
		const current = page.locator('[data-testid="pln-plan-row-current"]');
		await expect(current).toContainText("Current plan");
		await expect(page.locator('[data-testid="pln-plan-secondary-current"]')).toHaveText("View procurement progress");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Accounting Officer return preserves the submission and the workbench shows the correction Draft", async ({ page }) => {
		const state = resetFixture<GovernanceState>("reset_governance_fixture");
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		await page.locator('[data-testid="rev-secondary"]').click();
		const dialog = page.locator('[data-testid="rvw-return-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Return Plan Version for correction?");
		await expect(dialog).toContainText("The submitted Version 1 remains unchanged. State the correction required.");
		const confirm = page.locator('[data-testid="rvw-return-confirm"]');
		await expect(confirm).toBeDisabled();
		await page.locator('[data-testid="rvw-return-reason"]').fill("Confirm the planned contract-signing date against the delivery completion date.");
		await expect(confirm).toBeEnabled();
		await confirm.click();
		await expectReady(page, "workspace");

		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="ppl-context"]')).toContainText("Version 2");
		// A returned version comes back as a correction draft, which says so.
		await expect(page.locator('[data-testid="ppl-context"]')).toContainText("Draft update");
		await expect(page.locator('[data-testid="ppl-purchases"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="ppl-sign-submit"]')).toHaveText("Submit corrected Plan");
	});

	test("the statutory return dialog carries its own copy", async ({ page }) => {
		const state = resetFixture<GovernanceState>("reset_statutory_fixture");
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		await page.locator('[data-testid="rev-secondary"]').click();
		const dialog = page.locator('[data-testid="rvw-return-dialog"]');
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
		await expect(page.locator('[data-testid="rev-purchases"]')).toBeVisible();
		await expect(page.locator('[data-testid="rev-confirm"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="rev-secondary"]')).toHaveCount(0);
	});
});
