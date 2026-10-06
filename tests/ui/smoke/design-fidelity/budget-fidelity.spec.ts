import { test, expect, Page } from "@playwright/test";
import { openArtboard, expectLandmarkSubsequence, expectStructure } from "../../helpers/designFidelity";
import { DEPARTURES } from "../../fidelity/departures/budget.js";
import {
	ADMIN,
	APPROVER,
	AUDITOR,
	CANONICAL_FY,
	NOBODY,
	OFFICER,
	ClosureFixture,
	ConversionFixture,
	EmptyYearFixture,
	PendingFixture,
	SuccessorFixture,
	collectConsoleErrors,
	expectScreen,
	gotoBudget,
	login,
	resetFixture,
	selectYear,
} from "../budget/helpers";

/**
 * Budget & Funding design-fidelity gate — BUD-CHG-001 v1.9 (AGENTS.md §6.6
 * enforcement, tracker BUD19-403).
 *
 * Renders each reconciled `.dc.html` board in the same browser, puts it into
 * one named switcher state (the boards are multi-state: `<sc-if value="{{x}}">`
 * blocks and `{{placeholder}}` text, resolved here from a per-test map with the
 * dc-runtime blocked), derives the board's ordered structural landmarks
 * (card titles, dialog titles, labels, table headers, buttons, tabs) and
 * asserts the live route's own landmarks contain that sequence in order.
 *
 * Fixture data (ids, dates, amounts, names) is exempt; structure is not.
 * Landmarks whose text is fixture data (a dialog title carrying the year) are
 * dropped explicitly per test, never silently.
 */

const DESIGN_DIR = "docs/mvp-1-r1/03_budget/design";
const ART = "x-dc";
const LIVE = ".kt-industry";

const LIVE_SELECTOR = [".kt-card-title", ".dialog-title", "label", "legend", ".kt-label", "th", "button", ".kt-tab"].join(", ");
const ART_SELECTOR = [".kt-card-title", ".dialog-title", ".dialog-title", "label", "legend", ".kt-label", "th", "button"].join(", ");

type Vals = Record<string, string | boolean>;

/**
 * One resolved board, read by both instruments.
 *
 * `texts` is the ordered landmark copy the subsequence gate has always
 * compared; `html` is the same board's markup, which the structural gate
 * reduces to its landmark skeleton. They come from a single visit and a single
 * state resolution on purpose — resolving the board twice would let a
 * structural failure turn out to be a state the text gate never saw.
 */
type Board = { texts: string[]; html: string };

async function boardLandmarks(art: Page, file: string, vals: Vals, drops: string[] = []): Promise<Board> {
	await openArtboard(art, `${DESIGN_DIR}/${file}`, ART);
	const { texts, html } = await art.evaluate(
		({ scope, selector, vals }) => {
			const root = document.querySelector(scope)!;
			// The state switcher bar is design tooling, not the screen.
			root.querySelectorAll("button").forEach((b) => {
				if ((b.getAttribute("onclick") || "").startsWith("{{set")) b.remove();
			});
			// <sc-if value="{{name}}"> keeps its children only when vals[name] is true.
			const ifs = Array.from(root.querySelectorAll("sc-if")).reverse();
			for (const el of ifs) {
				const key = (el.getAttribute("value") || "").replace(/[{}]/g, "");
				const keep = Object.prototype.hasOwnProperty.call(vals, key) ? !!vals[key] : (el.getAttribute("hint-placeholder-val") || "").includes("true");
				if (!keep) el.remove();
			}
			const out: string[] = [];
			for (const el of Array.from(root.querySelectorAll<HTMLElement>(selector))) {
				if (!el.getClientRects().length) continue;
				let text = (el.textContent || "").replace(/\s+/g, " ").trim();
				text = text.replace(/\{\{(\w+)\}\}/g, (_m, k) => (typeof vals[k] === "string" ? String(vals[k]) : ""));
				text = text.replace(/\s+/g, " ").trim();
				if (text && !text.includes("{{")) out.push(text);
			}
			// The boards parameterise attributes as well as text: the lines
			// editor draws its reconciliation banner as `class="{{noticeClass}}"`,
			// resolved per state to `kt-notice is-live` or `kt-notice is-warning`.
			// Reading the markup without resolving those leaves the element
			// carrying a literal `{{noticeClass}}`, which is no landmark at all,
			// so the banner reads as a container the board never drew. Same
			// substitution the text pass above already does, applied to every
			// attribute.
			for (const el of Array.from(root.querySelectorAll<HTMLElement>("*"))) {
				for (const attr of Array.from(el.attributes)) {
					if (!attr.value.includes("{{")) continue;
					const resolved = attr.value.replace(/\{\{(\w+)\}\}/g, (m, k) =>
						typeof vals[k] === "string" ? String(vals[k]) : m
					);
					if (resolved !== attr.value) el.setAttribute(attr.name, resolved);
				}
			}
			return { texts: out, html: root.outerHTML };
		},
		{ scope: ART, selector: ART_SELECTOR, vals }
	);
	return { texts: texts.filter((t) => !drops.includes(t)), html };
}

