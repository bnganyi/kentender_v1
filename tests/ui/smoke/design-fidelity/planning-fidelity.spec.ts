import { expect, test } from "@playwright/test";

import { login, loginAsAdministrator } from "../../helpers/auth";
import {
	LandmarkExemption,
	expectLandmarkSubsequence,
	expectLayoutSanity,
	expectStructure,
	landmarks,
	onceEach,
	openSection,
	outerHtml,
} from "../../helpers/designFidelity";
import { DEPARTURES } from "../../fidelity/departures/procurement-planning.js";
import {
	ACCOUNTING_OFFICER,
	AUTHOR,
	FINANCE,
	HOD,
	PASSWORD,
	PLANNER,
	STATUTORY,
	collectConsoleErrors,
	expectReady,
	gotoDpp,
	gotoPlanning,
	resetFixture,
	restoreSite,
	tickCheckbox,
} from "../planning/helpers";

/**
 * Procurement Planning design-fidelity gate — PLN-CHG-001 v1.24 (Stage 2,
 * KT-STD-001 v1.7).
 *
 * Re-pointed for v1.24: the v1.23 per-screen artboard files (and their
 * positioned-label panel/tag convention) are retired, replaced by 10 bundled
 * `Artboards-*.dc.html` files. Several screen families now share one file
 * (U07+U08, U12+U13, U14+U16, and C01–C04+U21), and every variant is its own
 * `<section id="EXACT-SPEC-ID">` — `openSection` in the shared helper opens
 * one directly, with no panel/tag indexing step.
 *
 * The instrument is unchanged and deliberately narrow: the artboard's ordered
 * landmark texts (card/region titles, field labels, table headers, buttons)
 * must appear in that order in the live page. Extra live landmarks are
 * allowed. Values are never compared — the fixture year and the artboard's
 * fixture are different worlds on purpose.
 *
 * What is asserted here is what the Playwright fixture chain can actually put
 * the live screen into. Variants needing a state no fixture builds are named
 * in their family's own comment with where they are covered instead, rather
 * than silently omitted — a fidelity gate that quietly skips half its frames
 * is worse than one that says which half. A handful of named variants are
 * themselves "awaiting fixture" placeholders in the v1.24 pack (dashed-border
 * boxes, not finished mockups) — those are marked `test.fixme` here with the
 * screen-family slice that owns resolving them, per the Planning UI-fidelity
 * implementation plan.
 */

const DESIGN = "docs/mvp-1-r1/04_planning/design";
const LIVE = ".kt-pln .kt-shell";

const U01 = `${DESIGN}/Artboards-U01.dc.html`;
const U0205 = `${DESIGN}/Artboards-U02-U05.dc.html`;
const U06 = `${DESIGN}/Artboards-U06.dc.html`;
const U07 = `${DESIGN}/Artboards-U07-U08.dc.html`;
const U08 = U07; // same bundled file
const U09 = `${DESIGN}/Artboards-U09.dc.html`;
const U10 = `${DESIGN}/Artboards-U10.dc.html`;
const U11 = `${DESIGN}/Artboards-U11.dc.html`;
const U12 = `${DESIGN}/Artboards-U12-U13.dc.html`;
const U13 = U12; // same bundled file
const U14 = `${DESIGN}/Artboards-U14-U16.dc.html`;
const U16 = U14; // same bundled file
const U21 = `${DESIGN}/Artboards-C01-U21.dc.html`;

/**
 * §10.2's fixture pairs "no annual plan yet" with two departmental
 * submissions already Accepted and awaiting Procurement review, so
 * U01-NO-PLAN's Departmental plans table has rows. `reset_workspace_fixture`
 * builds the no-plan state alone, with no departmental submissions at all —
 * a real coverage gap, not a markup defect: the same table headers render
 * correctly (with rows) in every other U01 test against this exact
 * component. Exempted here rather than left to fail on a fixture the
 * Playwright chain does not build; a fixture that adds two Accepted DPPs
 * without an Annual Plan removes this exemption.
 */
