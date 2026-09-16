import { expect, test, Page } from "@playwright/test";

import { loginAsNdsFixtureAuthor, loginAsNdsFixtureReviewer } from "../../helpers/auth";
import { collectPageErrors, expectLandmarkSubsequence, openArtboard } from "../../helpers/designFidelity";
import {
	clearFixtures,
	expectScreen,
	gotoNeeds,
	purgeUntaggedNeedsSince,
	resetFixture,
	selectContext,
	siteNow,
} from "../departmental_needs/helpers";

/**
 * Departmental Needs design-fidelity gate (NDS-CHG-001 v1.13 §11, AGENTS.md
 * §6.6). Every artboard's ordered structural landmarks (card titles, field
 * labels, row labels, table headers, buttons) must appear in order on the
 * live screen. Data values are never compared.
 *
 * All artboards live in one file (`Departmental Needs - Design Board.dc.html`),
 * one `<div id="des…">` per screen. Each screen's primary composition is the
 * direct-child `.kt-panel-lg`; a handful of screens (DES-08/11/12) also carry
 * trailing compact state-variant cards as later siblings of that panel — this
 * gate scopes to `#desNN > .kt-panel-lg` specifically so a variant card's own
 * buttons/labels (e.g. DES-12's CLEAR card offering "Approve withdrawal")
 * never leak into the primary composition's expected landmark list. Those
 * variant cards, and NDS-DES-07A/13/14/15's dense standalone variant sets,
 * are covered by the functional Playwright specs and live verification, not
 * this structural gate — see FOLLOW_UPS FU-27 for the two variants that need
 * a genuine backend addition before they can be built at all.
 */

const ARTBOARD_FILE = "docs/mvp-1-r1/01_departmental_needs/design/Departmental Needs - Design Board.dc.html";
const LIVE_SCOPE = '[data-testid="nds-shell"]';

function panelScope(id: string): string {
	return `#${id} > .kt-panel-lg`;
}

/**
 * NDS's own landmark selector, not the shared `designFidelity.landmarks()`
 * one, for two board-specific reasons (kept local so no other module's gate
 * is affected):
 *
 *  1. The board's disabled-control convention is `<span class="btn …">`, not
 *     a real `<button>` — the shared selector's `button` clause matches
 *     nothing on the artboard side for this board, so footer/header action
 *     labels are added here as `.btn`.
 *  2. A table row's reference number is styled `.kt-label` on the artboard
 *     (`<td><div class="kt-label">NDS-MOH-2027-0001</div></td>`) purely for
 *     muted-text appearance — it is fixture data, not a structural label,
 *     and the live table never uses that class for its own reference cell.
 *     `.kt-label` elements nested inside a table cell are excluded so a
 *     fixture's generated reference number never becomes a required landmark.
 */
async function panelLandmarks(page: Page, scope: string): Promise<string[]> {
	return page.evaluate((scope) => {
		const root = document.querySelector(scope);
		if (!root) return [] as string[];
		const selector = ".kt-card-title, .kt-dialog-title, .dialog-title, label, legend, .kt-label, th, button, .btn";
		const texts: string[] = [];
		for (const el of Array.from(root.querySelectorAll<HTMLElement>(selector))) {
			if (!el.getClientRects().length) continue;
			if (el.classList.contains("kt-label") && el.closest("td")) continue;
			const text = (el.textContent || "").replace(/\s+/g, " ").trim();
			if (text) texts.push(text);
		}
		return texts;
	}, scope);
}

/**
 * A generated Need reference (`NDS-MOH-2027-0736` live vs. the artboard's own
 * canonical `NDS-MOH-2027-0001`) appears as its own landmark on several
 * screens — a standalone `.kt-label` line under the heading (DES-04/05/06/
 * 07/08/09) as well as inside DES-12's compound "Need X · Withdrawal request
 * Y · Accepted revision N" line. Collapse every occurrence, in isolation or
 * embedded in a longer line, to one placeholder token so a fixture's own
 * generated identifiers never fail the comparison — structure, not data, is
 * the contract (this file's own header comment).
 */
const REFERENCE_PATTERN = /\b(?:NDS-[A-Z]+-\d{4}-\d+|NDS-WDR-[A-Z0-9-]+)\b/g;
function stripFixtureReferences(list: string[]): string[] {
	return list.map((text) => text.replace(REFERENCE_PATTERN, "‹reference›"));
}

async function artboardLandmarks(browser: any, id: string): Promise<{ wanted: string[]; art: Page }> {
	const art = await browser.newPage();
	await openArtboard(art, ARTBOARD_FILE, panelScope(id));
	return { wanted: stripFixtureReferences(await panelLandmarks(art, panelScope(id))), art };
}

async function liveLandmarks(page: Page): Promise<string[]> {
	return stripFixtureReferences(await panelLandmarks(page, LIVE_SCOPE));
}

test.describe.configure({ mode: "default", timeout: 240_000 });

