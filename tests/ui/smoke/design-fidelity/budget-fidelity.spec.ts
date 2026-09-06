import { test, expect, Page } from "@playwright/test";
import { login } from "../../helpers/auth";
import {
	openArtboard,
	landmarks,
	expectLandmarkSubsequence,
	collectPageErrors,
} from "../../helpers/designFidelity";

/**
 * Budget & Funding design-fidelity gate (AGENTS.md §6.6 enforcement, BUD-802).
 *
 * Clones the System Setup gate's own approach (tests/ui/smoke/design-fidelity/
 * system-setup-fidelity.spec.ts): render each `.dc.html` artboard, derive its
 * ordered structural landmarks (card titles, field labels, table headers,
 * buttons — see designFidelity.ts's own doc comment for the exact selector),
 * and assert the live route's own landmarks contain that sequence in order.
 *
 * Covers all 22 non-retired Budget & Funding artboards (of the 30 total in
 * docs/mvp-1-r1/03_budget/design/ — the 8 excluded are the 4 "Activation
 * Task - *" + 4 "Initial Baseline Activation - *" files, which model the
 * explicitly-retired BUD-DES-12/13A second-decision-stage screens per
 * BUD-CHG-001 v1.3 §11.12/§11.13A — confirmed by content, they contain
 * literal "Awaiting Activation"/"Budget Reviewer" text). Between them the 22
 * artboards exercise all 5 live routes plus the 4 BUD-DES-16 workspace state
 * variants:
 *
 *   - Workspace                    /app/budget-funding
 *   - New/pre-creation             /app/budget-funding/new
 *   - Draft/successor editor       /app/budget-funding/{code}/version/{n}/edit[/lines]
 *   - Approval task                /app/budget-funding/review/{version}[/lines|/changes|/history]
 *   - Active budget detail         /app/budget-funding/{code}[/lines|/activity|/history]
 *   - Budget line detail           /app/budget-funding/line/{code}
 *
 * BUD-DES-05 (Active Budget Lines) and BUD-DES-07A (Active Budget History)
 * are deliberately NOT covered here: §11.5/§11.7A's own text says "no
 * .dc.html artboard exists for this screen" and instructs reusing the
 * BUD-DES-04 header/tabs plus another screen's table chrome verbatim — there
 * is no oracle artboard to render against, so no fidelity check is possible
 * or required for those two tab states.
 *
 * Known, deliberate artboard-vs-live deltas NOT asserted here (each stripped
 * from the artboard-derived `wanted` list before comparing, mirroring the
 * reference gate's own precedent for a documented, permanent fixture/
 * artboard delta — its C4 mnemonic-vs-generated-code allowance):
 *
 *   - "Procuring Entity": 8 of the 22 artboards ("Active Budget Overview
 *     [.dc.html/- Budget Officer]", "Budget Line Detail[.dc.html/- With
 *     Reservation]", "Initial Baseline Review - Overview", "Reviewer Task -
 *     Overview", "Register Approved Budget Draft", "Successor Revision Draft
 *     - Overview") still render this row as a genuine `.kt-label`/`<label>`
 *     landmark, even though BUD-CHG-001 v1.3 §11's own preamble explicitly
 *     prohibits it ("do not show a Procuring Entity row or selector") and
 *     the live screens correctly have none (BUD-702/BUD-705, browser-
 *     verified). Re-adding it to the live screens would be a regression
 *     against the governing spec text, not a fix.
 *   - "Recommend for activation": all 8 of the approval-task-shaped
 *     artboards ("Reviewer Task - *" and "Initial Baseline Review - *")
 *     carry this exact button text in their fixed footer, alongside
 *     "Return" — both artboard families predate BUD-DES-12/13A's retirement
 *     (the old two-stage Reviewer-then-Activation-Authority workflow) and
 *     were never updated to the single-decision "Approve" wording §11.8's
 *     own written spec text describes and BUD-705 already browser-verified
 *     live. "Return" itself is NOT stripped — it is a real, correctly-
 *     rendered live button on both fixtures.
 *   - "Replace": "Register Approved Budget Draft.dc.html" (BUD-DES-02) shows
 *     the Approval document field already holding a file (button reads
 *     "Replace"). A genuinely fresh "new" registration form — the only state
 *     this route can be in — has no file attached yet and reads "Upload"
 *     instead; this is a data-state difference in which moment the artboard
 *     depicts, not a missing control.
 *   - "Reviewed by" / "Activated by": "Active Budget Overview[.dc.html/-
 *     Budget Officer].dc.html"'s Activation card still splits the decision
 *     into two separate actors (the old two-stage workflow again), where
 *     §11.4's own written spec text and the live card both use one combined
 *     "Approved and activated by" row — same stale-artboard class as
 *     "Recommend for activation" above, same fix (not asserted).
 *
 * Separately, Budget's own screens style every small field-label row with
 * `.kt-eyebrow` (kentender_core's shared kt_industry_tokens.css), not the
 * artboards' `.kt-label` (a System-Setup-specific class, kt_admin_
 * configuration.css — confirmed by grep; Budget's screens never load that
 * stylesheet). Both render identically; only the class name differs. Rather
 * than fork designFidelity.ts's shared LANDMARK_SELECTOR (other gates use
 * it too) or invent a second live class purely to satisfy this gate,
 * `liveLandmarks()` below is this file's own local extraction — identical to
 * the shared `landmarks()` helper's own selector plus `.kt-eyebrow` — used
 * only for the live-page side of every comparison; the artboard side keeps
 * using the shared, unmodified `landmarks()`.
 *
 * Two genuine, small, artboard-specified defects found and fixed live while
 * building this gate (BudgetApprovalTaskScreen.vue): the Budget Lines tab's
 * amount column header was hardcoded "Proposed amount" even for the initial-
 * baseline (no-predecessor) case, where §11.13 specifies "Submitted amount";
 * and the History tab had no "Version history" card title at all, though
 * §11.11/§11.13 both specify one.
 *
 * Prerequisite state: `bench console` fed budget_fidelity_seed.py (idempotent
 * — the `ui-budget-fidelity-gate` make target runs it first, piped through
 * `exec(open(...).read())` rather than raw stdin — see that file's own
 * top-of-file comment for why: IPython's line-by-line stdin cell-splitting
 * silently mishandles multi-statement scripts with blank lines inside
 * indented blocks, which cost most of this gate's build time to track down).
 */

