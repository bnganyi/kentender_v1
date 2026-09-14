import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectPageErrors, expectLandmarkSubsequence, landmarks, openArtboard } from "../../helpers/designFidelity";
import { APPROVER, AUDITOR, AUTHOR, PASSWORD, expectScreen, gotoStrategy, resetFixture, type DefaultFixture, type SuccessorFixture } from "./helpers";

/**
 * Strategy Alignment design-fidelity gate (FU-01, STR-AC-025 "match their
 * approved static designs", STR18-AC-020). Renders each v1.8 `.dc.html`
 * artboard as the oracle and asserts the live route's ordered landmarks
 * (card titles, dialog titles, field labels, captions, table headers,
 * buttons) contain the artboard's sequence in order — the class of drift
 * behaviour tests never see. Data values are not compared.
 *
 * Deliberate artboard-vs-live deltas stripped from the wanted list:
 *   - "My work 0" on STR-DES-01: the owner's neutral-label decision (FU-07,
 *     plan D3) renders the tab as "Actions".
 *   - STR-DES-05-AddTarget draws the pending target editor as an overlay
 *     after the indicator card's footer; §11.5 places it inline inside the
 *     indicator surface, so the card and the editor are asserted as two
 *     ordered sequences.
 *   - STR-DES-06-Return re-draws STR-DES-06's page with abbreviated
 *     Structure-summary labels that differ from STR-DES-06 itself; the page
 *     is asserted against STR-DES-06 and only the dialog against 06-Return.
 *   - STR-DES-01's "Plans 1" / STR-DES-03/04's tab buttons are inline-styled
 *     <button>s in the artboard with fixture counts baked into the text;
 *     the live tabs carry live counts, so tab texts are stripped and the
 *     tab row itself is asserted separately.
 */

const DESIGN = "docs/mvp-1-r1/02_strategy/strategy_design";
const TAB_TEXTS = new Set(["Plans 1", "My work 0", "Overview", "Structure", "History", "Changes", "Collapse", "Expand"]);

