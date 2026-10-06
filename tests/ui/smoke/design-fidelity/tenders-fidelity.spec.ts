import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { artboardUrl, collectPageErrors, expectLandmarkSubsequence, landmarks, onceEach, openArtboard, LandmarkExemption } from "../../helpers/designFidelity";
import {
	AO,
	HOPF,
	OFFICER,
	PASSWORD,
	expectReady,
	gotoTenders,
	resetFixture,
	restoreSite,
} from "../tenders/helpers";

/**
 * TPR-CHG-001 v0.8 design-fidelity gate (AGENTS.md §6.6). One artboard per
 * file (no combined `sc-if` pack, unlike Requisitions): each `.dc.html` is
 * opened directly with support.js blocked, which freezes it at its own
 * default `state` — the variant compared here in each case. Only structural
 * landmarks (card titles, field labels, table headers, buttons), in order,
 * are compared; values are never compared.
 */

const DESIGN = "docs/mvp-1-r1/11_tenders/design";
const LIVE = '.kt-tnd [data-testid="tnd-shell"]';
const START_DIALOG_LIVE = '.kt-tnd [data-testid="tnd-start-dialog"]';

/**
 * A `sc-for` row template's own mustache placeholder (`{{row.action}}`) never
 * resolves without the dc-runtime this gate deliberately blocks (see
 * `openArtboard`'s own comment): the row is drawn once, literally, with its
 * placeholder text intact. It is template markup, not content — drop it the
 * same way this gate already never compares data values.
 */
function dropUnresolvedTemplateText(list: string[]): string[] {
	return list.filter((text) => !/^\{\{.*\}\}$/.test(text));
}

const LANDMARK_SELECTOR = ".kt-card-title, .dialog-title, .kt-section-title, .dialog-title, label, legend, .kt-label, th, button";

/**
 * `sc-if` is the design tool's own runtime conditional; with support.js
 * blocked (this gate's whole method — see `openArtboard`) it is inert, so
 * EVERY `sc-if` block paints unconditionally, including ones the artboard's
 * own `hint-placeholder-val="{{false}}"` says are hidden by default (a Yes/No
 * toggle's "Yes" branch, a closed drawer, an unopened dialog). Landmarks
 * inside such a block are never what the artboard's own default state shows,
 * so they are excluded here — the one generic rule every board needs, rather
 * than a per-board branch selector. A block whose default hint is
 * `{{true}}` (already open/visible) is kept.
 */
async function defaultStateLandmarks(page: any, scope: string): Promise<string[]> {
	return page.evaluate(
		({ scope, selector }: { scope: string; selector: string }) => {
			const root = document.querySelector(scope);
			if (!root) return [] as string[];
			const hiddenByDefault = Array.from(root.querySelectorAll('sc-if[hint-placeholder-val="{{false}}"]'));
			const texts: string[] = [];
			for (const el of Array.from(root.querySelectorAll(selector)) as HTMLElement[]) {
				if (!el.getClientRects().length) continue;
				if (hiddenByDefault.some((hidden) => (hidden as HTMLElement).contains(el))) continue;
				const text = (el.textContent || "").replace(/\s+/g, " ").trim();
				if (text) texts.push(text);
			}
			return texts;
		},
		{ scope, selector: LANDMARK_SELECTOR }
	);
}

