import { expect, test } from "@playwright/test";

import { login, loginAsAdministrator } from "../../helpers/auth";
import { LandmarkExemption, expectLandmarkSubsequence, landmarks, onceEach, openPanel, variantScope } from "../../helpers/designFidelity";
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
 * Procurement Planning design-fidelity gate — PLN-CHG-001 v1.23.
 *
 * Rewritten from scratch for v1.23: the v1.18 artboard files this spec used to
 * compare against are retired, and the v1.23 files have a different shape —
 * one labelled panel per variant rather than `.frame`/`.caption` pairs, with
 * several variants often drawn side by side in one panel. `openPanel` and
 * `variantScope` in the shared helper index them.
 *
 * The instrument is unchanged and deliberately narrow: the artboard's ordered
 * landmark texts (card titles, field labels, table headers, buttons) must
 * appear in that order in the live page. Extra live landmarks are allowed.
 * Values are never compared — the fixture year and the artboard's fixture are
 * different worlds on purpose.
 *
 * What is asserted here is what the Playwright fixture chain can actually put
 * the live screen into. Variants needing a state no fixture builds are named
 * in their family's own comment with where they are covered instead, rather
 * than silently omitted — a fidelity gate that quietly skips half its frames
 * is worse than one that says which half.
 */

const DESIGN = "docs/mvp-1-r1/04_planning/design";
const LIVE = ".kt-pln .kt-shell";

const U01 = `${DESIGN}/U01.dc.html`;
const U0205 = `${DESIGN}/U02-U05.dc.html`;
const U06 = `${DESIGN}/U06.dc.html`;
const U07 = `${DESIGN}/U07.dc.html`;
const U08 = `${DESIGN}/U08.dc.html`;
const U09 = `${DESIGN}/U09.dc.html`;
const U10 = `${DESIGN}/U10.dc.html`;
const U11 = `${DESIGN}/U11.dc.html`;
const U12 = `${DESIGN}/U12.dc.html`;
const U13 = `${DESIGN}/U13.dc.html`;
const U14 = `${DESIGN}/U14.dc.html`;
const U16 = `${DESIGN}/U16.dc.html`;
const U21 = `${DESIGN}/U21.dc.html`;

/**
 * Landmarks the v1.23 specification replaced but the v1.23 artboard pack still
 * draws. The code follows the specification, so the gate excuses these and says
 * which section retired them; refreshing the artboard is what removes the
 * exemption, because an exemption for a landmark the artboard no longer draws
 * fails as stale. Tracked as FU-V123-01 and FU-V123-05.
 */
const U11_DECISION_TABLE: LandmarkExemption[] = ["Decision", "Outcome", "Capacity", "Person", "Date/time"].map(
	(landmark) => ({
		landmark,
		because:
			"§10.10 replaced this decision-history table above the decision with the Accountability section (Funding, Preparation) plus a collapsed Changes and history disclosure.",
	})
);

const U14_EXECUTION_COLUMNS: LandmarkExemption[] = [
	{
		landmark: "Procurements started",
		because: "§10.13 names this column Procurement stage.",
	},
	{
		landmark: "Completion",
		because:
			"§10.13: do not create a Completion column unless an owning module supplies authoritative completion evidence. None does.",
	},
];

/** §10.8 renamed these; the U09 artboards still carry the older wording. */
const U09_SCHEDULE_LABELS: LandmarkExemption[] = [
	{ landmark: "Estimated period", because: "§10.8 Dates names it Expected delivery period." },
	{ landmark: "Estimated completion", because: "§10.8 Dates names it Expected completion." },
	{ landmark: "Departmental required-by date", because: "§10.8 Dates names it Departmental deadline." },
	{ landmark: "Review schedule", because: "§10.8 U09-INVALID-SCHEDULE names the action Review dates." },
];

const U09_REMOVE_ACTION: LandmarkExemption[] = [
	{
		landmark: "Remove item and return requirements",
		because:
			"§10.8 U09-REMOVE heads the dialog Remove this purchase? and names its primary action Remove purchase.",
	},
];

// U13 draws three withdrawal/correction variants side by side under one label;
// `variantScope` picks the one wanted by its `.tag`.
const WITHDRAWAL_PANEL = "U13-WITHDRAWAL-REQUEST \u00b7 U13-WITHDRAWN \u00b7 U13-CORRECT-EVIDENCE";
const TRANSMISSION_PANEL = "U13-SENDING \u00b7 U13-FAILED \u00b7 U13-UNKNOWN";
const LATE_PANEL = "U21-UNCERTAIN-DECISION \u00b7 U21-HISTORICAL \u00b7 U21-LATE-ACTIVATION";

// Sequential, but not serial: the gate runs on one worker because the fixtures
// are one shared world, and each panel is an independent assertion about an
// independent screen. Aborting the remaining twenty because the tenth found a
// missing label turns a full report into one finding per half-hour run.
test.describe.configure({ timeout: 180_000 });