function wanted(list: string[], extraStrip: string[] = []): string[] {
	const strip = new Set([...TAB_TEXTS, ...extraStrip]);
	return list.filter((t) => !strip.has(t));
}

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("Strategy design fidelity — v1.8 artboards", () => {
	let fixture: DefaultFixture;

	test.beforeAll(() => {
		fixture = resetFixture("reset_default");
	});
	test.afterAll(() => {
		resetFixture("reset_default");
	});

	test("STR-DES-01 Strategic plans and STR-DES-02 Create strategic plan (Author)", async ({ page }) => {
		await openArtboard(page, `${DESIGN}/STR-DES-01.dc.html`, "[data-screen-label='STR-DES-01']");
		const want01 = wanted(await landmarks(page, "[data-screen-label='STR-DES-01']"));
		await openArtboard(page, `${DESIGN}/STR-DES-02.dc.html`, "[data-screen-label='STR-DES-02']");
		const want02 = wanted(await landmarks(page, "x-dc"));
		// Page errors are collected for the live routes only; the artboard
		// renders deliberately abort support.js (see openArtboard).
		const errors = collectPageErrors(page);

		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		expectLandmarkSubsequence(want01, await landmarks(page, '[data-testid="str-portfolio"]'), "STR-DES-01");
		await expect(page.locator('[data-testid="str-tab-plans"]')).toBeVisible();
		await page.locator('[data-testid="str-new-plan"]').click();
		await expect(page.locator('[data-testid="str-new-plan-form"]')).toBeVisible();
		expectLandmarkSubsequence(want02, await landmarks(page, '[data-testid="str-portfolio"]'), "STR-DES-02");
		expect(errors).toEqual([]);
	});

	test("STR-DES-03 Current plan overview (Auditor)", async ({ page }) => {
		await openArtboard(page, `${DESIGN}/STR-DES-03.dc.html`, "[data-screen-label='STR-DES-03']");
		const want = wanted(await landmarks(page, "[data-screen-label='STR-DES-03']"));
		const errors = collectPageErrors(page);
		await login(page, AUDITOR, PASSWORD);
		await gotoStrategy(page, `/plan/${fixture.plan_reference}`);
		await expectScreen(page, "plan");
		expectLandmarkSubsequence(want, await landmarks(page, '[data-testid="str-plan"]'), "STR-DES-03");
		expect(errors).toEqual([]);
	});

	test("STR-DES-04 Draft structure editor and STR-DES-05-AddTarget inline target editor (Author)", async ({ page }) => {
		const draft = resetFixture<SuccessorFixture>("reset_draft_fixture");
		await openArtboard(page, `${DESIGN}/STR-DES-04.dc.html`, "[data-screen-label='STR-DES-04']");
		const want04 = wanted(await landmarks(page, "[data-screen-label='STR-DES-04']"));
		await openArtboard(page, `${DESIGN}/STR-DES-05-AddTarget.dc.html`, "[data-screen-label^='STR-DES-05']");
		const want05 = wanted(await landmarks(page, "[data-screen-label^='STR-DES-05']"));
		const errors = collectPageErrors(page);

		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/plan/${draft.plan_reference}/version/2/structure`);
		await expectScreen(page, "plan");
		await page.locator('[data-testid="str-tree-node"][data-node-type="Strategic Objective"]').first().click();
		expectLandmarkSubsequence(want04, await landmarks(page, '[data-testid="str-plan"]'), "STR-DES-04");
		await page.locator('[data-testid="str-tree-node"][data-node-type="Performance Indicator"]').first().click();
		await page.locator('[data-testid="str-add-target"]').click();
		await expect(page.locator('[data-testid="str-target-editor"]')).toBeVisible();
		// §11.5 places the pending target editor INLINE in the indicator
		// surface (it replaced the old dialog); the artboard draws that same
		// editor as an overlay after the card footer. The card and the editor
		// are therefore asserted as two ordered sequences.
		const splitAt = want05.indexOf("Add performance target");
		expectLandmarkSubsequence(want05.slice(0, splitAt), await landmarks(page, '[data-testid="str-plan"]'), "STR-DES-05-AddTarget (indicator surface)");
		expectLandmarkSubsequence(want05.slice(splitAt), await landmarks(page, '[data-testid="str-target-editor"]'), "STR-DES-05-AddTarget (target editor)");
		expect(errors).toEqual([]);
	});

	test("STR-DES-06..09 Approval task and STR-DES-06-Return (Approver)", async ({ page }) => {
		const submitted = resetFixture<SuccessorFixture>("reset_submitted_fixture");
		const wants: Record<string, string[]> = {};
		for (const id of ["06", "07", "08", "09", "06-Return"]) {
			const scope = `[data-screen-label^='STR-DES-${id.startsWith("06") ? "06" : id}']`;
			await openArtboard(page, `${DESIGN}/STR-DES-${id}.dc.html`, scope);
			wants[id] = wanted(await landmarks(page, "x-dc"));
		}
		const errors = collectPageErrors(page);

		await login(page, APPROVER, PASSWORD);
		await gotoStrategy(page, `/approval/${submitted.v2_reference}`);
		await expectScreen(page, "approval");
		expectLandmarkSubsequence(wants["06"], await landmarks(page, '[data-testid="str-approval"]'), "STR-DES-06");
		await page.locator('[data-testid="str-atab-structure"]').click();
		await expect(page.locator('[data-testid="str-approval-structure"]')).toBeVisible();
		expectLandmarkSubsequence(wants["07"], await landmarks(page, '[data-testid="str-approval"]'), "STR-DES-07");
		await page.locator('[data-testid="str-atab-changes"]').click();
		await expect(page.locator('[data-testid="str-approval-changes"]')).toBeVisible();
		expectLandmarkSubsequence(wants["08"], await landmarks(page, '[data-testid="str-approval"]'), "STR-DES-08");
		await page.locator('[data-testid="str-atab-history"]').click();
		await expect(page.locator('[data-testid="str-approval-history"]')).toBeVisible();
		expectLandmarkSubsequence(wants["09"], await landmarks(page, '[data-testid="str-approval"]'), "STR-DES-09");
		await page.locator('[data-testid="str-atab-overview"]').click();
		await page.locator('[data-testid="str-return"]').click();
		await expect(page.locator('[data-testid="str-return-dialog"]')).toBeVisible();
		// STR-DES-06-Return re-draws STR-DES-06's page with abbreviated summary
		// labels ("Objectives" for "Strategic objectives" …); the page itself is
		// asserted against STR-DES-06 above, so only the dialog is asserted here.
		const dialogAt = wants["06-Return"].indexOf("What needs to change?");
		expectLandmarkSubsequence(wants["06-Return"].slice(dialogAt), await landmarks(page, '[data-testid="str-return-dialog"]'), "STR-DES-06-Return (dialog)");
		expect(errors).toEqual([]);
	});
});