/**
 * U07 draws a failing check as a warning notice naming it in `<strong>`, and
 * the passing ones as quiet labelled facts below — so whichever check is
 * failing has no `.kt-label` on either side, and the landmark sequence depends
 * on *which* check fails. The board's own fixture fails Reserved procurement
 * and passes Schedule; `reset_plan_item_fixture` is the other way round, so
 * each world moves the other's label into its notice.
 *
 * This is a fixture-state difference, not a structural one, and the structural
 * assertion beside this call proves the notice and the group are both built as
 * the board draws them.
 */
const U07_FAILING_CHECK: LandmarkExemption[] = [
	{
		landmark: "Schedule",
		because:
			"U07's board fails Reserved procurement and states it in the notice, leaving Funding and Schedule as facts; reset_plan_item_fixture fails Schedule instead, so Schedule is the one in the notice and Reserved procurement is the fact. Whichever check fails is named in <strong>, which is not a landmark on either side.",
	},
];

const U01_NO_PLAN_TABLE: LandmarkExemption[] = ["Department", "Status", "Requirements", "Estimated cost", "Action"].map(
	(landmark) => ({
		landmark,
		because: "reset_workspace_fixture builds no departmental submissions; §10.2's own fixture pairs no-plan-yet with two Accepted ones.",
	}),
);

/**
 * U06-ACCEPTED-CLASSIFICATION adds a secondary region naming the draft
 * purchase a classification formed, when it formed and whether any submitted
 * or Active plan already uses it. `GetAcceptedDPPClassification` (§7.1) has no
 * such field — it returns `affected.recovery` for the unrelated correction-
 * impact notices, not a formed-purchase reference or timestamp for the
 * unmodified row — so this cannot be rendered without inventing a value. A
 * genuine gap, not a markup defect; flagged for the module owner rather than
 * silently built from guessed data. Removing the exemption is what closing it
 * looks like, once the read service supplies the field.
 */
const U06_DRAFT_PURCHASE_REGION: LandmarkExemption[] = [
	"Draft purchase formed from this classification",
	"Purchase",
	"Formed at",
	"Plan use",
].map((landmark) => ({
	landmark,
	because: "GetAcceptedDPPClassification supplies no formed-purchase reference, timestamp or plan-use fact for this row; not invented here.",
}));

// Sequential, but not serial: the gate runs on one worker because the fixtures
// are one shared world, and each section is an independent assertion about an
// independent screen. Aborting the remaining twenty because the tenth found a
// missing label turns a full report into one finding per half-hour run.
test.describe.configure({ timeout: 180_000 });

/**
 * Render one artboard section and hand back its ordered landmarks. A section
 * drawing a focused dialog over a dimmed page (U08 and its siblings) scopes
 * both together, so `subScope` narrows to the dialog alone — matching a live
 * test that (rightly) only asserts the dialog's own fidelity, since the page
 * behind it is a different screen's own test.
 */
async function wanted(browser: any, file: string, id: string, subScope = ""): Promise<string[]> {
	const art = await browser.newPage();
	try {
		const scope = await openSection(art, file, id);
		return await landmarks(art, subScope ? `${scope} ${subScope}` : scope);
	} finally {
		await art.close();
	}
}

/**
 * The same section's markup, for the structural half of the gate. The landmark
 * comparison above reads the artboard's *text*; this reads what it is built
 * out of — the containers and their nesting, which no text comparison can see
 * (see `tests/ui/fidelity/skeleton.js`).
 */
async function wantedStructure(browser: any, file: string, id: string, subScope = ""): Promise<string> {
	const art = await browser.newPage();
	try {
		const scope = await openSection(art, file, id);
		return await outerHtml(art, subScope ? `${scope} ${subScope} .kt-page` : `${scope} .kt-page`);
	} finally {
		await art.close();
	}
}