/** Render one artboard panel and hand back its ordered landmarks. */
async function wanted(browser: any, file: string, panel: string, variant?: string): Promise<string[]> {
	const art = await browser.newPage();
	try {
		const scope = await openPanel(art, file, panel);
		return await landmarks(art, variant ? await variantScope(art, scope, variant) : scope);
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
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U01-NO-PLAN");
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
		// saying what it is; they are never merged into one.
		await expect(page.locator('[data-testid="pln-plan-row-current"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-plan-row-candidate"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-plan-secondary-current"]')).toBeVisible();
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
		const art = await wanted(browser, U06, "U06 — BASE");
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
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U06-ACCEPTED-CLASSIFICATION");
		expect(errors, "console errors").toEqual([]);
	});
});

test.describe("Procurement Planning — design fidelity (U07 annual plan, U08 formation)", () => {
	test.afterAll(() => restoreSite());

	test("U07 — purchases first, then the plan's own checks", async ({ page, browser }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_plan_item_fixture");
		const art = await wanted(browser, U07, "U07 — BASE");
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
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U07");
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
		const art = await wanted(browser, U08, "U08-COMBINE (base)");
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
		await page.locator('[data-testid="pln-form-mode-combined"]').check();
		await expect(page.locator('[data-testid="pln-form-reason"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, '[data-testid="pln-form-dialog"]'), "U08-COMBINE");
		expect(errors, "console errors").toEqual([]);
	});
});

test.describe("Procurement Planning — design fidelity (U09 purchase editor)", () => {
	test.afterAll(() => restoreSite());

	test("U09 — the five decision sections and nothing else", async ({ page, browser }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_plan_item_fixture");
		const art = await wanted(browser, U09, "U09 — BASE");
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
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U09-INVALID-SCHEDULE", U09_SCHEDULE_LABELS);
		// The artboard lags §10.8 here, so assert the section's own words too —
		// otherwise the exemptions would leave almost nothing being checked.
		for (const label of ["Expected delivery period", "Expected completion", "Departmental deadline"]) {
			await expect(page.locator(LIVE)).toContainText(label);
		}
		await expect(page.locator('[data-testid="ppi-review-dates"]')).toHaveText("Review dates");
		expect(errors, "console errors").toEqual([]);
	});

	test("U09-REMOVE — what removing a purchase says it will do to its requirements", async ({ page, browser }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_plan_item_fixture");
		const art = await wanted(browser, U09, "U09-REMOVE");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`);
		await expectReady(page, "plan-item");
		await page.locator('[data-testid="ppi-remove"]').click();
		const dialog = page.locator('[data-testid="pln-dissolve-item-dialog"]');
		await expect(dialog).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, '[data-testid="pln-dissolve-item-dialog"]'), "U09-REMOVE", U09_REMOVE_ACTION);
		// §10.8's own copy, which the artboard has not caught up with.
		await expect(dialog).toContainText("Remove this purchase?");
		await expect(dialog).toContainText("These requirements will return to this draft plan so they can be added again. No funds are released.");
		await expect(page.locator('[data-testid="pln-dissolve-item-confirm"]')).toHaveText("Remove purchase");
		expect(errors, "console errors").toEqual([]);
	});

	test("U10 — approved, planned, difference and the result", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_finance_fixture");
		const art = await wanted(browser, U10, "U10 — BASE (within approved)");
		const errors = collectConsoleErrors(page);
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${state.task}`);
		await expectReady(page, "finance");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U10");
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
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U11-STATUTORY", U11_DECISION_TABLE);
		expect(errors, "console errors").toEqual([]);
	});

	test("U11-COLLECTIVE — the body decides, the recorder records", async ({ page, browser }) => {
		// §13.3's isolated collective profile: one site-wide route, put back by
		// restore_site. The decision belongs to the Council; the actor only
		// records it, and must supply the resolution it was taken under.
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
		const art = await wanted(browser, U12, "U12 — Pinned source (base)");
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
		const art = await wanted(browser, U21, LATE_PANEL, "U21-LATE-ACTIVATION");
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
		const art = await wanted(browser, U13, TRANSMISSION_PANEL, "U13-UNKNOWN");
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
		const art = await wanted(browser, U13, WITHDRAWAL_PANEL, "U13-CORRECT-EVIDENCE");
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
		const art = await wanted(browser, U14, "U14 — BASE (initial)");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}/progress`);
		await expectReady(page, "progress");
		// The artboard draws one card per purchase in §10.2's fixture, which has
		// two; this world has one. How many purchases a world holds is fixture
		// content, and this gate never compares fixture content — so the card's
		// own structure is compared once.
		expectLandmarkSubsequence(onceEach(art), await landmarks(page, LIVE), "U14", U14_EXECUTION_COLUMNS);
		// PLN22-AC-009 — the absence is the acceptance criterion.
		await expect(page.locator(LIVE)).not.toContainText("Completion");
		await expect(page.locator(LIVE)).not.toContainText("Forecast");
		expect(errors, "console errors").toEqual([]);
	});
});
