import { expect, test, Page } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectPageErrors, expectLandmarkSubsequence, landmarks, openArtboard } from "../../helpers/designFidelity";
import {
	AUTHOR,
	HOD,
	HOPF,
	PASSWORD,
	expectReady,
	gotoRequisitions,
	resetFixture,
	restoreSite,
} from "../requisitions/helpers";

/**
 * Procurement Requisitions design-fidelity gate (REQ-CHG-001 v1.6, AGENTS.md
 * §6.6). Every artboard's ordered structural landmarks (card titles, field
 * labels, table headers, buttons) must appear in order on the live screen.
 * Data values are never compared.
 *
 * Unlike Procurement Planning's one-artboard-per-file convention, every
 * REQ-CHG-001 artboard lives in one combined file
 * (`REQ-CHG-001 Artboards.dc.html`) as an `<sc-if value="{{ is.desNN }}">`
 * block, toggled at runtime by `support.js` — which `openArtboard` blocks to
 * get the artboard's own raw, un-re-rendered markup. With that script
 * blocked every `<sc-if>` block paints simultaneously (confirmed live:
 * height>0 on all eleven), so this spec scopes each artboard to its own
 * block with a plain CSS attribute selector on the still-unparsed
 * `value="{{ is.desNN }}"` text — `sc-if[value*="is.desNN"] > div` — rather
 * than extending the shared `designFidelity.ts` helper (the risk the
 * implementation plan flagged before this slice began).
 */

const ARTBOARD_FILE = "docs/mvp-1-r1/06_requisitions/design/REQ-CHG-001 Artboards.dc.html";
const LIVE_SCOPE = '.kt-req [data-testid="req-shell"]';

function artboardScope(id: string): string {
	return `sc-if[value*="is.${id}"] > div`;
}

/**
 * Some landmarks embed a data value in their own text (e.g. "Technical
 * requirements — 11 confirmed rows") — the row count differs legitimately
 * between the artboard's 2-item MOH fixture and this world's own
 * deliberately single-item Plan Item (same reasoning as REQ-DES-04's own
 * documented delta above). Strip the leading count so only the structural
 * wording is compared, never the data value itself.
 */
function stripCounts(list: string[]): string[] {
	return list.map((text) => text.replace(/— \d+ (confirmed rows?|rows?|items?)/, "— N $1"));
}

async function artboardLandmarks(browser: any, id: string): Promise<{ wanted: string[]; art: Page }> {
	const art = await browser.newPage();
	await openArtboard(art, ARTBOARD_FILE, artboardScope(id));
	return { wanted: await landmarks(art, artboardScope(id)), art };
}

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Procurement Requisitions — design fidelity", () => {
	test.afterAll(() => restoreSite());

	test("REQ-DES-01 — Workspace", async ({ page, browser }) => {
		resetFixture("reset_eligible_item_world");
		const { wanted, art } = await artboardLandmarks(browser, "des01");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "REQ-DES-01");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("REQ-DES-02 — Start Requisition", async ({ page, browser }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_eligible_item_world");
		const { wanted, art } = await artboardLandmarks(browser, "des02");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/new/${state.plan_item_id}`);
		await expectReady(page, "start");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "REQ-DES-02");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("REQ-DES-03 — Step 1: Request and drawdown", async ({ page, browser }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des03");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "REQ-DES-03");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("REQ-DES-04 — Step 2: Equipment items", async ({ page, browser }) => {
		// `reset_editor_review_fixture` already confirms every proposed
		// baseline row (it builds the Step-5-ready package), so §13.6A's own
		// "still Proposed" banner — the artboard's own Characteristic/
		// Comparison/Proposed value/Status table — would never appear; add
		// the item live instead, the same command sequence
		// requisitions-editor-drawdown-items.spec.ts already proves, so the
		// baseline rows are freshly proposed and still unconfirmed.
		const state = resetFixture<{ requisition: string }>("reset_editor_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des04");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="req-step-2"]').click();
		await page.locator('[data-testid="req-add-item"]').click();
		await page.locator("#item-source").selectOption({ index: 1 });
		await page.locator("#item-category").selectOption("Laptop");
		await page.locator("#item-name").fill("Business laptops");
		await page.locator("#item-use").fill("Playwright fixture deployment testing");
		await page.locator("#item-location").selectOption({ label: "Playwright — Requisitions Delivery Location" });
		await page.locator("#item-date").fill("2099-12-31");
		await page.locator('[data-testid="req-item-dialog-confirm"]').click();
		await expect(page.locator('[data-testid="req-item-dialog"]')).toHaveCount(0);
		// The baseline-proposal banner renders from a fresh read after the
		// item is added — wait for it explicitly rather than racing the
		// landmark measurement against that round-trip.
		await expect(page.locator('[data-testid^="req-baseline-banner-"]')).toBeVisible();
		// Known, deliberate delta (mirrors Planning's own fidelity spec
		// precedent): the artboard's own fixture has two items, so its own
		// baseline-proposal notice repeats one Characteristic/Comparison/
		// Proposed value/Status table per item. This world's own REQ-402
		// Plan Item is deliberately single-source (D13-equivalent scope
		// simplification, same reasoning as C5/FU-03's registered one-item
		// vs two-item gap), so only the first such group can ever appear
		// here — strip the artboard's own second, identical repeat before
		// the subsequence check rather than asserting a group this world
		// structurally cannot produce.
		const dedupedWanted: string[] = [];
		let seenStatusOnce = false;
		for (const landmark of wanted) {
			if (seenStatusOnce && ["Characteristic", "Comparison", "Proposed value", "Status"].includes(landmark)) continue;
			dedupedWanted.push(landmark);
			if (landmark === "Status") seenStatusOnce = true;
		}
		expectLandmarkSubsequence(dedupedWanted, await landmarks(page, LIVE_SCOPE), "REQ-DES-04");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("REQ-DES-05 — Step 3: Technical and support", async ({ page, browser }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_review_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des05");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="req-step-3"]').click();
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "REQ-DES-05");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("REQ-DES-06 — Step 4: Services and acceptance", async ({ page, browser }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_review_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des06");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="req-step-4"]').click();
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "REQ-DES-06");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("REQ-DES-07 — Step 5: Review and submit", async ({ page, browser }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_review_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des07");
		const errors = collectPageErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="req-step-5"]').click();
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "REQ-DES-07");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("REQ-DES-08 — Department approval task", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_department_task_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des08");
		const errors = collectPageErrors(page);
		await login(page, HOD, PASSWORD);
		await gotoRequisitions(page, `/department-task/${state.task}`);
		await expectReady(page, "department-task");
		expectLandmarkSubsequence(stripCounts(wanted), stripCounts(await landmarks(page, LIVE_SCOPE)), "REQ-DES-08");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("REQ-DES-09 — Procurement authorisation task", async ({ page, browser }) => {
		const state = resetFixture<{ task: string }>("reset_procurement_task_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des09");
		const errors = collectPageErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/procurement-task/${state.task}`);
		await expectReady(page, "procurement-task");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "REQ-DES-09");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("REQ-DES-10 — Authorised Requisition", async ({ page, browser }) => {
		const state = resetFixture<{ requisition: string }>("reset_authorised_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des10");
		const errors = collectPageErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}/authorised`);
		await expectReady(page, "authorised");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "REQ-DES-10");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});
});
