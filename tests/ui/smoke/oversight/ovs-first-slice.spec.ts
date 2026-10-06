import { expect, Page, test } from "@playwright/test";

import { login } from "../../helpers/auth";

/**
 * OVS-CHG-001 v0.6 plan Phases 6–8 — the first slice, driven as the canonical personas on the
 * canonical Tender (TND-MOH-2027-002: four bids, a delivered report with review state With Award,
 * an Award case at the Opinion stage). Read-only: nothing is written, so no world is reset.
 * Run on the test site: scripts/test-site.sh run npx playwright test tests/ui/smoke/oversight --workers=1
 *
 * Acceptance: OVS-AC-003, 004–007, 008, 010–012, 016 (the browser half).
 */
test.describe.configure({ mode: "serial", timeout: 180_000 });

const PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";
const AMINA = "amina.hassan@moh.example.test"; // Accounting Officer
const CHARLES = "charles.mutiso@moh.example.test"; // Head of Procurement Function
const NAOMI = "naomi.chebet@moh.example.test"; // Auditor
const PETER = "peter.kimani@moh.example.test"; // Head of User Department (Human Resources Management and Development contributes)
const DANIEL = "daniel.otieno@moh.example.test"; // Technical Operator
const AWARD = "AWD-MOH-2027-002";
const ESTHER = "esther.muthoni@moh.example.test"; // Strategy Author: no procurement responsibility
const TENDER = "TND-MOH-2027-002";
const BIDDERS = ["Afya Digital Supplies Limited", "Jirani Office Supplies Limited", "Pwani Tech Distributors Limited", "Mlima Computer Solutions Limited"];

async function gotoDesk(page: Page, route: string) {
	await page.goto(`/desk/${route}`, { waitUntil: "domcontentloaded" });
}
const evl = (page: Page) => page.locator('[data-testid="evl-host"]');

test.describe("the Accounting Officer after the report is delivered", () => {
	test("reads the decision, the four-bid comparison and the report, with no bid to review", async ({ page }) => {
		await login(page, AMINA, PASSWORD);
		await gotoDesk(page, `tenders/${TENDER}/evaluation`);
		await expect(evl(page)).toContainText("The committee report was sent to Charles Mutiso on 16 Jun 2027, 14:07 EAT.", { timeout: 60_000 });
		const comparison = evl(page).locator('[data-testid="evl-comparison"]');
		for (const bidder of BIDDERS) await expect(comparison).toContainText(bidder);
		await expect(evl(page)).toContainText("Recommendation: Afya Digital Supplies Limited");
		await expect(evl(page)).not.toContainText("Review bid"); // an overseeing reader reviews no bid
		await expect(evl(page)).not.toContainText("Return for correction"); // and holds no recipient action
		await expect(evl(page)).not.toContainText("Report delivered"); // the old setup-only line
	});

	test("opens the report: summary, sections and the three signatures", async ({ page }) => {
		await login(page, AMINA, PASSWORD);
		await gotoDesk(page, `tenders/${TENDER}/evaluation`);
		await evl(page).getByRole("button", { name: "View report" }).click({ timeout: 60_000 });
		await expect(page).toHaveURL(new RegExp(`/desk/tenders/${TENDER}/evaluation/report`));
		await expect(evl(page)).toContainText("Evaluation report 1");
		await expect(evl(page)).toContainText("Afya Digital Supplies Limited");
		for (const member of ["Grace Wambui", "Peter Mugo", "Ruth Achieng"]) await expect(evl(page)).toContainText(member);
		await expect(evl(page)).not.toContainText("Return for correction");
	});

	test("reads the committee record: sessions, the clarification and the committee's outcome", async ({ page }) => {
		await login(page, AMINA, PASSWORD);
		await gotoDesk(page, `tenders/${TENDER}/evaluation/record`);
		await expect(evl(page)).toContainText("Sessions", { timeout: 60_000 });
		await expect(evl(page)).toContainText("Committee outcome");
		await expect(evl(page)).toContainText("Brian Wafula");
	});

	test("a bid-level address stays closed to the offices: the live bid screen is Not found", async ({ page }) => {
		await login(page, AMINA, PASSWORD);
		const answer = await page.request.get(`/api/method/kentender_procurement.bid_evaluation.api.get_bid?tender_reference=${TENDER}&bid=NO-SUCH-BID`);
		expect([403, 404]).toContain(answer.status());
	});
});

