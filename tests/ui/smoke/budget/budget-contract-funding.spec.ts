import { test, expect, Page } from "@playwright/test";
import { APPROVER, AUDITOR, NOBODY, OFFICER, bench, collectConsoleErrors, confirmDecision, gotoBudget, login, selectYear, purgeWhenDone } from "./helpers";

/**
 * BUD-CHG-001 v1.16 §11.22 — BUD-DES-21 Contract funding and BUD-DES-22 Review contract funding, with their variants
 * (BUD25-AC-008, -009, -012; CM-AC-89, -94). The fixture is the document's: contract CM-MOH-2027-EXT-001, Afya Digital Supplies
 * Limited; confirmed charge KES 600,000; real Budget coverage KES 100,000; so KES 500,000 is new, over two Entity-wide lines of the
 * same year (Hardware and IT equipment 300,000, IT support equipment 200,000). The roles are the normal ones: Josphat Mwangi
 * prepares, Beatrice Kamau decides, the Auditor reads, Samuel Otieno holds nothing.
 */
purgeWhenDone();
test.describe.configure({ mode: "serial" });

const FIXTURES = "kentender_budget.seeds.funding_ui_fixtures";
const HWD = "Hardware and IT equipment";
const SUPPORT = "IT support equipment";
const RECONCILIATION = "Existing funding checked against the confirmed current-year charge.";

interface FundingFixture {
	budget: string;
	budget_code: string;
	fiscal_year: string;
	request: string;
	entry?: string;
	hwd_line: string;
	support_line: string;
	contract: string;
}

function reset(variant: string): FundingFixture {
	const output = bench(`execute ${FIXTURES}.reset_contract_funding --kwargs '{"variant": "${variant}"}'`);
	return JSON.parse(output.trim().split("\n").pop() || "{}") as FundingFixture;
}

async function expectFunding(page: Page): Promise<void> {
	await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute("data-screen", "funding", { timeout: 30_000 });
	const el = page.locator('[data-testid="bud-funding"]');
	await expect(el).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
	await expect(el).toHaveAttribute("data-refreshing", "false", { timeout: 30_000 });
}

async function open(page: Page, fx: FundingFixture): Promise<void> {
	await gotoBudget(page, `/funding/${fx.request}`);
	await expectFunding(page);
}

test("the Officer finds the contract in the work list, allocates the new charge to two lines, keeps a draft through a refresh and submits", async ({ page }) => {
	const fx = reset("ready");
	const errors = collectConsoleErrors(page);
	await login(page, OFFICER);
	await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
	await selectYear(page, fx.fiscal_year);
	await gotoBudget(page);
	const work = page.getByTestId("budget-funding-work");
	await expect(work).toContainText("Fund existing contract", { timeout: 30_000 });
	await expect(work).toContainText("CM-MOH-2027-EXT-001");
	await expect(page.getByTestId("budget-funding-work-status")).toHaveText("Ready to prepare");
	await page.getByTestId("budget-funding-work-open").click();
	await expectFunding(page);

	await expect(page.getByTestId("bud-funding-status")).toHaveText("Ready to prepare");
	await expect(page.getByTestId("bud-funding-next")).toContainText("Your turn — Allocate KES 500,000 to budget lines");
	await expect(page.getByTestId("bud-funding-charge")).toHaveText("KES 600,000");
	await expect(page.getByTestId("bud-funding-covered")).toHaveText("KES 100,000");
	await expect(page.getByTestId("bud-funding-required")).toHaveText("KES 500,000");
	await expect(page.getByTestId("bud-funding-submit")).toBeEnabled(); // the server, not the browser, refuses an allocation that does not add up (next test)

	await page.getByTestId("bud-funding-add").click();
	await page.getByTestId("bud-funding-add").click();
	await page.getByTestId("bud-funding-line").nth(0).selectOption({ label: HWD });
	await page.getByTestId("bud-funding-line").nth(1).selectOption({ label: SUPPORT });
	await page.getByTestId("bud-funding-amount").nth(0).fill("300000");
	await page.getByTestId("bud-funding-amount").nth(1).fill("200000");
	await page.getByTestId("bud-funding-recon").fill(RECONCILIATION);
	await expect(page.getByTestId("bud-funding-total")).toContainText("KES 500,000");
	await expect(page.getByTestId("bud-funding-remaining")).toContainText("KES 0");

	await page.getByTestId("bud-funding-save").click();
	await expect(page.getByTestId("bud-funding-entry-state")).toHaveText("Draft", { timeout: 30_000 });
	await page.reload({ waitUntil: "domcontentloaded" });
	await expectFunding(page);
	await expect(page.getByTestId("bud-funding-row")).toHaveCount(2);
	await expect(page.getByTestId("bud-funding-total")).toContainText("KES 500,000");
	await expect(page.getByTestId("bud-funding-recon")).toHaveValue(RECONCILIATION);

	await page.getByTestId("bud-funding-submit").click();
	await expect(page.getByTestId("bud-funding-entry-state")).toHaveText("Awaiting approval", { timeout: 30_000 });
	await expect(page.getByTestId("bud-funding-next")).toContainText("Budget Approver");
	await expect(page.getByTestId("bud-funding-amount")).toHaveCount(0);
	await expect(page.getByTestId("bud-funding-submit")).toHaveCount(0);
	expect(errors).toEqual([]);
});

