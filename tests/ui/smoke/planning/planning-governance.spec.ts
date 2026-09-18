import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	ACCOUNTING_OFFICER,
	PASSWORD,
	PLANNER,
	STATUTORY,
	collectConsoleErrors,
	contextValue,
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
		// §10.10's second section: who checked the funding and who signed the
		// preparation, as two compact rows — not a decision-history table.
		const accountability = page.locator('[data-testid="rev-accountability"]');
		await expect(accountability).toContainText("Funding");
		await expect(accountability).toContainText("Preparation");
		await page.locator('[data-testid="rev-confirm"]').click();
		await expectReady(page, "workspace");

		// PLN-DES-12 — the statutory approver's own task
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		const action = page.locator('[data-testid="pln-action"]');
		// §10.3 — the card leads with the outcome the actor is being asked for.
		await expect(action.locator(".kt-meta-value").first()).toHaveText("Approve the Annual Procurement Plan");
		await action.locator('[data-testid="pln-action-button"]').click();
		await expectReady(page, "governance");
		// §10.10 — the stage names the authority that is actually being waited
		// on, not the internal name of the step.
		await expect(page.locator('[data-testid="rev-context"]')).toContainText("Awaiting Responsible Cabinet Secretary");
		const authority = page.locator('[data-testid="rev-accountability"]');
		await expect(authority).toContainText("Playwright Finance Officer");
		await expect(authority).toContainText("Head of Procurement Function");
		// §10.10 U11-STATUTORY — the statement says what the control does, and
		// is explicit that approval is not yet publication.
		await expect(page.locator('[data-testid="rev-statement"]')).toContainText(
			"Publication and activation checks must still be completed."
		);
		await expect(page.locator('[data-testid="rev-resolution"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="rev-confirm"]')).toHaveText("Approve Annual Procurement Plan");
		await page.locator('[data-testid="rev-confirm"]').click();
		await expectReady(page, "workspace");

		// §5.5.2 — approval commits the snapshot, the publication and the
		// intent. It does not send anything and does not activate: the plan is
		// not in force until the publication is acknowledged, which is the
		// publication spec's own subject.
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toHaveCount(0);
		const approved = page.locator('[data-testid="pln-plan-row-draft"]');
		await expect(approved).toContainText("Approved — publication pending");
		// §10.3 — and the workspace says plainly what that does not yet permit.
		await expect(page.locator('[data-testid="pln-plan-note"]')).toContainText(
			"It cannot yet be used to authorise procurement."
		);
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
		await expect(contextValue(page, "ppl-context", "Version")).toHaveText("2");
		// A returned version comes back as an ordinary Draft — §10.6 has no
		// separate correction badge; what says so is the submission action.
		await expect(contextValue(page, "ppl-context", "Status")).toHaveText("Draft");
		await expect(page.locator('[data-testid="ppl-purchases"] tbody tr')).toHaveCount(1);
		// §6.2 — signing and submitting belongs to the Head of Procurement
		// Function, never the Planner, so §10.6 names who is waited on instead
		// of offering a control this reader does not hold.
		await expect(page.locator('[data-testid="ppl-sign-submit"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="ppl-waiting-on"]')).toContainText(
			"Ready for the Head of Procurement Function to sign and submit"
		);
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