test.describe("Decisions and progress on the Tender record", () => {
	test("the Head of Procurement Function sees three stages, each with the owner's record, and no header buttons", async ({ page }) => {
		await login(page, CHARLES, PASSWORD);
		await gotoDesk(page, `tenders/${TENDER}`);
		const section = page.locator('[data-testid="tnd-decisions-progress"]');
		await expect(section).toBeVisible({ timeout: 60_000 });
		await expect(section.locator("h2")).toHaveText("Decisions and progress");
		await expect(section.locator(".tnd-stage")).toHaveCount(3);
		await expect(page.locator('[data-testid="tnd-stage-bid-evaluation"]')).toContainText("Afya Digital Supplies Limited");
		await expect(page.locator('[data-testid="tnd-stage-bid-evaluation"]')).toContainText("KES 46,400,000.00");
		await expect(page.locator('[data-testid="tnd-stage-bid-opening"]')).toContainText("Bids opened");
		await expect(page.locator('[data-testid="tnd-stage-award"]')).toContainText("is preparing the professional opinion");
		await expect(page.locator("[data-testid^='tnd-link-']")).toHaveCount(0); // each header link gave way to its block
		await page.locator('[data-testid="tnd-stage-bid-evaluation-view-record"]').click();
		await expect(page).toHaveURL(new RegExp(`/desk/tenders/${TENDER}/evaluation$`));
		await page.goBack();
		await expect(section).toBeVisible({ timeout: 60_000 }); // back lands on the same record, with its section
	});

	test("a Head of User Department sees a summary: the decision and its reason, no report link, no opening record", async ({ page }) => {
		await login(page, PETER, PASSWORD);
		await gotoDesk(page, `tenders/${TENDER}`);
		const evaluation = page.locator('[data-testid="tnd-stage-bid-evaluation"]');
		await expect(evaluation).toBeVisible({ timeout: 60_000 });
		await expect(evaluation).toHaveAttribute("data-disclosure", "summary");
		await expect(evaluation).toContainText("Recommendation");
		await expect(evaluation).toContainText("Recorded reason");
		await expect(page.locator('[data-testid="tnd-stage-bid-evaluation-view-report"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-stage-bid-opening"] button')).toHaveCount(0);
	});

	test("the department-level evaluation view has the outcome and reason and none of the bids", async ({ page }) => {
		await login(page, PETER, PASSWORD);
		await gotoDesk(page, `tenders/${TENDER}/evaluation`);
		await expect(evl(page)).toContainText("Recommendation", { timeout: 60_000 });
		await expect(evl(page)).toContainText("Recorded reason");
		await expect(evl(page)).not.toContainText("Bid comparison");
		for (const rival of BIDDERS.slice(1)) await expect(evl(page)).not.toContainText(rival);
	});
});