test("rows that do not add up are refused with the difference, and nothing is submitted", async ({ page }) => {
	const fx = reset("ready");
	await login(page, OFFICER);
	await open(page, fx);
	await page.getByTestId("bud-funding-add").click();
	await page.getByTestId("bud-funding-line").nth(0).selectOption({ label: HWD });
	await page.getByTestId("bud-funding-amount").nth(0).fill("300000");
	await page.getByTestId("bud-funding-recon").fill(RECONCILIATION);
	await expect(page.getByTestId("bud-funding-remaining")).toContainText("KES 200,000");
	await page.getByTestId("bud-funding-submit").click();
	await expect(page.getByTestId("bud-funding-rows-error")).toContainText("must add up to the amount requiring funding", { timeout: 30_000 });
	await expect(page.getByTestId("bud-funding-submit")).toBeVisible(); // still the Officer's turn: nothing went to review
	await expect(page.getByTestId("bud-funding-entry-state")).toHaveCount(0);
});

test("the Approver reviews the frozen entry, approves it after a confirmation that repeats the total, and the lines show the new commitments", async ({ page }) => {
	const fx = reset("submitted");
	const errors = collectConsoleErrors(page);
	await login(page, APPROVER);
	await open(page, fx);
	await expect(page.getByTestId("bud-funding-header")).toContainText("Review contract funding");
	await expect(page.getByTestId("bud-funding-next")).toContainText("Your turn — Review the funding entry");
	await expect(page.getByTestId("bud-funding-amount")).toHaveCount(0);
	await expect(page.getByTestId("bud-funding-row")).toHaveCount(2);
	await expect(page.getByTestId("bud-funding-submitter")).toContainText("Josphat");
	await expect(page.getByTestId("bud-funding-approve")).toBeEnabled();

	await page.getByTestId("bud-funding-approve").click();
	const dialog = page.getByTestId("kt-confirm-dialog");
	await expect(dialog).toContainText("KES 500,000");
	await expect(dialog).toContainText(HWD);
	await expect(dialog).toContainText(SUPPORT);
	await confirmDecision(page, "Approve funding entry");
	await expect(page.getByTestId("bud-funding-approved")).toContainText("Funding entry approved", { timeout: 30_000 });
	await expect(page.getByTestId("bud-funding-status")).toHaveText("Funding entry approved");
	await expect(page.getByTestId("bud-funding-approve")).toHaveCount(0);
	await page.reload({ waitUntil: "domcontentloaded" });
	await expectFunding(page);
	await expect(page.getByTestId("bud-funding-approved")).toBeVisible();

	await gotoBudget(page, `/line/${fx.hwd_line}`);
	await expect(page.getByTestId("bud-line-position-cards")).toContainText("KES 400,000", { timeout: 30_000 });
	await expect(page.getByTestId("bud-line-position-cards")).toContainText("KES 600,000");
	await expect(page.getByTestId("bud-line-commitment")).toHaveCount(2);
	await gotoBudget(page, `/line/${fx.support_line}`);
	await expect(page.getByTestId("bud-line-position-cards")).toContainText("KES 200,000", { timeout: 30_000 });
	await expect(page.getByTestId("bud-line-position-cards")).toContainText("KES 800,000");
	expect(errors).toEqual([]);
});

test("the Approver returns the entry with a reason and the Officer corrects and resubmits it", async ({ page }) => {
	const fx = reset("submitted");
	await login(page, APPROVER);
	await open(page, fx);
	await page.getByTestId("bud-funding-return").click();
	await expect(page.getByTestId("kt-confirm-ok")).toBeDisabled();
	await page.getByTestId("kt-confirm-dialog").locator("textarea").fill("Confirm the source allocation");
	await page.getByTestId("kt-confirm-ok").click();
	await expect(page.getByTestId("bud-funding-status")).toHaveText("Returned", { timeout: 30_000 });

	await login(page, OFFICER);
	await open(page, fx);
	await expect(page.getByTestId("bud-funding-returned")).toContainText("Confirm the source allocation");
	await expect(page.getByTestId("bud-funding-amount")).toHaveCount(2);
	await expect(page.getByTestId("bud-funding-submit")).toBeEnabled();
	await page.getByTestId("bud-funding-submit").click();
	await expect(page.getByTestId("bud-funding-entry-state")).toHaveText("Awaiting approval", { timeout: 30_000 });
});