test.describe("Procurement Planning — design fidelity (U01 workspace)", () => {
	test.afterAll(() => restoreSite());

	test("U01-NO-PLAN — the year's own empty state", async ({ page, browser }) => {
		resetFixture("reset_workspace_fixture");
		const art = await wanted(browser, U01, "U01-NO-PLAN");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U01-NO-PLAN", U01_NO_PLAN_TABLE);
		expect(errors, "console errors").toEqual([]);
	});

	test("U01-CURRENT — a plan in force, with its own procurement progress link", async ({ page, browser }) => {
		resetFixture("reset_active_fixture");
		const art = await wanted(browser, U01, "U01-CURRENT");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U01-CURRENT");
		expect(errors, "console errors").toEqual([]);
	});

	test("U01-CURRENT-UPDATE — the plan in force and its open candidate, as two rows", async ({ page, browser }) => {
		resetFixture("reset_update_candidate_fixture");
		const art = await wanted(browser, U01, "U01-CURRENT-UPDATE");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U01-CURRENT-UPDATE");
		// §9.1 — the plan in force and the candidate are separate rows, each
		// saying what it is; they are never merged into one. §10.3 v1.24 demotes
		// the plan in force to a compact read-only baseline once a candidate
		// exists — it keeps its own region but loses the interactive
		// "View procurement progress" link the dominant row alone carries.
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toContainText("In force");
		await expect(page.locator('[data-testid="pln-plan-row-candidate"]')).toBeVisible();
		expect(errors, "console errors").toEqual([]);
	});

	test("U01-DEPARTMENT-AUTHOR — the Author's own reading of the same workspace", async ({ page, browser }) => {
		resetFixture("reset_dpp_fixture");
		const art = await wanted(browser, U01, "U01-DEPARTMENT-AUTHOR");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U01-DEPARTMENT-AUTHOR");
		expect(errors, "console errors").toEqual([]);
	});

	test("U01-HOD — the same plan, the Head of Department's own action", async ({ page, browser }) => {
		resetFixture("reset_dpp_fixture", { funded: true });
		const art = await wanted(browser, U01, "U01-HOD");
		const errors = collectConsoleErrors(page);
		await login(page, HOD, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U01-HOD");
		expect(errors, "console errors").toEqual([]);
	});
});

/**
 * U02–U05. U03-EXCLUDE, U03-REINCLUDE and U04-EDIT are dialog/editor states
 * reached by a click rather than a fixture, and are asserted through their
 * own components' tests; U05-ALL-EXCLUDED and the closed-window panel need
 * fixture states with no reset function yet.
 */
test.describe("Procurement Planning — design fidelity (U02–U05 departmental)", () => {
	test.afterAll(() => restoreSite());

	test("U02-AUTHOR-DRAFT — the department's own draft, its requirements and its actions", async ({ page, browser }) => {
		const state = resetFixture<{ dpp_reference: string }>("reset_dpp_fixture");
		const art = await wanted(browser, U0205, "U02-AUTHOR-DRAFT");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U02-AUTHOR-DRAFT");
		expect(errors, "console errors").toEqual([]);
	});

	test("U03-FUNDING — the funding panel, open beneath its own row", async ({ page, browser }) => {
		const state = resetFixture<{ dpp_reference: string }>("reset_dpp_fixture");
		const art = await wanted(browser, U0205, "U03-FUNDING");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		await page.locator('[data-testid="pln-dpp-row-action"]').first().click();
		await expect(page.locator('[data-testid="dpp-funding-panel"]')).toBeVisible();
		// The rest of the plan stays visible: that is the whole point of the
		// panel opening in place rather than on its own page.
		await expect(page.locator('[data-testid="pln-dpp-table"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U03-FUNDING");
		expect(errors, "console errors").toEqual([]);
	});

	test("U04-DIRECT — a requirement the department states itself", async ({ page, browser }) => {
		const state = resetFixture<{ dpp_reference: string }>("reset_dpp_fixture");
		const art = await wanted(browser, U0205, "U04-DIRECT");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference, "/add-direct");
		await expectReady(page, "dpp-entry");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U04-DIRECT");
		expect(errors, "console errors").toEqual([]);
	});

	test("U05-HOD — the same plan read for certification", async ({ page, browser }) => {
		const state = resetFixture<{ dpp_reference: string }>("reset_dpp_fixture", { funded: true });
		const art = await wanted(browser, U0205, "U05-HOD");
		const errors = collectConsoleErrors(page);
		await login(page, HOD, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U05-HOD");
		expect(errors, "console errors").toEqual([]);
	});
});

test.describe("Procurement Planning — design fidelity (U06 validation)", () => {
	test.afterAll(() => restoreSite());

	test("U06 — the submission as the Planner reads it, with its classification input", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_review_fixture");
		const art = await wanted(browser, U06, "U06");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/dpp-review/${state.task}`);
		await expectReady(page, "dpp-review");
		// The artboard's base state has the requirement type chosen, which is
		// what makes the acceptance available: the control is absent until the
		// evidence supports it, not disabled (§10.5).
		// Acceptance needs every requirement classified, and this submission
		// carries two (a Need-origin row and a direct one) — classifying only
		// the first leaves it correctly blocked.
		const types = page.locator('[data-testid="pln-review-type"]');
		for (let i = 0; i < (await types.count()); i += 1) {
			await types.nth(i).selectOption({ index: 1 });
		}
		await expect(page.locator('[data-testid="pln-review-accept"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U06");
		expect(errors, "console errors").toEqual([]);
	});

	test("U06-ACCEPTED-CLASSIFICATION — the accepted record, read after the fact", async ({ page, browser }) => {
		const state = resetFixture<{ dpp_submission: string }>("reset_accepted_fixture");
		const art = await wanted(browser, U06, "U06-ACCEPTED-CLASSIFICATION");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/dpp-classification/${state.dpp_submission}`);
		await expectReady(page, "dpp-classification");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U06-ACCEPTED-CLASSIFICATION", U06_DRAFT_PURCHASE_REGION);
		expect(errors, "console errors").toEqual([]);
	});
});

test.describe("Procurement Planning — design fidelity (U07 annual plan, U08 formation)", () => {
	test.afterAll(() => restoreSite());

	test("U07 — purchases first, then the plan's own checks", async ({ page, browser }) => {
		// A published 30% target, so the plan shows the board's unmet
		// Reservation allocation block (PLN v1.25).
		const state = resetFixture<{ plan_reference: string }>("reset_plan_item_fixture", { reservation_target_percent: 30 });
		const art = await wanted(browser, U07, "U07");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`);
		await expectReady(page, "plan");
		// §10.6 omits Project name when blank, so the live Draft offers the
		// control instead. The artboard depicts the Planner who took it up —
		// take it up here too, then compare the same state.
		await page.locator('[data-testid="ppl-add-project-name"]').click();
		await expect(page.locator('[data-testid="ppl-project-name"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U07", U07_FAILING_CHECK);
		// The containers, not just the copy: the `.kt-group` around Plan checks
		// was dropped and every landmark assertion still passed (24 Sep 2026).
		await expectStructure(page, `${LIVE} .kt-page`, await wantedStructure(browser, U07, "U07"), "U07", DEPARTURES["AnnualPlanScreen#U07"]);
		// AGENTS.md §6.6/§6.11 — repeated notices, controls inside a fact, and a
		// label over nothing. The rule already said every editor journey should
		// call this; one did.
		await expectLayoutSanity(page, "U07");
		expect(errors, "console errors").toEqual([]);
	});

	test("U07-UNALLOCATED — the requirements still waiting to become purchases", async ({ page, browser }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_workbench_fixture");
		const art = await wanted(browser, U07, "U07-UNALLOCATED");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`);
		await expectReady(page, "plan");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U07-UNALLOCATED");
		expect(errors, "console errors").toEqual([]);
	});

	test("U08-COMBINE — the selected requirements, the choice and what it produces", async ({ page, browser }) => {
		// The choice between keeping requirements separate and combining them
		// only exists with more than one selected, which is what the artboard
		// draws — so this variant needs a world with two unallocated sources.
		const state = resetFixture<{ plan_reference: string }>("reset_combinable_sources_fixture");
		const art = await wanted(browser, U08, "U08", ".dialog");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`);
		await expectReady(page, "plan");
		const sources = page.locator('[data-testid="ppl-select-source"]');
		await expect(sources).toHaveCount(2);
		await tickCheckbox(sources.nth(0));
		await tickCheckbox(sources.nth(1));
		await page.locator('[data-testid="ppl-add-selected"]').click();
		await expect(page.locator('[data-testid="pln-form-dialog"]')).toBeVisible();
		// The dialog opens on Keep separate; this panel is the combined choice,
		// and the reason it asks for only exists once that choice is made.
		// U08's own `.seg`/`.seg-opt` toggle hides its native radio input
		// (pointer-events aside, the visual state is drawn entirely on the
		// label) — same as the checkbox trap `tickCheckbox` already exists
		// for, so it is reused here rather than `.check()`ing the hidden input.
		await tickCheckbox(page.locator('[data-testid="pln-form-mode-combined"]'));
		await expect(page.locator('[data-testid="pln-form-reason"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, '[data-testid="pln-form-dialog"]'), "U08-COMBINE");
		expect(errors, "console errors").toEqual([]);
	});
});

test.describe("Procurement Planning — design fidelity (U09 purchase editor)", () => {
	test.afterAll(() => restoreSite());

	test("U09 — the five decision sections and nothing else", async ({ page, browser }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_plan_item_fixture");
		const art = await wanted(browser, U09, "U09");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`);
		await expectReady(page, "plan-item");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U09");
		expect(errors, "console errors").toEqual([]);
	});
});