test.describe("Procurement meetings", () => {
	test("the Accounting Officer sees the totals by type and lead department and the meetings", async ({ page }) => {
		await login(page, AMINA, PASSWORD);
		await gotoDesk(page, "procurement-meetings");
		await expect(page.locator('[data-testid="pmt-title"]')).toHaveText("Procurement meetings", { timeout: 60_000 });
		await expect(page.locator('[data-testid="pmt-held-total"]')).toHaveText("3");
		await expect(page.locator('[data-testid="pmt-totals"]')).toContainText("Grouped by lead department");
		await expect(page.locator('[data-testid="pmt-by-department"] tbody tr').first()).toContainText("Digital Health");
		await expect(page.locator('[data-testid="pmt-rows"] tbody tr')).toHaveCount(3);
		await expect(page.locator('[data-testid="pmt-rows"]')).toContainText("Contributor: Human Resources Management and Development");
		await expect(page.locator("body")).not.toContainText("Afya"); // no bidder anywhere on the register
	});

	test("a filter narrows the rows, keeps the reader's choice, and Clear filters restores them", async ({ page }) => {
		await login(page, AMINA, PASSWORD);
		await gotoDesk(page, "procurement-meetings");
		await expect(page.locator('[data-testid="pmt-rows"] tbody tr')).toHaveCount(3, { timeout: 60_000 });
		await expect(page.locator('[data-testid="pmt-clear"]')).toHaveCount(0);
		await page.locator("#pmt-type").selectOption("Bid opening");
		await expect(page.locator('[data-testid="pmt-rows"] tbody tr')).toHaveCount(1);
		await expect(page.locator("#pmt-type")).toHaveValue("Bid opening"); // the control keeps the reader's own choice
		await expect(page.locator('[data-testid="pmt-held-total"]')).toHaveText("1");
		await page.locator('[data-testid="pmt-clear"]').click();
		await expect(page.locator('[data-testid="pmt-rows"] tbody tr')).toHaveCount(3);
		await page.locator("#pmt-q").fill("NO-SUCH-TENDER");
		await expect(page.locator('[data-testid="pmt-empty"]')).toContainText("No meetings match these filters.");
	});

	test("a row opens the meeting's own record on its Tender, and back returns to the register", async ({ page }) => {
		await login(page, NAOMI, PASSWORD);
		await gotoDesk(page, "procurement-meetings");
		const first = page.locator('[data-testid="pmt-row-opening"]').first();
		await first.getByRole("link", { name: /View record/ }).click({ timeout: 60_000 });
		await expect(page).toHaveURL(new RegExp(`/desk/tenders/${TENDER}/opening`));
		await page.goBack();
		await expect(page.locator('[data-testid="pmt-title"]')).toBeVisible({ timeout: 60_000 });
	});

	test("a Head of User Department reads the register for a Tender their unit contributed to", async ({ page }) => {
		await login(page, PETER, PASSWORD);
		await gotoDesk(page, "procurement-meetings");
		await expect(page.locator('[data-testid="pmt-held-total"]')).toHaveText("3", { timeout: 60_000 });
	});

	test("a person with no procurement responsibility gets the forbidden panel and no data", async ({ page }) => {
		await login(page, ESTHER, PASSWORD);
		await gotoDesk(page, "procurement-meetings");
		await expect(page.locator('[data-testid="pmt-forbidden"]')).toContainText("You do not have access to Procurement meetings.", { timeout: 60_000 });
		await expect(page.locator('[data-testid="pmt-rows"]')).toHaveCount(0);
	});

	test("the sidebar lists Procurement meetings under Tender Management", async ({ page }) => {
		await login(page, AMINA, PASSWORD);
		await gotoDesk(page, "procurement-meetings");
		await expect(page.locator('[data-testid="pmt-title"]')).toBeVisible({ timeout: 60_000 });
		const link = page.locator(".sidebar-item-container a, .desk-sidebar a").filter({ hasText: "Procurement meetings" }).first();
		if (!(await link.isVisible())) await page.getByText("Tender Management", { exact: true }).first().click(); // the group opens on a click
		await expect(link).toBeVisible();
		await link.click();
		await expect(page.locator('[data-testid="pmt-title"]')).toBeVisible();
	});
});