test("a shortfall on one line leaves no commitment, names the shortfall and puts the entry back with the Officer", async ({ page }) => {
	const fx = reset("shortfall");
	await login(page, OFFICER);
	await open(page, fx);
	await expect(page.getByTestId("bud-funding-status")).toHaveText("Funding shortfall");
	await expect(page.getByTestId("bud-funding-returned")).toContainText("Funding shortfall");
	await expect(page.getByTestId("bud-funding-returned")).toContainText("50000");
	await expect(page.getByTestId("bud-funding-amount")).toHaveCount(2);
	await gotoBudget(page, `/line/${fx.hwd_line}`);
	await expect(page.getByTestId("bud-line-position-cards")).toContainText("KES 100,000", { timeout: 30_000 });
	await expect(page.getByTestId("bud-line-commitment")).toHaveCount(1);
});

test("a changed opening review cannot be approved: the Approver is told to return the entry", async ({ page }) => {
	const fx = reset("changed_basis");
	await login(page, APPROVER);
	await open(page, fx);
	await expect(page.getByTestId("bud-funding-basis-changed")).toContainText("The opening review has changed. Return this entry for an updated allocation.");
	await expect(page.getByTestId("bud-funding-approve")).toBeDisabled();
	await expect(page.getByTestId("bud-funding-return")).toBeEnabled();
});

test("without Finance's year basis the request waits: Year allocation required, submit waits, the draft still saves", async ({ page }) => {
	const fx = reset("missing_basis");
	await login(page, OFFICER);
	await open(page, fx);
	await expect(page.getByTestId("bud-funding-status")).toHaveText("Year allocation required");
	await expect(page.getByTestId("bud-funding-waiting")).toContainText("Year allocation required");
	await expect(page.getByTestId("bud-funding-submit")).toBeDisabled();
	await expect(page.getByTestId("bud-funding-open-contract")).toBeVisible();
	await page.getByTestId("bud-funding-add").click();
	await page.getByTestId("bud-funding-line").nth(0).selectOption({ label: HWD });
	await page.getByTestId("bud-funding-save").click();
	await expect(page.getByTestId("bud-funding-entry-state")).toHaveText("Draft", { timeout: 30_000 });
	await page.reload({ waitUntil: "domcontentloaded" });
	await expectFunding(page);
	await expect(page.getByTestId("bud-funding-row")).toHaveCount(1);
	await expect(page.getByTestId("bud-funding-submit")).toBeDisabled();
});

test("when Budget already covers the whole charge the request is complete: Already covered, no entry to prepare", async ({ page }) => {
	const fx = reset("already_covered");
	await login(page, OFFICER);
	await open(page, fx);
	await expect(page.getByTestId("bud-funding-closed")).toContainText("Already covered — no new entry required");
	await expect(page.getByTestId("bud-funding-allocation")).toHaveCount(0);
	await expect(page.getByTestId("bud-funding-submit")).toHaveCount(0);
});

test("funding outside the supported scope says so and invents nothing", async ({ page }) => {
	const fx = reset("scope");
	await login(page, OFFICER);
	await open(page, fx);
	await expect(page.getByTestId("bud-funding-scope")).toContainText("This funding is outside the supported scope");
	await expect(page.getByTestId("bud-funding-submit")).toHaveCount(0);
});

test("the Auditor reads the request with no editor or decision, and a person with no Budget responsibility is refused", async ({ page }) => {
	const fx = reset("submitted");
	await login(page, AUDITOR);
	await open(page, fx);
	await expect(page.getByTestId("bud-funding-row")).toHaveCount(2);
	for (const id of ["bud-funding-amount", "bud-funding-approve", "bud-funding-return", "bud-funding-save", "bud-funding-submit", "bud-funding-decline"]) {
		await expect(page.getByTestId(id)).toHaveCount(0);
	}
	await login(page, NOBODY);
	await gotoBudget(page, `/funding/${fx.request}`);
	await expect(page.getByTestId("bud-funding-forbidden")).toBeVisible({ timeout: 30_000 });
	await expect(page.locator(".modal.show")).toHaveCount(0);
});