test.describe("Procurement Planning — design fidelity (U10 funding review)", () => {
	test.afterAll(() => restoreSite());

	test("U09-INVALID-SCHEDULE — the dates that miss the department's deadline", async ({ page, browser }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_item_feasibility_fail_fixture");
		const art = await wanted(browser, U09, "U09-INVALID-SCHEDULE");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`);
		await expectReady(page, "plan-item");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U09-INVALID-SCHEDULE");
		// §10.8's own words, asserted directly as well as through the landmark
		// sequence above.
		for (const label of ["Expected delivery period", "Expected completion", "Departmental deadline"]) {
			await expect(page.locator(LIVE)).toContainText(label);
		}
		await expect(page.locator('[data-testid="ppi-review-dates"]')).toHaveText("Review dates");
		expect(errors, "console errors").toEqual([]);
	});

	test("U09-REMOVE — what removing a purchase says it will do to its requirements", async ({ page, browser }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_plan_item_fixture");
		const art = await wanted(browser, U09, "U09-REMOVE", ".dialog");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`);
		await expectReady(page, "plan-item");
		await page.locator('[data-testid="ppi-remove"]').click();
		const dialog = page.locator('[data-testid="pln-dissolve-item-dialog"]');
		await expect(dialog).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, '[data-testid="pln-dissolve-item-dialog"]'), "U09-REMOVE");
		// §10.8's own copy, which the artboard has not caught up with.
		await expect(dialog).toContainText("Remove this purchase?");
		await expect(dialog).toContainText("These requirements will return to this draft plan so they can be added again. No funds are released.");
		await expect(page.locator('[data-testid="pln-dissolve-item-confirm"]')).toHaveText("Remove purchase");
		expect(errors, "console errors").toEqual([]);
	});

	test("U10 — approved, planned, difference and the result", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_finance_fixture");
		const art = await wanted(browser, U10, "U10");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U10");
		expect(errors, "console errors").toEqual([]);
	});

	test("U10-OVER-APPROVED — the plan asks for more than the line approves", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_finance_excess_fixture");
		const art = await wanted(browser, U10, "U10-OVER-APPROVED");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U10-OVER-APPROVED");
		// §10.9's own headings, which this artboard borrowed from another table.
		for (const heading of ["Approved amount", "Planned amount", "Difference", "Result"]) {
			await expect(page.locator(LIVE)).toContainText(heading);
		}
		// §10.9 U10-OVER-APPROVED — the exact shortfall, named.
		await expect(page.locator(LIVE)).toContainText("exceeds its approved budget by");
		// §10.9 — an approved excess blocks confirmation and leaves the return.
		await expect(page.locator('[data-testid="fnt-confirm"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="fnt-return"]')).toBeVisible();
		expect(errors, "console errors").toEqual([]);
	});

	test("U10-RETURN — the correction Finance is asking for", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_finance_excess_fixture");
		const art = await wanted(browser, U10, "U10-RETURN", ".dialog");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");
		await page.locator('[data-testid="fnt-return"]').click();
		await expect(page.locator('[data-testid="fnt-return-dialog"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, '[data-testid="fnt-return-dialog"]'), "U10-RETURN");
		expect(errors, "console errors").toEqual([]);
	});

	test("U10-REASSESS — checking the same plan again on a new basis", async ({ page, browser }) => {
		// `U10-REASSESS` is an "awaiting fixture" placeholder in the v1.24 pack
		// (Artboards-U10.dc.html — a dashed-border box, not a finished mockup),
		// so there is no real design to compare against yet. Resolving this is
		// slice 1f's job in the Planning UI-fidelity implementation plan, not
		// this harness re-point.
		test.fixme(true, "U10-REASSESS has no finished v1.24 design yet — see plan slice 1f");
		const state = resetFixture<{ task: string }>("reset_finance_reassessment_fixture");
		const art = await wanted(browser, U10, "U10-REASSESS");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U10-REASSESS");
		expect(errors, "console errors").toEqual([]);
	});

	// U10-HISTORY carries no landmarks at all — it is values and prose, which
	// this instrument never compares — so it cannot be gated by landmark order.
	// Its structure is asserted here instead, and FU-V123-08 records that the
	// live block names and columns do not match §10.9's own.
	test("U10-HISTORY — both reviews kept, neither overwriting the other", async ({ page }) => {
		const state = resetFixture<{ task: string }>("reset_finance_reassessment_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");
		const history = page.locator('[data-testid="fnt-history"]');
		await expect(history).toBeVisible();
		await expect(history.locator("tbody tr")).toHaveCount(2);
		await expect(page.locator('[data-testid="fnt-history-review-1"]')).toContainText("Confirmed");
		await expect(page.locator('[data-testid="fnt-history-review-2"]')).toContainText("Awaiting confirmation");
		expect(errors, "console errors").toEqual([]);
	});
});