const DESIGN_DIR = "docs/mvp-1-r1/03_budget/design";
const ARTBOARD_SCOPE = "x-dc";
// .kt-industry, not .kt-shell: the Approval task / editor screens' fixed
// footer (Return/Approve, Save draft/Submit for review) is a SIBLING of
// .kt-shell, not a descendant — scoping to .kt-shell alone silently drops
// every footer-button landmark.
const LIVE_SCOPE = ".kt-industry";

const PASSWORD = "Test@123";
const BUDGET_OFFICER = "josphat.mwangi@moh.example.test";
const BUDGET_APPROVER = "beatrice.kamau@moh.example.test";
const AUDITOR = "naomi.chebet@moh.example.test";
const NO_ASSIGNMENT_ACTOR = "samuel.otieno@moh.example.test";

const EMPTY_FY = "2063-2064";

test.use({ viewport: { width: 1440, height: 1024 } });

async function loginAsBudgetOfficer(page: Page) {
	await login(page, BUDGET_OFFICER, PASSWORD);
}
async function loginAsBudgetApprover(page: Page) {
	await login(page, BUDGET_APPROVER, PASSWORD);
}
async function loginAsAuditor(page: Page) {
	await login(page, AUDITOR, PASSWORD);
}

/** See this file's own top-of-file comment on the .kt-eyebrow/.kt-label delta. */
const LIVE_LANDMARK_SELECTOR = [
	".kt-card-title",
	".kt-dialog-title",
	".dialog-title",
	"label",
	"legend",
	".kt-label",
	".kt-eyebrow",
	"th",
	"button",
].join(", ");

async function liveLandmarks(page: Page, scope: string): Promise<string[]> {
	return page.evaluate(
		({ scope, selector }) => {
			const root = document.querySelector(scope);
			if (!root) return [];
			const texts: string[] = [];
			for (const el of Array.from(root.querySelectorAll<HTMLElement>(selector))) {
				if (!el.getClientRects().length) continue;
				const text = (el.textContent || "").replace(/\s+/g, " ").trim();
				if (text) texts.push(text);
			}
			return texts;
		},
		{ scope, selector: LIVE_LANDMARK_SELECTOR },
	);
}

/** See this file's own top-of-file comment on each stripped delta. */
function stripKnownArtboardDeltas(wanted: string[], extra: string[] = []): string[] {
	const drop = new Set(["Procuring Entity", ...extra]);
	return wanted.filter((t) => !drop.has(t));
}

