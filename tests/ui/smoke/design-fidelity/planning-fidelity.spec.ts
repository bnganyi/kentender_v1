import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	boxWidth,
	collectPageErrors,
	expectClose,
	expectLandmarkSubsequence,
	landmarks,
	openArtboard,
} from "../../helpers/designFidelity";
import {
	ACCOUNTING_OFFICER,
	AUTHOR,
	FINANCE,
	HOD,
	NOBODY,
	PASSWORD,
	PLANNER,
	STATUTORY,
	expectReady,
	gotoDpp,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "../planning/helpers";

/**
 * Procurement Planning design-fidelity gate (PLN-CHG-001 v1.12, decision
 * D14; AGENTS.md §6.6). Each `.dc.html` artboard is rendered in the same
 * browser as the live page and its ordered structural landmarks (card
 * titles, labels, table headers, buttons) must appear in order in the live
 * screen. Data values are never compared. Slice A covers PLN-DES-01, 02, 03,
 * 04, 05, 06, 16, Slice B's 07, 08, 09, 09A, Slice C's 10, 11, 12, 15 and
 * Slice D's 13, 14, 14A — every artboard of the v1.12 set.
 *
 * Known, deliberate deltas NOT asserted (stripped from the artboard list):
 *   - PLN-DES-16 is a seven-state gallery on one artboard; a live page shows
 *     one state at a time, so each reachable state is asserted on its own
 *     route below instead of as one subsequence. Its "not available" card
 *     copy predates §11.18's Forbidden wording (which mentions no Procuring
 *     Entity); the live copy follows §11.18.
 */

const DESIGN_DIR = "docs/mvp-1-r1/04_planning/design";
const ARTBOARD_SCOPE = ".artboard";
const LIVE_SCOPE = ".kt-pln .kt-shell";

async function artboardLandmarks(browser: any, file: string): Promise<{ wanted: string[]; art: Page }> {
	const art = await browser.newPage();
	await openArtboard(art, `${DESIGN_DIR}/${file}`, ARTBOARD_SCOPE);
	return { wanted: await landmarks(art, ARTBOARD_SCOPE), art };
}

type State = { dpp_reference: string; need_entry_id: string; direct_entry_id: string; task: string; plan_reference: string; plan_item_id: string; publication: string };
const DIALOG_SCOPE = ".kt-dialog";

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Procurement Planning — design fidelity (Slice A)", () => {
	test.afterAll(() => restoreSite());

	test("PLN-DES-01 — Procurement Planning workspace", async ({ page, browser }) => {
		resetFixture("reset_accepted_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-01 Workspace.dc.html");
		const errors = collectPageErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-actionable"]')).toBeVisible();

		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-01");
		// the filter is plain text weight, not a bordered card (§11.2)
		await expect(page.locator('[data-testid="pln-context-strip"]')).not.toHaveClass(/kt-card/);
		// (no column-width probe here: the Desk page column is narrower than the
		// artboard's free-standing 1200px content column by the rail's width)
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-02 — Draft Departmental Procurement Plan", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_dpp_fixture", { with_direct: true });
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-02 Draft DPP.dc.html");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-02");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-03 — Accepted Need funding details", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_dpp_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-03 Accepted Need Funding.dc.html");
		const artColumn = await boxWidth(art, `${ARTBOARD_SCOPE} .content`);
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference, `/entry/${state.need_entry_id}`);
		await expectReady(page, "dpp-entry");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-03");
		expectClose(await boxWidth(page, ".pln-editor"), artColumn, 4, "editor column width");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-04 — Direct departmental requirement", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_dpp_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-04 Direct Requirement.dc.html");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference, "/add-direct");
		await expectReady(page, "dpp-entry");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-04");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-05 — HoD departmental-plan submission", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_dpp_fixture", { with_direct: true, funded: true });
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-05 HoD Submission.dc.html");
		const errors = collectPageErrors(page);
		await login(page, HOD, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-certification"]')).toBeVisible();
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-05");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-06 — DPP validation task", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_review_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-06 DPP Validation.dc.html");
		const errors = collectPageErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/dpp-review/${state.task}`);
		await expectReady(page, "dpp-review");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-06");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-07 — Draft Annual Procurement Plan", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_workbench_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-07 Draft Annual Plan.dc.html");
		const errors = collectPageErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-07");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-08 — Form Plan Items dialog", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_workbench_fixture");
		const art = await browser.newPage();
		await openArtboard(art, `${DESIGN_DIR}/PLN-DES-08 Form Plan Items Dialog.dc.html`, ".dialog");
		const wanted = await landmarks(art, ".dialog");
		const artWidth = await boxWidth(art, ".dialog");
		const errors = collectPageErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await page.locator('[data-testid="pln-form-items"]').click();
		await expect(page.locator('[data-testid="pln-form-dialog"]')).toBeVisible();
		// the artboard depicts the several-sources variant with its formation
		// radios; one source shows no radio (§12.7), so the radio labels are
		// the one documented delta stripped here
		const wantedWithoutRadios = wanted.filter((text) => !/^Create one /.test(text));
		expectLandmarkSubsequence(wantedWithoutRadios, await landmarks(page, DIALOG_SCOPE), "PLN-DES-08");
		expectClose(await boxWidth(page, DIALOG_SCOPE), artWidth, 4, "dialog width");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-09 — Plan Item editor", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_plan_item_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-09 Plan Item Editor.dc.html");
		const errors = collectPageErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		// the artboard's dc-runtime <sc-if> renders BOTH disclosure states'
		// markup statically (closed summary and the open period inputs); the
		// live page shows one at a time, so open the disclosure for parity
		await page.locator('[data-testid="ppi-adjust-periods"]').click();
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-09");
		// (no 1000px column probe: the Desk page column is narrower than the
		// artboard's free-standing content column — the DES-01 delta again)
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-09A — Combined Plan Item editor", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_combined_item_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-09A Combined Plan Item Editor.dc.html");
		const errors = collectPageErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await page.locator('[data-testid="ppi-adjust-periods"]').click();
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-09A");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-10 — Plan funding confirmation task", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_finance_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-10 Finance Confirmation.dc.html");
		const errors = collectPageErrors(page);
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-10");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-11 — Accounting Officer adoption", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_governance_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-11 Accounting Officer Adoption.dc.html");
		const errors = collectPageErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-11");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-12 — Statutory approval", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_statutory_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-12 Statutory Approval.dc.html");
		const errors = collectPageErrors(page);
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-12");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-15 — the two return dialogs", async ({ page, browser }) => {
		const art = await browser.newPage();
		await openArtboard(art, `${DESIGN_DIR}/PLN-DES-15 Return Dialogs.dc.html`, ".artboard");
		const panels = await art.locator(".panel").count();
		expect(panels).toBe(2);
		const wantedAo = await landmarks(art, ".panel:nth-of-type(1) .dialog");
		const wantedStatutory = await landmarks(art, ".panel:nth-of-type(2) .dialog");
		const artWidth = await boxWidth(art, ".panel:nth-of-type(1) .dialog");
		await art.close();

		const ao = resetFixture<State>("reset_governance_fixture");
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${ao.task}`);
		await expectReady(page, "governance");
		await page.locator('[data-testid="pgt-return"]').click();
		await expect(page.locator('[data-testid="pgt-return-dialog"]')).toBeVisible();
		expectLandmarkSubsequence(wantedAo, await landmarks(page, DIALOG_SCOPE), "PLN-DES-15 (AO)");
		// the artboard draws these two dialogs at 420px; DES-08/14A's 640px is
		// the Planning dialog width — a documented artboard-vs-artboard delta,
		// so the width is not asserted, the landmarks are
		expect(artWidth).toBeGreaterThan(0);

		const statutory = resetFixture<State>("reset_statutory_fixture");
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page, `/review/${statutory.task}`);
		await expectReady(page, "governance");
		await page.locator('[data-testid="pgt-return"]').click();
		await expect(page.locator('[data-testid="pgt-return-dialog"]')).toBeVisible();
		expectLandmarkSubsequence(wantedStatutory, await landmarks(page, DIALOG_SCOPE), "PLN-DES-15 (statutory)");
	});

	test("PLN-DES-13 — Publication result", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_publication_failed_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-13 Publication Result.dc.html");
		const errors = collectPageErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "PLN-DES-13");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-14 — Active Annual Procurement Plan", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_active_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "PLN-DES-14 Active Annual Plan.dc.html");
		const errors = collectPageErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		// the artboard's dc-runtime renders the schedule card open with its
		// binding placeholders as the toggle text; open the live card and
		// drop that one un-rendered placeholder landmark
		await page.locator(`[data-testid="pln-active-schedule-${state.plan_item_id}"]`).click();
		await expect(page.locator('[data-testid="pln-schedule-card"]')).toBeVisible();
		// the Schedule card title embeds the fixture item's own title (a data
		// value, not structure) — compared by prefix only
		const wantedRendered = wanted.filter((text) => !/^\{\{/.test(text)).map((text) => (text.startsWith("Schedule — ") ? "Schedule — Digital health infrastructure package" : text));
		expectLandmarkSubsequence(wantedRendered, await landmarks(page, LIVE_SCOPE), "PLN-DES-14");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("PLN-DES-14A — Shift schedule from here dialog", async ({ page, browser }) => {
		const state = resetFixture<State>("reset_active_fixture");
		const art = await browser.newPage();
		await openArtboard(art, `${DESIGN_DIR}/PLN-DES-14A Shift Schedule Dialog.dc.html`, ".dialog");
		const wanted = await landmarks(art, ".dialog");
		const artWidth = await boxWidth(art, ".dialog");
		await art.close();
		const errors = collectPageErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await page.locator(`[data-testid="pln-active-schedule-${state.plan_item_id}"]`).click();
		await page.locator('[data-testid="pln-shift-bid_opening"]').click();
		await expect(page.locator('[data-testid="pln-shift-dialog"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-shift-row-delivery_completion"]')).toBeVisible();
		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "PLN-DES-14A");
		expectClose(await boxWidth(page, DIALOG_SCOPE), artWidth, 4, "dialog width (640px, §11.16A)");
		expect(errors, "console errors").toEqual([]);
	});

	test("PLN-DES-16 — common page states, one route per reachable state", async ({ page, browser }) => {
		resetFixture("reset_workspace_fixture");
		const art = await browser.newPage();
		await openArtboard(art, `${DESIGN_DIR}/PLN-DES-16 Common Page States.dc.html`, ARTBOARD_SCOPE);
		const artCardWidth = await boxWidth(art, `${ARTBOARD_SCOPE} .state-card`);
		expect(artCardWidth).toBeGreaterThan(200);
		await art.close();

		// Forbidden — heading + text, no control
		await login(page, NOBODY, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		const forbidden = page.locator('[data-testid="pln-forbidden"]');
		await expect(forbidden).toHaveClass(/pln-state-card/);
		await expect(forbidden.locator("h3")).toHaveText("You do not have access to Procurement Planning");
		await expect(forbidden.locator("button")).toHaveCount(0);

		// Load error — Try again + support reference
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, "DPP-NOPE-0000-000");
		await expectReady(page, "dpp");
		const error = page.locator('[data-testid="pln-error"]');
		await expect(error).toHaveClass(/pln-state-card/);
		await expect(error.locator("h3")).toHaveText("Procurement Planning could not be loaded");
		await expect(error.locator("button")).toHaveText("Try again");
		await expect(error).toContainText("Support reference: PLN-ERR-");

		// No departmental plan — the workspace's Open departmental plan action
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-work-action-0"]')).toHaveText("Open departmental plan");
	});
});