test.describe("Procurement Planning — design fidelity (U11 governance, U12 evidence)", () => {
	test.afterAll(() => restoreSite());

	test("U11-AO — one document, the decision before the evidence", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_governance_fixture");
		const art = await wanted(browser, U11, "U11-AO");
		const errors = collectConsoleErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		// The artboard's own caption: "One purchase is shown open to picture the
		// single drill-down level; no purchase opens automatically" — so open one
		// deliberately, matching what the artboard depicts, rather than asserting
		// against a state the live page never reaches on its own.
		await page.locator('[data-testid="rev-review-purchase"]').first().click();
		await expect(page.locator('[data-testid="rev-purchase-detail"]').first()).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U11-AO");
		expect(errors, "console errors").toEqual([]);
	});

	test("U11-STATUTORY — the approving authority's own reading", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_statutory_fixture");
		const art = await wanted(browser, U11, "U11-STATUTORY");
		const errors = collectConsoleErrors(page);
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U11-STATUTORY");
		expect(errors, "console errors").toEqual([]);
	});

	test("U11-COLLECTIVE — the body decides, the recorder records", async ({ page, browser }) => {
		// §13.3's isolated collective profile: one site-wide route, put back by
		// restore_site. The decision belongs to the Council; the actor only
		// records it, and must supply the resolution it was taken under.
		//
		// `U11-COLLECTIVE` is itself an "awaiting fixture" placeholder in the
		// v1.24 pack (Artboards-U11.dc.html) — no finished mockup exists yet.
		// Resolving this is slice 1g's job in the Planning UI-fidelity
		// implementation plan, not this harness re-point.
		test.fixme(true, "U11-COLLECTIVE has no finished v1.24 design yet — see plan slice 1g");
		const state = resetFixture<{ task: string }>("reset_collective_fixture");
		const art = await wanted(browser, U11, "U11-COLLECTIVE");
		const errors = collectConsoleErrors(page);
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		await expect(page.locator('[data-testid="rev-collective"]')).toBeVisible();
		await expect(page.locator('[data-testid="rev-resolution"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U11-COLLECTIVE");
		expect(errors, "console errors").toEqual([]);
	});

	test("U12 — the exact departmental requirement behind one reviewed source", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_governance_fixture");
		const art = await wanted(browser, U12, "U12");
		const errors = collectConsoleErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		// §10.10 — no purchase starts expanded, and the source evidence links
		// live in the one level of detail Review purchase opens.
		await page.locator('[data-testid="rev-review-purchase"]').first().click();
		await expect(page.locator('[data-testid="rev-purchase-detail"]').first()).toBeVisible();
		await page.locator('[data-testid="rev-view-evidence"]').first().click();
		await expectReady(page, "governance-source");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U12");
		expect(errors, "console errors").toEqual([]);
	});
});

