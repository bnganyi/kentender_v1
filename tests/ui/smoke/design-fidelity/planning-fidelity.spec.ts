import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { expectLandmarkSubsequence, landmarks, openPanel, variantScope } from "../../helpers/designFidelity";
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

test.describe.configure({ mode: "serial", timeout: 180_000 });

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
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U06");
		expect(errors, "console errors").toEqual([]);
	});

	test("U06-ACCEPTED-CLASSIFICATION — the accepted record, read after the fact", async ({ page, browser }) => {
		const state = resetFixture<{ submission: string }>("reset_accepted_fixture");
		const art = await wanted(browser, U06, "U06-ACCEPTED-CLASSIFICATION");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/dpp-classification/${state.submission}`);
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
		await gotoPlanning(page);
		await page.goto(`${page.url().split("/desk")[0]}/app/annual-procurement-plan/${state.plan_reference}`);
		await expectReady(page, "plan");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U07");
		expect(errors, "console errors").toEqual([]);
	});

	test("U07-UNALLOCATED — the requirements still waiting to become purchases", async ({ page, browser }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_workbench_fixture");
		const art = await wanted(browser, U07, "U07-UNALLOCATED");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`${page.url().split("/desk")[0]}/app/annual-procurement-plan/${state.plan_reference}`);
		await expectReady(page, "plan");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U07-UNALLOCATED");
		expect(errors, "console errors").toEqual([]);
	});

	test("U08-COMBINE — the selected requirements, the choice and what it produces", async ({ page, browser }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_workbench_fixture");
		const art = await wanted(browser, U08, "U08-COMBINE (base)");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`${page.url().split("/desk")[0]}/app/annual-procurement-plan/${state.plan_reference}`);
		await expectReady(page, "plan");
		await page.locator('[data-testid="ppl-select-source"]').first().check();
		await page.locator('[data-testid="ppl-add-selected"]').click();
		await expect(page.locator('[data-testid="pln-form-dialog"]')).toBeVisible();
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
		await page.goto(`${page.url().split("/desk")[0]}/app/procurement-plan-item/${state.plan_item_id}`);
		await expectReady(page, "plan-item");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U09");
		expect(errors, "console errors").toEqual([]);
	});
});

test.describe("Procurement Planning — design fidelity (U10 funding review)", () => {
	test.afterAll(() => restoreSite());

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
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U11-STATUTORY");
		expect(errors, "console errors").toEqual([]);
	});

	test("U12 — the exact departmental requirement behind one reviewed source", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_governance_fixture");
		const art = await wanted(browser, U12, "U12 — Pinned source (base)");
		const errors = collectConsoleErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${state.task}`);
		await expectReady(page, "governance");
		await page.locator('[data-testid="rev-view-evidence"]').first().click();
		await expectReady(page, "governance-source");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U12");
		expect(errors, "console errors").toEqual([]);
	});
});

/**
 * U13. The published/active panels are covered by the active fixture; the
 * Treasury form, its correction and both withdrawal dialogs need the
 * approved-but-unpublished or publication-failed states, which
 * `reset_publication_failed_fixture` builds.
 */
test.describe("Procurement Planning — design fidelity (U13 publication)", () => {
	test.afterAll(() => restoreSite());

	test("U13-TREASURY-FORM — every field, and the confirmation that gates it", async ({ page, browser }) => {
		const state = resetFixture<{ publication: string }>("reset_publication_failed_fixture");
		const art = await wanted(browser, U13, "U13-TREASURY-FORM");
		const errors = collectConsoleErrors(page);
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/publication/${state.publication}`);
		await expectReady(page, "publication");
		const record = page.locator('[data-testid="pub-record-treasury"]');
		const correct = page.locator('[data-testid="pub-correct-treasury"]');
		await (await record.count() ? record : correct).click();
		await expect(page.locator('[data-testid="pub-treasury-dialog"]')).toBeVisible();
		expectLandmarkSubsequence(art, await landmarks(page, '[data-testid="pub-treasury-dialog"]'), "U13-TREASURY-FORM");
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
		await page.goto(`${page.url().split("/desk")[0]}/app/annual-procurement-plan/${state.plan_reference}/progress`);
		await expectReady(page, "progress");
		expectLandmarkSubsequence(art, await landmarks(page, LIVE), "U14");
		// PLN22-AC-009 — the absence is the acceptance criterion.
		await expect(page.locator(LIVE)).not.toContainText("Completion");
		await expect(page.locator(LIVE)).not.toContainText("Forecast");
		expect(errors, "console errors").toEqual([]);
	});
});
