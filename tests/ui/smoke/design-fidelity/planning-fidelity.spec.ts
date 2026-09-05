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
	AUTHOR,
	HOD,
	NOBODY,
	PASSWORD,
	PLANNER,
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
 * 04, 05, 06 and 16; later slices add their artboards to this file.
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

type State = { dpp_reference: string; need_entry_id: string; direct_entry_id: string; task: string };

test.describe.configure({ mode: "serial" });

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