/**
 * U13. The published/active panels are covered by the active fixture. The
 * Treasury form and its correction are two different artboards because they
 * are two different states of the same route: before a submission exists the
 * Accounting Officer is asked to confirm the document, and after one exists
 * they are asked why they are changing it. Each is compared against its own
 * panel, from the fixture that actually produces it.
 */
test.describe("Procurement Planning — design fidelity (U13 publication)", () => {
	test.afterAll(() => restoreSite());

	test("U13-TREASURY-FORM — every field, and the confirmation that gates it", async ({ page, browser }) => {
		const state = resetFixture<{ publication: string }>("reset_approved_fixture");
		const art = await wanted(browser, U13, "U13-TREASURY-FORM");
		const errors = collectConsoleErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		await page.locator('[data-testid="pub-record-treasury"]').click();
		await expect(page.locator('[data-testid="pub-treasury-dialog"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, '[data-testid="pub-treasury-dialog"]'), "U13-TREASURY-FORM");
		expect(errors, "console errors").toEqual([]);
	});

	test("U21-LATE-ACTIVATION — why the plan started late, said once and kept", async ({ page, browser }) => {
		const state = resetFixture<{ publication: string }>("reset_late_activation_fixture");
		const art = await wanted(browser, U21, "U21-LATE-ACTIVATION", ".dialog");
		const errors = collectConsoleErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="pub-late-activation"]')).toBeVisible();
		await page.locator('[data-testid="pub-explain-late"]').click();
		const dialog = page.locator('[data-testid="pln-late-explanation-dialog"]');
		await expect(dialog).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, '[data-testid="pln-late-explanation-dialog"]'), "U21-LATE-ACTIVATION");
		// §10.14 — it says why, and offers no way to change when.
		await expect(dialog.locator('input[type="date"]')).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("U13-UNKNOWN — an unconfirmed result is neither success nor failure", async ({ page, browser }) => {
		const state = resetFixture<{ publication: string }>("reset_publication_unknown_fixture");
		const art = await wanted(browser, U13, "U13-UNKNOWN");
		const errors = collectConsoleErrors(page);
		// §10.12 — reconciling an unknown result is the technical operator's,
		// and a technical read alone never creates retry authority, so the
		// panel this artboard draws is theirs.
		await loginAsAdministrator(page);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U13-UNKNOWN");
		// Reconciliation, never a blind retry, and never shown as failure.
		await expect(page.locator('[data-testid="pub-retry"]')).toHaveCount(0);
		await expect(page.locator(LIVE)).not.toContainText("The plan was not published");

		// The Accounting Officer reads the same unknown result and is offered
		// no recovery of any kind.
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="pub-retry"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pub-reconcile"]')).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("U13-CORRECT-EVIDENCE — the same route once a submission already exists", async ({ page, browser }) => {
		const state = resetFixture<{ publication: string }>("reset_publication_failed_fixture");
		const art = await wanted(browser, U13, "U13-CORRECT-EVIDENCE");
		const errors = collectConsoleErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		await page.locator('[data-testid="pub-correct-treasury"]').click();
		await expect(page.locator('[data-testid="pub-treasury-dialog"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, '[data-testid="pub-treasury-dialog"]'), "U13-CORRECT-EVIDENCE");
		expect(errors, "console errors").toEqual([]);
	});
});

test.describe("Procurement Planning — design fidelity (U14 progress, U16 corrections)", () => {
	test.afterAll(() => restoreSite());

	test("U14 — planned, covered and what has started", async ({ page, browser }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_active_fixture");
		const art = await wanted(browser, U14, "U14");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}/progress`);
		await expectReady(page, "progress");
		// The artboard draws one card per purchase in §10.2's fixture, which has
		// two; this world has one. How many purchases a world holds is fixture
		// content, and this gate never compares fixture content — so the card's
		// own structure is compared once.
		expectLandmarkSubsequence(onceEach(art), await landmarks(page, LIVE), "U14");
		// PLN22-AC-009 — the absence is the acceptance criterion.
		await expect(page.locator(LIVE)).not.toContainText("Completion");
		await expect(page.locator(LIVE)).not.toContainText("Forecast");
		expect(errors, "console errors").toEqual([]);
	});
});