test.describe("the readers the first slice left out", () => {
	test("a Head of User Department opens the Award from the Tender record and reads the stage only", async ({ page }) => {
		await login(page, PETER, PASSWORD);
		await gotoDesk(page, `tenders/${TENDER}`);
		await page.locator('[data-testid="tnd-stage-award-view-record"]').click({ timeout: 60_000 });
		await expect(page).toHaveURL(new RegExp(`/desk/award/${AWARD}$`));
		const body = page.locator('[data-testid="awd-board"]');
		await expect(body).toContainText("Award stage", { timeout: 60_000 });
		await expect(body).toContainText("is preparing the professional opinion.");
		await expect(body).toContainText("Details are shared with you when the Accounting Officer records the decision.");
		for (const word of ["Afya", "Jirani", "Sign opinion", "Evaluation report", "Bid comparison"]) await expect(body).not.toContainText(word);
		await page.goBack();
		await expect(page.locator('[data-testid="tnd-decisions-progress"]')).toBeVisible({ timeout: 60_000 });
	});

	test("the Award stays Not found to an unrelated reader", async ({ page }) => {
		await login(page, ESTHER, PASSWORD);
		await gotoDesk(page, `award/${AWARD}`);
		await expect(page.locator("body")).toContainText("This award record does not exist or you do not have access to it.", { timeout: 60_000 });
	});

	test("a technical reader reads the delivered evaluation record and report, with no bid to review and no action", async ({ page }) => {
		await login(page, DANIEL, PASSWORD);
		await gotoDesk(page, `tenders/${TENDER}/evaluation`);
		await expect(evl(page).locator('[data-testid="evl-comparison"]')).toBeVisible({ timeout: 60_000 });
		await expect(evl(page)).not.toContainText("Review bid");
		await evl(page).getByRole("button", { name: "View report" }).click();
		await expect(page).toHaveURL(new RegExp(`/desk/tenders/${TENDER}/evaluation/report`));
		await expect(evl(page)).toContainText("Evaluation report 1", { timeout: 60_000 });
		for (const word of ["Return for correction", "Sign report", "Revise report"]) await expect(evl(page)).not.toContainText(word);
	});
});

test.describe("CTX v1.1: no route asks for a Procuring Entity", () => {
	test("Procurement Home shows the site's one entity as text, with no selector", async ({ page }) => {
		await login(page, AMINA, PASSWORD);
		await gotoDesk(page, "kt-procurement-home");
		const entity = page.locator('[data-testid="kt-ph-entity"]');
		await expect(entity).toBeVisible({ timeout: 60_000 });
		expect(await entity.evaluate((el) => el.tagName)).not.toBe("SELECT");
		await expect(entity).toContainText("Ministry of Health");
		await expect(page.locator("body")).not.toContainText("No Procuring Entity is available");
	});

	test("a direct link into a record works whatever filter the user saved last", async ({ page }) => {
		await login(page, CHARLES, PASSWORD);
		await gotoDesk(page, `tenders/${TENDER}`);
		await expect(page.locator('[data-testid="tnd-decisions-progress"]')).toBeVisible({ timeout: 60_000 });
		await expect(page.locator('[data-testid="kt-rail-pe"], [data-testid="kt-rail-pe-select"]')).toHaveCount(0);
	});
});

test.describe("Strategic plans for the readers of approved Strategy", () => {
	test("a Head of User Department opens an approved plan with View", async ({ page }) => {
		// UAT: the list drew a View button for this reader but the row had no route, so it did nothing.
		await login(page, PETER, PASSWORD);
		await gotoDesk(page, "strategy");
		const view = page.locator('[data-testid="str-row-action"]').first();
		await expect(view).toBeVisible({ timeout: 60_000 });
		await expect(view).toHaveText("View");
		await view.click();
		await expect(page).toHaveURL(/\/desk\/strategy\/plan\/[^/]+/);
		const shell = page.locator('[data-testid="str-shell"]');
		await expect(shell).toHaveAttribute("data-screen", "plan", { timeout: 30_000 });
		await expect(page.locator('[data-testid="str-plan"]')).toHaveAttribute("data-loading", "false", { timeout: 30_000 });
		// A reader decides nothing: no way to update or submit the plan.
		await expect(page.locator('[data-testid="str-update-plan"]')).toHaveCount(0);
	});
});

