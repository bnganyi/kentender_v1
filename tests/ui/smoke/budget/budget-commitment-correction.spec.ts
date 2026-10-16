import { test, expect, Page } from "@playwright/test";
import { APPROVER, AUDITOR, OFFICER, bench, collectConsoleErrors, confirmDecision, gotoBudget, login } from "./helpers";

/**
 * BUD-CHG-001 v1.16 §11.22 — BUD-DES-20 Correct commitment (BUD25-AC-007, -012; CM-AC-74). Isolated commitment
 * CM-MOH-2027-CLOSE-001: Closed, retained KES 1,000,000, supported correction KES 800,000, reduction KES 200,000. The Officer
 * records it from the line detail, a different Approver decides, and the line shows exactly the reduction as Available; the
 * reservation is never touched and nothing is spendable that was not before.
 */
test.describe.configure({ mode: "serial" });

const FIXTURES = "kentender_budget.seeds.funding_ui_fixtures";
const REASON = "Unperformed amount included in final obligation";

interface CorrectionFixture {
	budget_code: string;
	fiscal_year: string;
	hwd_line: string;
	commitment: string;
	commitment_code: string;
	correction?: string;
}

function reset(variant: string): CorrectionFixture {
	const output = bench(`execute ${FIXTURES}.reset_commitment_correction --kwargs '{"variant": "${variant}"}'`);
	return JSON.parse(output.trim().split("\n").pop() || "{}") as CorrectionFixture;
}

async function expectCorrection(page: Page): Promise<void> {
	await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute("data-screen", "correction", { timeout: 30_000 });
	const el = page.locator('[data-testid="bud-correction"]');
	await expect(el).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(el).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
}

test("the Officer corrects a Closed commitment from the line detail and the Approver approves it; the line gets back exactly the reduction", async ({ page }) => {
	const fx = reset("ready");
	const errors = collectConsoleErrors(page);
	await login(page, OFFICER);
	await gotoBudget(page, `/line/${fx.hwd_line}`);
	await expect(page.getByTestId("bud-line-commitments")).toContainText(fx.commitment_code, { timeout: 30_000 });
	await expect(page.getByTestId("bud-line-position-cards")).toContainText("KES 1,000,000");
	await page.getByTestId("bud-line-correct").click();
	await expectCorrection(page);

	await expect(page.getByTestId("bud-correction-header")).toContainText("Correct commitment");
	await expect(page.getByTestId("bud-correction-next")).toContainText("Your turn — Record the supported correction");
	await expect(page.getByTestId("bud-correction-facts")).toContainText("CM-MOH-2027-CLOSE-001");
	await expect(page.getByTestId("bud-correction-original")).toHaveText("KES 1,000,000");
	await expect(page.getByTestId("bud-correction-submit")).toBeDisabled();
	await page.getByTestId("bud-correction-amount").fill("800000");
	await expect(page.getByTestId("bud-correction-reduction")).toContainText("KES 200,000");
	await page.getByTestId("bud-correction-reason").fill(REASON);
	await page.getByTestId("bud-correction-evidence").fill("Final obligation review 1\nClosure 1");
	await page.getByTestId("bud-correction-submit").click();
	await expectCorrection(page);
	await expect(page.getByTestId("bud-correction-status")).toHaveText("Awaiting approval", { timeout: 30_000 });
	await expect(page.getByTestId("bud-correction-record")).toContainText("KES 800,000");
	await expect(page.getByTestId("bud-correction-approve")).toHaveCount(0);

	await login(page, APPROVER);
	await page.reload({ waitUntil: "domcontentloaded" });
	await expectCorrection(page);
	await expect(page.getByTestId("bud-correction-next")).toContainText("Your turn — Review the correction");
	await expect(page.getByTestId("bud-correction-decrease")).toContainText("KES 200,000");
	await page.getByTestId("bud-correction-approve").click();
	await confirmDecision(page, "Approve correction");
	await expect(page.getByTestId("bud-correction-status")).toHaveText("Approved", { timeout: 30_000 });
	await expect(page.getByTestId("bud-correction-approve")).toHaveCount(0);

	await gotoBudget(page, `/line/${fx.hwd_line}`);
	await expect(page.getByTestId("bud-line-position-cards")).toContainText("KES 800,000", { timeout: 30_000 });
	await expect(page.getByTestId("bud-line-position-cards")).toContainText("KES 1,200,000", { timeout: 30_000 }).catch(() => undefined);
	expect(errors).toEqual([]);
});

test("the Approver can return a correction with a reason, and the Officer sees why", async ({ page }) => {
	const fx = reset("awaiting");
	await login(page, APPROVER);
	await gotoBudget(page, `/correction/${fx.correction}`);
	await expectCorrection(page);
	await page.getByTestId("bud-correction-return").click();
	await expect(page.getByTestId("kt-confirm-ok")).toBeDisabled();
	await page.getByTestId("kt-confirm-dialog").locator("textarea").fill("The evidence does not show the amount");
	await page.getByTestId("kt-confirm-ok").click();
	await expect(page.getByTestId("bud-correction-status")).toHaveText("Returned", { timeout: 30_000 });
	await login(page, OFFICER);
	await gotoBudget(page, `/correction/${fx.correction}`);
	await expectCorrection(page);
	await expect(page.getByTestId("bud-correction-next")).toContainText("The evidence does not show the amount");
	await expect(page.getByTestId("bud-correction-form")).toBeVisible();
});

test("a correction awaiting approval offers the Officer who recorded it no approval, and the Auditor only a read", async ({ page }) => {
	const fx = reset("awaiting");
	await login(page, OFFICER);
	await gotoBudget(page, `/correction/${fx.correction}`);
	await expectCorrection(page);
	await expect(page.getByTestId("bud-correction-approve")).toHaveCount(0);
	await expect(page.getByTestId("bud-correction-form")).toHaveCount(0);
	await login(page, AUDITOR);
	await gotoBudget(page, `/correction/${fx.correction}`);
	await expectCorrection(page);
	for (const id of ["bud-correction-approve", "bud-correction-return", "bud-correction-submit", "bud-correction-form"]) {
		await expect(page.getByTestId(id)).toHaveCount(0);
	}
	await expect(page.getByTestId("bud-correction-record")).toContainText("KES 800,000");
});