async function artboardLandmarks(browser: any, file: string, label: string, scopeOverride?: string): Promise<string[]> {
	const art = await browser.newPage();
	const scope = scopeOverride || `[data-screen-label="${label}"]`;
	await openArtboard(art, `${DESIGN}/${file}`, scope);
	const wanted = dropUnresolvedTemplateText(await defaultStateLandmarks(art, scope));
	await art.close();
	return wanted;
}

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("Tenders — design fidelity", () => {
	test.afterAll(() => restoreSite());

	test("TPR-DES-01 — Tenders workspace", async ({ page, browser }) => {
		resetFixture("reset_start_fixture");
		// with support.js blocked the artboard's own sc-if empty/non-empty
		// branches both render unconditionally (raw markup, un-interpolated),
		// duplicating "Clear filters" — a design-tool artifact of the inert
		// runtime, never a live-page gap; onceEach dedupes it the same way the
		// shared helper already documents for repeated fixture rows.
		const wanted = onceEach(await artboardLandmarks(browser, "Tenders Workspace.dc.html", "TPR-DES-01 Tenders workspace"));
		const errors = collectPageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page);
		await expectReady(page, "workspace");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-01");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-02 — Start Tender dialog", async ({ page, browser }) => {
		const state = resetFixture<{ handoff: string }>("reset_start_fixture");
		// this one board has no `data-screen-label` attribute — its label lives
		// only in the switcher header text; and its blurred background is a
		// fake placeholder card ("Tenders"/two skeleton bars), not the real
		// workspace, so the dialog itself (not `.dialog-demo`) is the subject.
		const wanted = await artboardLandmarks(browser, "Start Tender Dialog.dc.html", "TPR-DES-02 Start Tender dialog", ".dialog-backdrop .dialog");
		const errors = collectPageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/new/${state.handoff}`);
		await expectReady(page, "start");
		expectLandmarkSubsequence(wanted, await landmarks(page, START_DIALOG_LIVE), "TPR-DES-02");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-03 — Draft: Tender details", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string }>("reset_draft_fixture");
		const wanted = await artboardLandmarks(browser, "Draft - Tender Details.dc.html", "TPR-DES-03 Draft Tender details");
		const errors = collectPageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/details`);
		await expectReady(page, "details");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-03");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-04 — Draft: Supplier and contract requirements", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string }>("reset_draft_complete_fixture");
		const wanted = await artboardLandmarks(browser, "Draft - Supplier and Contract Requirements.dc.html", "TPR-DES-04 Draft supplier and contract requirements");
		const errors = collectPageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/requirements`);
		await expectReady(page, "requirements");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-04");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-05 — Review and submit", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string }>("reset_draft_complete_fixture");
		const wanted = await artboardLandmarks(browser, "Review and Submit.dc.html", "TPR-DES-05 Review and submit");
		const errors = collectPageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/review`);
		await expectReady(page, "review");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-05");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-06 — HOPF approval", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string }>("reset_awaiting_hopf_fixture");
		const wanted = await artboardLandmarks(browser, "HOPF Approval.dc.html", "TPR-DES-06 HOPF approval");
		const errors = collectPageErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "approval");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-06");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-07 — AO publication authorisation", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string }>("reset_awaiting_ao_fixture");
		const wanted = await artboardLandmarks(browser, "AO Publication Authorisation.dc.html", "TPR-DES-07 AO publication authorisation");
		const errors = collectPageErrors(page);
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "authorisation");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-07");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-08 — Publication confirmation", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string }>("reset_publication_fixture", { confirmed: 2 });
		// The invalid-evidence variant's State Portal row sits in an `sc-if`
		// inside <tbody>; the HTML parser hoists the wrapper out of the table,
		// so the row paints even though its hint hides it. The repeated
		// "Confirm publication" is that artifact, not a live-page gap.
		const wanted = onceEach(await artboardLandmarks(browser, "Publication Progress and Evidence.dc.html", "TPR-DES-08 Publication confirmation"));
		const errors = collectPageErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/publication`);
		await expectReady(page, "publication");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-08");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-09 — Published Tender", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string }>("reset_published_fixture", { with_addendum: true, with_clarification: true, answered: true });
		const wanted = await artboardLandmarks(browser, "Published Tender.dc.html", "TPR-DES-09 Published Tender");
		const errors = collectPageErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-09");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-10 — Prepare and issue addendum", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string; addendum: string }>("reset_addendum_draft_fixture");
		const wanted = await artboardLandmarks(browser, "Prepare and Issue Addendum.dc.html", "TPR-DES-10 Prepare and issue addendum");
		const errors = collectPageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-10");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-11 — Respond to supplier clarification", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string; clarification: string }>("reset_clarification_fixture");
		const wanted = await artboardLandmarks(browser, "Respond to Supplier Clarification.dc.html", "TPR-DES-11 Respond to supplier clarification");
		const errors = collectPageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/clarifications/${state.clarification}`);
		await expectReady(page, "clarification");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-11");
		expect(errors, "console errors").toEqual([]);
	});

	test("TPR-DES-12 — Cancel Tender", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string }>("reset_cancel_fixture");
		const wanted = await artboardLandmarks(browser, "Cancel Tender.dc.html", "TPR-DES-12 Cancel Tender");
		const errors = collectPageErrors(page);
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-12");
		expect(errors, "console errors").toEqual([]);
	});

	// TPR-DES-13's default artboard state is "Correction requested" (the
	// "Returned" Draft is TPR-DES-04's returned variant, compared there).
	test("TPR-DES-13 — Requisition correction", async ({ page, browser }) => {
		const state = resetFixture<{ tender_reference: string }>("reset_correction_requested_fixture");
		const wanted = await artboardLandmarks(browser, "Requisition Correction.dc.html", "TPR-DES-13 Requisition correction");
		const errors = collectPageErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "correction");
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE), "TPR-DES-13");
		expect(errors, "console errors").toEqual([]);
	});

	// TPR-DES-14 (v0.12) draws its states from a list in the board's own
	// script, so the raw markup holds one template card. Every variant the
	// board lists must be one the live CommonState draws (its copy and
	// actions are compared per kind by the component tests).
	test("TPR-DES-14 — Common states", async () => {
		const fs = await import("node:fs");
		const path = await import("node:path");
		const source = fs.readFileSync(path.resolve(__dirname, "../../../../", `${DESIGN}/Common States.dc.html`), "utf8");
		const variants = Array.from(source.matchAll(/\['(?:critical|attention|info)', '([^']+)'/g)).map((m) => m[1]);
		expect(variants.length).toBeGreaterThanOrEqual(16);
		const LIVE_KIND: Array<[RegExp, string]> = [
			[/^Forbidden/, "forbidden"], [/^Not found/, "not-found"], [/^Source unavailable/, "source-unavailable"], [/^Already started — Brian/, "already-started"],
			[/^Already started — viewer without/, "requisition-unavailable"], [/^Template unavailable/, "template-unavailable"], [/^Bound release Superseded/, "release-superseded"],
			[/^Bound release Withdrawn/, "release-withdrawn"], [/^Bound release integrity failed/, "release-failed"], [/^Publication not configured/, "rule-unavailable"],
			[/^Stale write/, "stale"], [/^Load failure/, "failure"],
		];
		const unmapped = variants.filter((v) => !LIVE_KIND.some(([re]) => re.test(v)));
		expect(unmapped, "board variants with no live common state").toEqual([]);
	});
});