async function liveLandmarks(page: Page): Promise<string[]> {
	return page.evaluate(
		({ scope, selector }) => {
			const root = document.querySelector(scope);
			if (!root) return [];
			const out: string[] = [];
			for (const el of Array.from(root.querySelectorAll<HTMLElement>(selector))) {
				if (!el.getClientRects().length) continue;
				const text = (el.textContent || "").replace(/\s+/g, " ").trim();
				if (text) out.push(text);
			}
			return out;
		},
		{ scope: LIVE, selector: LIVE_SELECTOR }
	);
}

async function withBoard(browser: any, file: string, vals: Vals, drops: string[] = []): Promise<Board> {
	const art = await browser.newPage();
	try {
		return await boardLandmarks(art, file, vals, drops);
	} finally {
		await art.close();
	}
}

async function openWorkspace(page: Page, user: string, fy: string) {
	await login(page, user);
	await gotoBudget(page);
	await selectYear(page, fy);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
}

test.describe.configure({ mode: "serial" });

test.describe("Budget & Funding — design fidelity (v1.9 boards)", () => {
	const WS = "Budget & Funding Workspace.dc.html";
	const DETAIL = "Budget Detail Workspace.dc.html";
	const LINE = "Budget Line Detail.dc.html";
	const TASK = "Approval Task.dc.html";
	const REG = "Register Approved Budget.dc.html";
	const EDITOR = "Draft Budget Lines Editor.dc.html";
	const SUCC = "Successor Revision Draft.dc.html";

	test("BUD-DES-01 workspace, Active", async ({ page, browser }) => {
		resetFixture("reset_default");
		const wanted = await withBoard(browser, WS, { isActive: true, isPendingCard: false });
		const errors = collectConsoleErrors(page);
		await openWorkspace(page, AUDITOR, CANONICAL_FY);
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-01");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-01");
		expect(errors).toEqual([]);
	});

	test("BUD-DES-01B initial draft / submitted / returned", async ({ page, browser }) => {
		const draft = resetFixture<PendingFixture>("reset_initial_draft");
		let wanted = await withBoard(browser, WS, { isActive: false, isPendingCard: true, isReturned: false, pendingAction: "Continue draft", pendingWhoLabel: "Created by", pendingWhenLabel: "Last saved" });
		await openWorkspace(page, OFFICER, draft.pending.fiscal_year);
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-01B initial draft");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-01B initial draft");

		const submitted = resetFixture<PendingFixture>("reset_initial_submitted");
		wanted = await withBoard(browser, WS, { isActive: false, isPendingCard: true, isReturned: false, pendingAction: "Review", pendingWhoLabel: "Submitted by", pendingWhenLabel: "Submitted" });
		await openWorkspace(page, APPROVER, submitted.pending.fiscal_year);
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-01B initial submitted");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-01B initial submitted");

		const returned = resetFixture<PendingFixture>("reset_returned_draft");
		wanted = await withBoard(browser, WS, { isActive: false, isPendingCard: true, isReturned: true, pendingAction: "Correct and resubmit", pendingWhoLabel: "Submitted by", pendingWhenLabel: "Returned" });
		await openWorkspace(page, OFFICER, returned.pending.fiscal_year);
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-01B returned");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-01B returned");
	});

	test("BUD-DES-01A/01B current with an update (draft, submitted, technical reader)", async ({ page, browser }) => {
		resetFixture<SuccessorFixture>("reset_successor_draft");
		let wanted = await withBoard(browser, WS, { isActive: true, isPendingCard: true, isReturned: false, pendingAction: "Continue update", pendingWhoLabel: "Created by", pendingWhenLabel: "Last saved" });
		await openWorkspace(page, OFFICER, CANONICAL_FY);
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-01B current + draft");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-01B current + draft");

		resetFixture<SuccessorFixture>("reset_successor_submitted");
		wanted = await withBoard(browser, WS, { isActive: true, isPendingCard: true, isReturned: false, pendingAction: "View version (read-only)", pendingWhoLabel: "Submitted by", pendingWhenLabel: "Submitted" });
		await openWorkspace(page, ADMIN, CANONICAL_FY);
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-01A technical reader");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-01A technical reader");
	});

	test("BUD-DES-16 workspace states: no baseline, forbidden, server error, loading", async ({ page, browser }) => {
		const fx = resetFixture<EmptyYearFixture>("reset_no_budget_year");
		let wanted = await withBoard(browser, WS, { isActive: false, showWorkspace: false, isNoBaseline: true });
		await openWorkspace(page, OFFICER, fx.empty_fiscal_year);
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-16 no baseline");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-16 no baseline", DEPARTURES["BudgetWorkspaceScreen#BUD-DES-16-no-baseline"]);

		await login(page, NOBODY);
		await gotoBudget(page);
		await expect(page.getByTestId("bud-forbidden")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("budget-fy-filter")).toHaveCount(0);
		await expect(page.locator(".modal.show")).toHaveCount(0);

		wanted = await withBoard(browser, WS, { isActive: false, showWorkspace: false, isServerError: true });
		await login(page, OFFICER);
		await page.route("**/api/method/kentender_budget.api.budget_api.get_budget_workspace", (route) => route.fulfill({ status: 500, body: "boom" }));
		await gotoBudget(page);
		await selectYear(page, CANONICAL_FY);
		await gotoBudget(page);
		await expect(page.getByTestId("bud-ws-server-error")).toBeVisible({ timeout: 30_000 });
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-16 server error");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-16 server error", DEPARTURES["BudgetWorkspaceScreen#BUD-DES-16-server-error"]);
		await page.unrouteAll({ behavior: "ignoreErrors" });

		await page.route("**/api/method/kentender_budget.api.budget_api.get_budget_workspace", () => undefined);
		await gotoBudget(page);
		await expect(page.getByTestId("bud-ws-skeleton")).toBeVisible({ timeout: 30_000 });
		expect(await page.locator(".kt-skel").count()).toBeGreaterThanOrEqual(6);
		await page.unrouteAll({ behavior: "ignoreErrors" });
	});

	test("BUD-DES-02 record approved allocation", async ({ page, browser }) => {
		const fx = resetFixture<EmptyYearFixture>("reset_no_budget_year");
		const wanted = await withBoard(browser, REG, {});
		await login(page, OFFICER);
		await gotoBudget(page);
		await selectYear(page, fx.empty_fiscal_year);
		await gotoBudget(page, "/new");
		await expectScreen(page, "register");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-02");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-02");
	});

	test("BUD-DES-03 draft budget lines editor", async ({ page, browser }) => {
		const fx = resetFixture<PendingFixture>("reset_initial_draft");
		const wanted = await withBoard(browser, EDITOR, { hwdAmount: "KES 60,000,000", entered: "KES 160,000,000", noticeClass: "kt-notice is-live", noticeText: "Budget lines match the approved allocation." });
		await login(page, OFFICER);
		await gotoBudget(page, `/${fx.pending.budget_code}/version/1/edit/lines`);
		await expectScreen(page, "editor");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-03");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-03");
	});

	test("BUD-DES-14/15 successor draft, approval details and lines, and Changes requested", async ({ page, browser }) => {
		const fx = resetFixture<SuccessorFixture>("reset_successor_draft");
		let wanted = await withBoard(browser, SUCC, { isOverview: true, isLines: false, isReturned: false, statusLabel: "Draft" });
		await login(page, OFFICER);
		await gotoBudget(page, `/${fx.budget_code}/version/${fx.v2_number}/edit`);
		await expectScreen(page, "editor");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-14");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-14");
		wanted = await withBoard(browser, SUCC, { isOverview: false, isLines: true, isReturned: false, statusLabel: "Draft" });
		await gotoBudget(page, `/${fx.budget_code}/version/${fx.v2_number}/edit/lines`);
		await expectScreen(page, "editor");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-15");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-15");

		const returned = resetFixture<SuccessorFixture>("reset_successor_returned");
		wanted = await withBoard(browser, SUCC, { isOverview: true, isLines: false, isReturned: true, statusLabel: "Changes requested" });
		await gotoBudget(page, `/${returned.budget_code}/version/${returned.v2_number}/edit`);
		await expectScreen(page, "editor");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-14 Changes requested");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-14 Changes requested");
	});

	test("BUD-DES-04/04A/05/07/07A budget workspace tabs", async ({ page, browser }) => {
		resetFixture("reset_default");
		const base = { isOverview: true, isLines: false, isActivity: false, isHistory: false, isOfficer: false, isApproverActive: false, isCloseSurface: false, isApprover: false, isClosed: false, statusLabel: "Current", reserved: "KES 0", committed: "KES 0", available: "KES 160,000,000", asAt: "" };
		let wanted = await withBoard(browser, DETAIL, base);
		await login(page, AUDITOR);
		await gotoBudget(page, "/MOH-BUD-2027-001");
		await expectScreen(page, "detail");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-04");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-04");

		wanted = await withBoard(browser, DETAIL, { ...base, isOfficer: true });
		await login(page, OFFICER);
		await gotoBudget(page, "/MOH-BUD-2027-001");
		await expectScreen(page, "detail");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-04A");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-04A");

		wanted = await withBoard(browser, DETAIL, { ...base, isOverview: false, isLines: true });
		await gotoBudget(page, "/MOH-BUD-2027-001/lines");
		await expectScreen(page, "detail");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-05");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-05");

		wanted = await withBoard(browser, DETAIL, { ...base, isOverview: false, isActivity: true });
		await gotoBudget(page, "/MOH-BUD-2027-001/activity");
		await expectScreen(page, "detail");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-07");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-07");

		wanted = await withBoard(browser, DETAIL, { ...base, isOverview: false, isHistory: true });
		await gotoBudget(page, "/MOH-BUD-2027-001/history");
		await expectScreen(page, "detail");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-07A");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-07A", DEPARTURES["BudgetDetailScreen#BUD-DES-07A-history"]);
	});

	test("BUD-DES-17 closure: before year end, blocked, ready, confirm, closed", async ({ page, browser }) => {
		resetFixture("reset_default");
		let wanted = await withBoard(browser, DETAIL, { isOverview: true, isOfficer: false, isApproverActive: true, isApprover: true, isCloseSurface: false, isClosed: false, statusLabel: "Current" });
		await login(page, APPROVER);
		await gotoBudget(page, "/MOH-BUD-2027-001");
		await expectScreen(page, "detail");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-17 approver header");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-17 approver header");

		const blocked = resetFixture<ClosureFixture>("reset_close_blocked");
		wanted = await withBoard(browser, DETAIL, { isOverview: false, showTabs: false, isCloseSurface: true, isCloseBlocked: true, isCloseReady: false, isCloseConfirm: false, isClosed: false, isOfficer: false, isApproverActive: false, isApprover: false });
		await gotoBudget(page, `/${blocked.closure.budget_code}/close`);
		await expectScreen(page, "closure");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-17 blocked");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-17 blocked", DEPARTURES["BudgetClosureScreen#BUD-DES-17"]);

		const ready = resetFixture<ClosureFixture>("reset_close_ready");
		wanted = await withBoard(browser, DETAIL, { isOverview: false, showTabs: false, isCloseSurface: true, isCloseBlocked: false, isCloseReady: true, isCloseConfirm: false, isClosed: false, isOfficer: false, isApproverActive: false, isApprover: false });
		await gotoBudget(page, `/${ready.closure.budget_code}/close`);
		await expectScreen(page, "closure");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-17 ready");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-17 ready", DEPARTURES["BudgetClosureScreen#BUD-DES-17"]);

		wanted = await withBoard(browser, DETAIL, { isOverview: false, showTabs: false, isCloseSurface: true, isCloseBlocked: false, isCloseReady: true, isCloseConfirm: true, isClosed: false, isOfficer: false, isApproverActive: false, isApprover: false }, ["Close budget for FY 2027/28?"]);
		await page.getByTestId("bud-close-btn").click();
		await expect(page.getByTestId("bud-close-confirm")).toBeVisible();
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-17 confirm");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-17 confirm", DEPARTURES["BudgetClosureScreen#BUD-DES-17"]);
		await page.getByTestId("bud-close-confirm-btn").click();
		await expect(page.getByTestId("bud-close-closed")).toBeVisible({ timeout: 30_000 });

		wanted = await withBoard(browser, DETAIL, { isOverview: true, isClosed: true, isCloseSurface: false, isOfficer: false, isApproverActive: false, isApprover: false, statusLabel: "Closed" });
		await gotoBudget(page, `/${ready.closure.budget_code}`);
		await expectScreen(page, "detail");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-17 closed");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-17 closed");
	});

	test("BUD-DES-06/06A/06B budget line detail", async ({ page, browser }) => {
		const fx = resetFixture<SuccessorFixture>("reset_successor_draft");
		let wanted = await withBoard(browser, LINE, { hasReservation: false, hasPartial: false, isPartial: false, isReview: false, noReservation: true, eyebrow: "", lineTitle: "", ownerScope: "", observedAt: "", approved: "", reserved: "", available: "", committed: "", availableKpiClass: "kt-kpi-card", reservedBarStyle: "", committedBarStyle: "", committedStyle: "" });
		await login(page, AUDITOR);
		await gotoBudget(page, `/line/${fx.hwd_code}`);
		await expectScreen(page, "line");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-06");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-06");

		wanted = await withBoard(browser, LINE, { hasReservation: true, hasPartial: false, isPartial: false, isReview: false, noReservation: false });
		await gotoBudget(page, `/line/${fx.dhi_code}`);
		await expectScreen(page, "line");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-06A");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-06A");

		const conv = resetFixture<ConversionFixture>("reset_requires_review");
		// The board splits "partially converted" and "requires review" into two
		// switcher views with two fixtures; the live `reset_requires_review` record
		// is BOTH — 60m of its 80m hold is committed AND it needs review. Resolving
		// only isReview drops the board's conversion explanation, which §11.19
		// requires in words, so the live notice then read as unregistered structure.
		wanted = await withBoard(browser, LINE, { hasReservation: false, hasPartial: true, isPartial: true, isReview: true, noReservation: false, partialStatus: "Requires review — funds remain reserved", partialStatusClass: "kt-status is-attention" });
		await gotoBudget(page, `/line/${conv.conversion.dhi_code}`);
		await expectScreen(page, "line");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-06B");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-06B");
	});

	test("BUD-DES-13 review registered allocation, four tabs", async ({ page, browser }) => {
		const fx = resetFixture<PendingFixture>("reset_initial_submitted");
		await login(page, APPROVER);
		const v1 = { isV1: true, isV2: false, isBlocked: false, isReturn: false, approveLabel: "Approve registered allocation", afterHeader: "Available after update", createdLabel: "Budget Version 1 created" };
		for (const [tab, route] of [["isOverview", ""], ["isLines", "/lines"], ["isChanges", "/changes"], ["isHistory", "/history"]] as const) {
			const wanted = await withBoard(browser, TASK, { ...v1, isOverview: false, isLines: false, isChanges: false, isHistory: false, [tab]: true });
			await gotoBudget(page, `/review/${fx.pending.version_code}${route}`);
			await expectScreen(page, "review");
			expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), `BUD-DES-13 ${tab}`);
			await expectStructure(page, LIVE, wanted.html, `BUD-DES-13 ${tab}`,
				tab === "isHistory" ? DEPARTURES["BudgetApprovalTaskScreen#BUD-DES-13-history"] : []);
		}
	});

	test("BUD-DES-08/09/10/11 review allocation changes, blocked variant and Return dialog", async ({ page, browser }) => {
		const fx = resetFixture<SuccessorFixture>("reset_successor_submitted");
		await login(page, APPROVER);
		const v2 = { isV1: false, isV2: true, isBlocked: false, isReturn: false, approveLabel: "Approve allocation update", afterHeader: "Available after update", createdLabel: "Draft update created from Version 1" };
		for (const [tab, route] of [["isOverview", ""], ["isLines", "/lines"], ["isChanges", "/changes"], ["isHistory", "/history"]] as const) {
			const wanted = await withBoard(browser, TASK, { ...v2, isOverview: false, isLines: false, isChanges: false, isHistory: false, [tab]: true });
			await gotoBudget(page, `/review/${fx.v2_code}${route}`);
			await expectScreen(page, "review");
			expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), `BUD-DES-08..11 ${tab}`);
			await expectStructure(page, LIVE, wanted.html, `BUD-DES-08..11 ${tab}`,
				tab === "isHistory" ? DEPARTURES["BudgetApprovalTaskScreen#BUD-DES-13-history"] : []);
		}
		let wanted = await withBoard(browser, TASK, { ...v2, isOverview: true, isReturn: true });
		await gotoBudget(page, `/review/${fx.v2_code}`);
		await expectScreen(page, "review");
		await page.getByTestId("bud-task-return-btn").click();
		await expect(page.getByTestId("bud-task-return-dialog")).toBeVisible();
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-08 Return dialog");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-08 Return dialog", DEPARTURES["BudgetApprovalTaskScreen#BUD-DES-08-return-dialog"]);

		const breach = resetFixture<SuccessorFixture>("reset_live_breach");
		wanted = await withBoard(browser, TASK, { ...v2, isOverview: true, isBlocked: true, afterHeader: "Available after update / Shortfall" });
		await gotoBudget(page, `/review/${breach.v2_code}`);
		await expectScreen(page, "review");
		expectLandmarkSubsequence(wanted.texts, await liveLandmarks(page), "BUD-DES-08 blocked");
		await expectStructure(page, LIVE, wanted.html, "BUD-DES-08 blocked");
		await expect(page.getByTestId("bud-task-approve-btn")).toBeDisabled();
	});
});