// Captured before any test runs. DES-04/08/09 reach their target states
// through real UI create/submit/propose-change clicks, minting Needs no
// fixture builder stamps — `purgeUntaggedNeedsSince()` sweeps those up by
// creation time instead (see FOLLOW_UPS.md, NDS-CHG-001 tracker NDS13-406).
// Must be the site's own clock (`siteNow()`), not a JS `Date` — `creation`
// is a naive site-local timestamp and a UTC-labelled cutoff reads ~3 hours
// early, catching more than this run actually created.
const SUITE_STARTED_AT = siteNow();

test.describe("Departmental Needs — design fidelity", () => {
	test.afterAll(() => {
		clearFixtures();
		purgeUntaggedNeedsSince(SUITE_STARTED_AT);
	});

	test("NDS-DES-01 — Author workspace", async ({ page, browser }) => {
		const fixture = resetFixture<{ need: string }>("reset_open_intake_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des01");
		const errors = collectPageErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await expect(page.locator(`[data-reference="${fixture.need}"]`)).toBeVisible();
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des01");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("NDS-DES-02 — HoD shared workspace", async ({ page, browser }) => {
		// `reset_review_task_fixture` builds exactly one Need, which is
		// necessarily in the decision queue — §11.3's register section
		// deliberately excludes queued rows (NDS13-301), so it renders empty
		// here rather than the artboard's own two-row register. The queue
		// section (the part this row actually added) is the real fidelity
		// question; truncate the wanted list there rather than asserting
		// against an empty-state composition no fixture in this file builds.
		resetFixture("reset_review_task_fixture");
		const { wanted: full, art } = await artboardLandmarks(browser, "des02");
		const wanted = full.slice(0, full.indexOf("All departmental needs"));
		const errors = collectPageErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des02");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("NDS-DES-03 — Create a departmental need", async ({ page, browser }) => {
		resetFixture("reset_open_intake_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des03");
		const errors = collectPageErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "/new");
		await expectScreen(page, "editor");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des03");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("NDS-DES-04 — Returned correction", async ({ page, browser }) => {
		const fixture = resetFixture<{ need: string; task: string }>("reset_review_task_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des04");
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, `/review/${fixture.task}`);
		await expectScreen(page, "task");
		await page.locator('[data-testid="nds-decision-return"]').click();
		await page.locator('[data-testid="nds-dialog-reason"]').fill("Confirm the quantity against the current cohort.");
		await page.locator('[data-testid="nds-dialog-confirm"]').click();
		await expect(page.locator('[data-testid="nds-dialog-reason"]')).toHaveCount(0);

		const errors = collectPageErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, `/${fixture.need}/edit`);
		await expectScreen(page, "editor");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des04");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("NDS-DES-05 — Submitted detail", async ({ page, browser }) => {
		const fixture = resetFixture<{ need: string }>("reset_review_task_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des05");
		const errors = collectPageErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, `/${fixture.need}`);
		await expectScreen(page, "detail");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des05");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("NDS-DES-06 — Initial HoD review", async ({ page, browser }) => {
		const fixture = resetFixture<{ task: string }>("reset_review_task_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des06");
		const errors = collectPageErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, `/review/${fixture.task}`);
		await expectScreen(page, "task");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des06");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("NDS-DES-07 — Accepted requirement and Planning status", async ({ page, browser }) => {
		const fixture = resetFixture<{ need: string }>("reset_accepted_source_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des07");
		const errors = collectPageErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, `/${fixture.need}`);
		await expectScreen(page, "detail");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des07");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("NDS-DES-08 — Propose changes to an accepted Need", async ({ page, browser }) => {
		const fixture = resetFixture<{ need: string }>("reset_accepted_source_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des08");
		const errors = collectPageErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, `/${fixture.need}`);
		await expectScreen(page, "detail");
		await page.locator('[data-testid="nds-owner-action"][data-action="create-update"]').click();
		await expectScreen(page, "editor");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des08");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("NDS-DES-09 — HoD review of proposed changes", async ({ page, browser }) => {
		const fixture = resetFixture<{ need: string }>("reset_accepted_source_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des09");
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, `/${fixture.need}`);
		await expectScreen(page, "detail");
		await page.locator('[data-testid="nds-owner-action"][data-action="create-update"]').click();
		await expectScreen(page, "editor");
		await page.locator('[data-testid="nds-required-by"]').fill("2028-04-30");
		await page.locator('[data-testid="nds-submit"]').click();
		await expectScreen(page, "detail");

		const errors = collectPageErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, `/${fixture.need}`);
		await expectScreen(page, "detail");
		await page.locator('[data-testid="nds-detail-review"]').click();
		await expectScreen(page, "task");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des09");
		expect(errors).toEqual([]);
		await art.close();
	});

	test("NDS-DES-12 — Withdrawal review (blocked)", async ({ page, browser }) => {
		const fixture = resetFixture<{ need: string }>("reset_withdrawal_blocked_fixture");
		const { wanted, art } = await artboardLandmarks(browser, "des12");
		const errors = collectPageErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await page
			.locator(
				`[data-testid="nds-need-row"][data-reference="${fixture.need}"] [data-testid="nds-row-action"][data-action="withdrawal"]`,
			)
			.click();
		await expectScreen(page, "withdrawal");
		expectLandmarkSubsequence(wanted, await liveLandmarks(page), "des12");
		expect(errors).toEqual([]);
		await art.close();
	});
});