async function artboardLandmarks(page: Page, file: string, extraDrops: string[] = []): Promise<string[]> {
	await openArtboard(page, `${DESIGN_DIR}/${file}`, ARTBOARD_SCOPE);
	return stripKnownArtboardDeltas(await landmarks(page, ARTBOARD_SCOPE), extraDrops);
}

test.describe("Budget & Funding — design fidelity", () => {
	// ---------------------------------------------------------------
	// Workspace (/app/budget-funding) — BUD-DES-01 + BUD-DES-16 states
	// ---------------------------------------------------------------

	test("BUD-DES-01 — Budget & Funding workspace (Active state)", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Budget and Funding Workspace.dc.html");

		const errors = collectPageErrors(page);
		await loginAsAuditor(page);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="budget-fy-filter"]', { timeout: 30_000 });
		await page.selectOption('[data-testid="budget-fy-filter"]', "2027-2028");
		await page.waitForSelector('[data-testid="budget-summary-card"]', { timeout: 20_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-01");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-16 — Workspace state: Loading", async ({ page, browser }) => {
		const art = await browser.newPage();
		// The Loading artboard's whole card content is skeleton placeholder
		// bars (plain unstyled <div>s) — no .kt-card-title/label/th/button
		// element exists to land on the shared landmark selector, so `wanted`
		// is genuinely empty here (confirmed: expectLandmarkSubsequence's own
		// "at least one landmark matched" assertion is not meaningful against
		// an empty artboard set). Assert structure directly instead: the
		// artboard's own composition — one full-width card followed by 4
		// position-card skeletons — is what the live skeleton must match.
		await openArtboard(art, `${DESIGN_DIR}/Workspace State - Loading.dc.html`, ARTBOARD_SCOPE);
		const artSkelCount = await art.locator(`${ARTBOARD_SCOPE} .kt-skel`).count();

		await loginAsBudgetOfficer(page);
		// Hang the workspace call indefinitely so the loading skeleton renders
		// and stays put for the assertion (route interception — no other way
		// to hold this real, fast, in-process call open long enough to observe).
		await page.route("**/api/method/**get_budget_workspace*", () => {
			/* never fulfilled */
		});
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="budget-fy-filter"]', { timeout: 30_000 });
		await page.selectOption('[data-testid="budget-fy-filter"]', "2027-2028");
		await page.waitForSelector(".kt-skel", { timeout: 10_000 });

		expect(await page.locator(".kt-skel").count(), "skeleton bar count").toBeGreaterThanOrEqual(artSkelCount);
		await page.unrouteAll({ behavior: "ignoreErrors" });
		await art.close();
	});

	test("BUD-DES-16 — Workspace state: No baseline", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Workspace State - No Baseline.dc.html");

		const errors = collectPageErrors(page);
		await loginAsBudgetOfficer(page);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="budget-fy-filter"]', { timeout: 30_000 });
		await page.selectOption('[data-testid="budget-fy-filter"]', EMPTY_FY);
		await page.waitForSelector('[data-testid="budget-no-baseline"]', { timeout: 20_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-16 No baseline");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-16 — Workspace state: Forbidden", async ({ page, browser }) => {
		const art = await browser.newPage();
		// Same empty-landmark-set situation as the Loading state above: the
		// artboard's icon/heading/body are all plain unstyled <div>s (no
		// .kt-card-title/label/th/button), so there is nothing for the shared
		// landmark selector to match. Verify the artboard's own body copy
		// directly instead — it is real, comparable text, just not inside a
		// landmark element.
		await openArtboard(art, `${DESIGN_DIR}/Workspace State - Forbidden.dc.html`, ARTBOARD_SCOPE);
		const artBody = (await art.locator(`${ARTBOARD_SCOPE} .card`).innerText()).trim();
		expect(artBody).toContain("Ask your KenTender administrator to review your Budget assignment.");
		// The artboard still carries v1.3's copy ("…review your Budget
		// assignment."); BUD-CHG-001 v1.6 §11.16 / BUD-AC-040 and KT-STD-001
		// §3A.4 replaced it with the responsibility list and the System setup
		// pointer, which is what the live page shows (FOLLOW_UPS FU-06 family:
		// artboard text lags the governing spec section).

		// KT-STD-001 §3A.2 — the verdict is data, not an HTTP 403 (a 403 would
		// also raise Frappe's own "Not permitted" modal). Samuel Otieno is the
		// register's no-Budget-responsibility actor (§8.3: expired assignment),
		// so the real page-load path is exercised, not a mocked response.
		const errors = collectPageErrors(page);
		await login(page, NO_ASSIGNMENT_ACTOR, PASSWORD);
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="bud-forbidden"]', { timeout: 30_000 });
		await expect(page.getByText("You do not have access to Budget & Funding")).toBeVisible();
		await expect(
			page.getByText("Budget Officer, Budget Approver, Finance Confirmation Officer or Auditor")
		).toBeVisible();
		await expect(page.getByText("Ask your KenTender administrator to assign one in System setup.")).toBeVisible();
		// §3A.1 — no content, empty state or permission modal behind the panel.
		expect(await page.locator('[data-testid="budget-summary-card"]').count()).toBe(0);
		expect(await page.locator(".modal.show").count()).toBe(0);
		expect(errors, "console errors").toEqual([]);

		await art.close();
	});

	test("BUD-DES-16 — Workspace state: Server error", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Workspace State - Server Error.dc.html");

		await loginAsBudgetOfficer(page);
		await page.route("**/api/method/**get_budget_workspace*", async (route) => {
			await route.fulfill({ status: 500, contentType: "application/json", body: "{}" });
		});
		await page.goto("/app/budget-funding", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="budget-fy-filter"]', { timeout: 30_000 });
		await page.selectOption('[data-testid="budget-fy-filter"]', "2027-2028");
		await page.waitForSelector('text=Budget & Funding could not be loaded.', { timeout: 20_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-16 Server error");
		await page.unrouteAll({ behavior: "ignoreErrors" });
		await art.close();
	});

	// ---------------------------------------------------------------
	// New / pre-creation (/app/budget-funding/new) — BUD-DES-02
	// ---------------------------------------------------------------

	test("BUD-DES-02 — Register approved budget draft", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Register Approved Budget Draft.dc.html", ["Replace"]);

		const errors = collectPageErrors(page);
		await loginAsBudgetOfficer(page);
		await page.goto("/app/budget-funding/new", { waitUntil: "domcontentloaded" });
		await page.waitForSelector("#bud-new-fy", { timeout: 30_000 });
		await page.selectOption("#bud-new-fy", EMPTY_FY);
		await page.waitForSelector('[data-testid="bud-editor-save-btn"]', { timeout: 20_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-02");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// ---------------------------------------------------------------
	// Draft editor, existing (/app/budget-funding/{code}/version/{n}/edit/lines)
	// — BUD-DES-03
	// ---------------------------------------------------------------

	test("BUD-DES-03 — Draft Budget Lines editor", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Draft Budget Lines Editor.dc.html");

		const errors = collectPageErrors(page);
		await loginAsBudgetOfficer(page);
		await page.goto("/app/budget-funding/BUD-FIDELITY-DRAFT/version/1/edit/lines", {
			waitUntil: "domcontentloaded",
		});
		await page.waitForSelector('[data-testid="bud-editor-lines-table"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-03");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// ---------------------------------------------------------------
	// Active budget detail (/app/budget-funding/{code}[/tab]) — BUD-DES-04/04A/07
	// ---------------------------------------------------------------

	test("BUD-DES-04 — Active Budget overview (Auditor)", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Active Budget Overview.dc.html", ["Reviewed by", "Activated by"]);

		const errors = collectPageErrors(page);
		await loginAsAuditor(page);
		await page.goto("/app/budget-funding/MOH-BUD-2027-001", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="budget-detail-header"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-04");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-04A — Active Budget overview (Budget Officer, Create revision)", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Active Budget Overview - Budget Officer.dc.html", [
			"Reviewed by",
			"Activated by",
		]);

		const errors = collectPageErrors(page);
		await loginAsBudgetOfficer(page);
		await page.goto("/app/budget-funding/MOH-BUD-2027-001", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="budget-detail-create-revision-btn"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-04A");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-07 — Funding Activity", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Funding Activity.dc.html");

		const errors = collectPageErrors(page);
		await loginAsAuditor(page);
		await page.goto("/app/budget-funding/BUD-FIDELITY-REVIEW/activity", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="budget-detail-activity-table"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-07");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// ---------------------------------------------------------------
	// Budget Line detail (/app/budget-funding/line/{code}) — BUD-DES-06/06A
	// ---------------------------------------------------------------

	test("BUD-DES-06 — Budget Line detail (no reservation)", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Budget Line Detail.dc.html");

		const errors = collectPageErrors(page);
		await loginAsBudgetOfficer(page);
		await page.goto("/app/budget-funding/line/MOH-BL-HWD-2027", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="bud-line-reservations-empty"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-06");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-06A — Budget Line detail (with an active reservation)", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Budget Line Detail - With Reservation.dc.html");

		const errors = collectPageErrors(page);
		await loginAsAuditor(page);
		await page.goto("/app/budget-funding/line/BUD-FIDELITY-REVIEW-DHI", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="bud-line-reservations-table"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-06A");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// ---------------------------------------------------------------
	// Approval task (/app/budget-funding/review/{version}[/tab])
	// — BUD-DES-13 (Initial Baseline Review, Version 1, no predecessor)
	// ---------------------------------------------------------------

	test("BUD-DES-13 Overview — Initial baseline review", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Initial Baseline Review - Overview.dc.html", ["Recommend for activation"]);

		const errors = collectPageErrors(page);
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-FIDELITY-BASELINE-V1", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="bud-task-readiness"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-13 Overview");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-13 Budget Lines — Initial baseline review", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Initial Baseline Review - Budget Lines.dc.html", ["Recommend for activation"]);

		const errors = collectPageErrors(page);
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-FIDELITY-BASELINE-V1/lines", {
			waitUntil: "domcontentloaded",
		});
		await page.waitForSelector('[data-testid="bud-task-lines-table"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-13 Budget Lines");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-13 Changes — Initial baseline review", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Initial Baseline Review - Changes.dc.html", ["Recommend for activation"]);

		const errors = collectPageErrors(page);
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-FIDELITY-BASELINE-V1/changes", {
			waitUntil: "domcontentloaded",
		});
		await page.waitForSelector('[data-testid="bud-task-changes-baseline"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-13 Changes");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-13 History — Initial baseline review", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Initial Baseline Review - History.dc.html", ["Recommend for activation"]);

		const errors = collectPageErrors(page);
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-FIDELITY-BASELINE-V1/history", {
			waitUntil: "domcontentloaded",
		});
		await page.waitForSelector('[data-testid="bud-task-history-table"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-13 History");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// ---------------------------------------------------------------
	// Approval task — BUD-DES-08/09/10/11 (Reviewer Task, Version 2 successor
	// with a predecessor: "Based on" / "Revision type" / Changes vs Active)
	// ---------------------------------------------------------------

	test("BUD-DES-08 Overview — Reviewer task", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Reviewer Task - Overview.dc.html", ["Recommend for activation"]);

		const errors = collectPageErrors(page);
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-FIDELITY-REVIEW-V2", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="bud-task-readiness"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-08");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-09 Budget Lines — Reviewer task", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Reviewer Task - Budget Lines.dc.html", ["Recommend for activation"]);

		const errors = collectPageErrors(page);
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-FIDELITY-REVIEW-V2/lines", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="bud-task-lines-table"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-09");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-10 Changes — Reviewer task", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Reviewer Task - Changes.dc.html", ["Recommend for activation"]);

		const errors = collectPageErrors(page);
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-FIDELITY-REVIEW-V2/changes", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="bud-task-changes-table"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-10");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-11 History — Reviewer task", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Reviewer Task - History.dc.html", ["Recommend for activation"]);

		const errors = collectPageErrors(page);
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-FIDELITY-REVIEW-V2/history", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="bud-task-history-table"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-11");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// ---------------------------------------------------------------
	// Successor revision draft, unsubmitted
	// (/app/budget-funding/{code}/version/{n}/edit[/lines]) — BUD-DES-14/15
	// ---------------------------------------------------------------

	test("BUD-DES-14 — Successor revision draft, Overview", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Successor Revision Draft - Overview.dc.html");

		const errors = collectPageErrors(page);
		await loginAsBudgetOfficer(page);
		await page.goto("/app/budget-funding/BUD-FIDELITY-SUCCESSOR/version/2/edit", {
			waitUntil: "domcontentloaded",
		});
		await page.waitForSelector('[data-testid="bud-editor-submit-btn"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-14");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("BUD-DES-15 — Successor revision draft, Budget Lines", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "Successor Revision Draft - Budget Lines.dc.html");

		const errors = collectPageErrors(page);
		await loginAsBudgetOfficer(page);
		await page.goto("/app/budget-funding/BUD-FIDELITY-SUCCESSOR/version/2/edit/lines", {
			waitUntil: "domcontentloaded",
		});
		await page.waitForSelector('[data-testid="bud-editor-lines-table"]', { timeout: 30_000 });

		expectLandmarkSubsequence(wanted, await liveLandmarks(page, LIVE_SCOPE), "BUD-DES-15");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});
});
