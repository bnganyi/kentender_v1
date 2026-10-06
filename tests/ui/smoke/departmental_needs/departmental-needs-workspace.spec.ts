import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureAuthor } from "../../helpers/auth";
import { expectLayoutSanity } from "../../helpers/designFidelity";
import {
	clearFixtures,
	collectConsoleErrors,
	expectScreen,
	gotoNeeds,
	purgeUntaggedNeedsSince,
	resetFixture,
	selectContext,
	siteNow,
} from "./helpers";

/**
 * NDS-CHG-001 v1.6 — NDS-UI-01 requester workspace (`/app/departmental-needs`)
 * and NDS-UI-03 need editor (`/app/departmental-needs/new`).
 *
 * Replaces the pre-v1.1 workspace/create/edit specs, which drove the retired
 * NDS-CHG-002 routes and screens (`departmental-needs-new`, the items table,
 * attachments, indicative cost) that §1.1 removed outright.
 *
 * Fixture: `reset_open_intake_fixture` — one Draft under the dedicated
 * Playwright Organisation Unit. §5.1 gates creation on the Needs-submission
 * flag being Open; §14.1 requires it already Open on the site's one Fiscal
 * Year before any seed runs (`kentender_core.seeds.site_setup` owns the
 * flag), so this fixture only ever builds the Draft — it never opens or
 * closes the flag itself (see `playwright_ui_fixtures.py`'s own docstring).
 */

let NEED = "";

test.describe.configure({ mode: "serial" });

test.describe("NDS-UI-01 workspace and NDS-UI-03 editor", () => {
	test.beforeEach(() => {
		NEED = resetFixture<{ need: string }>("reset_open_intake_fixture").need;
	});
	test.afterAll(() => clearFixtures());

	test("the workspace lists the author's needs with one action each", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");

		// §1.1 replaced four summary cards and split action/waiting sections with
		// one role-appropriate table, so exactly one table is the assertion.
		await expect(page.locator('[data-testid="nds-needs-table"]')).toHaveCount(1);
		const row = page.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"]`);
		await expect(row).toBeVisible();
		await expect(row).toHaveAttribute("data-status", "Draft");
		// NDS-CHG-001 v1.13 §11.2 — the author's own list carries no
		// Requester/Requested-by column at all (every row is already theirs);
		// that column exists only in the HoD's shared register (§11.3), covered
		// by the review-task spec's dual-role fixture.
		await expect(
			page.locator('[data-testid="nds-needs-table"] th', { hasText: "Requested by" }),
		).toHaveCount(0);
		// §12.1 — a Draft belongs to its author, so the row offers Continue.
		await expect(row.locator('[data-testid="nds-row-action"]')).toHaveAttribute(
			"data-action",
			"edit",
		);
		await expect(page.locator('[data-testid="kt-pager-count"]')).toContainText("need");

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Create need is offered while intake is Open and opens the editor", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");

		await page.locator('[data-testid="nds-create-need"]').click();
		await expectScreen(page, "editor");

		// §2.2 / NDS-AC-001 — exactly the six requester-entered values, and none
		// of the fields §1.1 removed.
		for (const field of [
			"nds-title",
			"nds-description",
			"nds-result",
			"nds-quantity",
			"nds-unit",
			"nds-required-by",
		]) {
			await expect(page.locator(`[data-testid="${field}"]`)).toBeVisible();
		}
		// NDS-AC-007 / NDS-AC-029 — no funding, cost, location or attachment.
		for (const forbidden of ["indicative_cost", "currency", "budget_line", "attachment"]) {
			await expect(page.locator(`[name="${forbidden}"]`)).toHaveCount(0);
		}
		await expect(page.getByText(/attach/i)).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Create need opens blank after another need was open", async ({ page }) => {
		/**
		 * Reported live 2026-09-11: the create editor showed the previously
		 * opened need's title, description and result. The root fed the editor
		 * the shared `detail` payload, which entering /new never cleared — the
		 * create editor must have no source revision at all.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await page
			.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"] [data-testid="nds-row-action"]`)
			.click();
		await expectScreen(page, "editor");
		await expect(page.locator('[data-testid="nds-title"]')).not.toHaveValue("");

		// NDS-CHG-001 v1.13 §11.5/§11.16 — a Draft/Returned Need's destructive
		// footer button is now "Withdraw need" (a real command, confirmed via
		// dialog), not a plain navigate-away Cancel; go back to the workspace
		// directly rather than exercising that confirmation here.
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await page.locator('[data-testid="nds-create-need"]').click();
		await expectScreen(page, "editor");
		await expect(page).toHaveURL(/\/departmental-needs\/new$/);
		for (const field of ["nds-title", "nds-description", "nds-result", "nds-quantity", "nds-required-by"]) {
			await expect(page.locator(`[data-testid="${field}"]`)).toHaveValue("");
		}
		await expect(page.getByText("Returned for correction")).toHaveCount(0);
		// AGENTS.md 6.6 — an editor opened in an incomplete state is where a
		// repeated notice, a control built inside a fact, or a heading left
		// standing over resolved-away content hides. A blank create editor is
		// the most incomplete state this screen has.
		await expectLayoutSanity(page, "NDS create editor, blank");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a Draft opens in the editor and saves", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");

		await page
			.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"] [data-testid="nds-row-action"]`)
			.click();
		await expectScreen(page, "editor");

		await page.locator('[data-testid="nds-title"]').fill("County health records digitisation v2");
		await page.locator('[data-testid="nds-save-draft"]').click();

		await expect(page.locator('[data-testid="nds-error-summary"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
	test("Submit for review straight after Save draft is not refused as a stale write", async ({ page }) => {
		/**
		 * Regression (2026-09-11): the version stamp the next command carried
		 * came from the post-save reload, which resolves after the buttons are
		 * re-enabled. A Save draft followed at once by Submit for review (or a
		 * second Save) sent the pre-save stamp and the server answered "This
		 * Departmental Need changed after it was opened" with nobody else
		 * editing. The stamp now comes from the save response itself; this
		 * test widens the reload window so the old behaviour cannot pass.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		await page
			.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"] [data-testid="nds-row-action"]`)
			.click();
		await expectScreen(page, "editor");

		// Every editor reload now lands 1.5 s after the save it follows.
		await page.route("**/api/method/*.get_departmental_need", async (route) => {
			const response = await route.fetch();
			await new Promise((resolve) => setTimeout(resolve, 1500));
			await route.fulfill({ response });
		});

		await page.locator('[data-testid="nds-title"]').fill("County health records digitisation v3");
		await page.locator('[data-testid="nds-save-draft"]').click();
		await expect(page.locator('[data-testid="nds-save-draft"]')).toBeEnabled();
		await page.locator('[data-testid="nds-submit"]').click();
		await page.locator('[data-testid="nds-dialog-confirm"]').click();

		await expect(page.locator('[data-testid="nds-error-summary"]')).toHaveCount(0);
		await expect(page).toHaveURL(new RegExp(`/departmental-needs/${NEED}$`), { timeout: 30_000 });
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
	test("an unparseable typed date blocks the submit with a field error", async ({ page }) => {
		/**
		 * A native date input holding text that does not parse (the reported
		 * case: 31/09/2026) keeps the text visible but reports value "" — the
		 * old behaviour silently dropped it and the server answered
		 * "Required-by date is required." for a field that looked filled in.
		 * The editor now refuses to emit and names the real problem.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "/new");
		await expectScreen(page, "editor");
		await page.locator('[data-testid="nds-title"]').fill("Unparseable date guard");
		// Partial keyboard entry leaves the input in the badInput state.
		await page.locator('[data-testid="nds-required-by"]').click();
		await page.keyboard.press("3");
		await page.keyboard.press("1");
		await page.locator('[data-testid="nds-submit"]').click();
		await expect(page.locator('[data-testid="nds-required-by-error"]')).toHaveText(
			"Required by must be a real calendar date.",
		);
		// Nothing was sent: no server summary, and the route did not change.
		await expect(page.locator('[data-testid="nds-error-summary"]')).toHaveCount(0);
		await expect(page).toHaveURL(/\/departmental-needs\/new$/);
		await expectLayoutSanity(page, "NDS create editor, refused submit");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
	test("a Required by date outside the financial year is refused with the allowed dates", async ({ page }) => {
		/**
		 * UAT issue #25: the form accepted 2030 for FY 2027/28 and only the
		 * server's submit check refused it. The picker is now limited to the year
		 * and Save draft / Submit name the allowed dates without a round trip.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "/new");
		await expectScreen(page, "editor");
		const requiredBy = page.locator('[data-testid="nds-required-by"]');
		await expect(requiredBy).toHaveAttribute("min", "2027-07-01");
		await expect(requiredBy).toHaveAttribute("max", "2028-06-30");
		await page.locator('[data-testid="nds-title"]').fill("Required by outside the year");
		await requiredBy.fill("2030-01-31");
		await page.locator('[data-testid="nds-save-draft"]').first().click();
		await expect(page.locator('[data-testid="nds-required-by-error"]')).toHaveText(
			"Required by must be between 1 Jul 2027 and 30 Jun 2028, the dates of FY 2027/28.",
		);
		// Nothing was sent: no server summary, and the route did not change.
		await expect(page.locator('[data-testid="nds-error-summary"]')).toHaveCount(0);
		await expect(page).toHaveURL(/\/departmental-needs\/new$/);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
	test("Submit for review asks first; Cancel sends nothing", async ({ page }) => {
		/**
		 * UAT #30: Submit saved and submitted straight from the button. It now
		 * opens "Submit for review?" first; Cancel changes nothing.
		 */
		await loginAsNdsFixtureAuthor(page);
		const sent: string[] = [];
		page.on("request", (request) => {
			if (/save_need_draft|submit_need_revision/.test(request.url())) sent.push(request.url());
		});
		await gotoNeeds(page, "/new");
		await expectScreen(page, "editor");
		await page.locator('[data-testid="nds-title"]').fill("Submit asks first");
		await page.locator('[data-testid="nds-submit"]').click();
		const dialog = page.locator('[data-testid="nds-dialog"]');
		await expect(dialog).toContainText("Submit for review?");
		await expect(dialog).toContainText("Submit asks first");
		await page.locator('[data-testid="nds-dialog-cancel"]').click();
		await expect(dialog).toHaveCount(0);
		expect(sent, "Cancel must not save or submit").toEqual([]);
		await expect(page).toHaveURL(/\/departmental-needs\/new$/);
		await expect(page.locator('[data-testid="nds-title"]')).toHaveValue("Submit asks first");
	});
	test("a failed Unit list leaves the editor usable and Try again fills it", async ({ page }) => {
		/**
		 * UAT #29: the unit call failed on a half-deployed server and the whole
		 * editor was replaced by "Departmental Needs could not be loaded". The
		 * form now stays, says the list could not be loaded, and retries in place.
		 */
		await loginAsNdsFixtureAuthor(page);
		const unitsCall = "**/api/method/kentender_procurement.departmental_needs.api.list_need_units";
		await page.route(unitsCall, (route) =>
			route.fulfill({
				status: 417,
				contentType: "application/json",
				body: JSON.stringify({ exc_type: "AttributeError", exception: "no attribute list_need_units" }),
			}),
		);
		await gotoNeeds(page, "/new");
		await expectScreen(page, "editor");
		await expect(page.locator('[data-testid="nds-title"]')).toBeVisible();
		await expect(page.getByText("Departmental Needs could not be loaded")).toHaveCount(0);
		await expect(page.locator('[data-testid="nds-units-error"]')).toContainText("The list of units could not be loaded.");
		await page.locator('[data-testid="nds-title"]').fill("Typed while units were unavailable");

		await page.unroute(unitsCall);
		await page.locator('[data-testid="nds-units-retry"]').click();
		await expect(page.locator('[data-testid="nds-units-error"]')).toHaveCount(0);
		expect(await page.locator('[data-testid="nds-unit"] option').count()).toBeGreaterThan(1);
		// What was typed in the meantime is still there.
		await expect(page.locator('[data-testid="nds-title"]')).toHaveValue("Typed while units were unavailable");
	});
	test("a refused first submit lands on the saved draft and the retry updates it", async ({ page }) => {
		/**
		 * Reported live 2026-09-25: the first Submit for review on /new saved a
		 * Draft, then the server refused the submit (a Required-by date outside
		 * the financial year). The retry, after correcting the form, minted a
		 * second Need and left the first behind as an orphan Draft with the
		 * same title. Only the intake-closed refusal used to remember the
		 * reference the first save had minted; any refusal must.
		 */
		const since = siteNow();
		try {
			// No console-error assertion here: the refused submit is deliberate and
			// the server's 417 + traceback land in the console by design.
			const saves: string[] = [];
			page.on("request", (request) => {
				if (request.url().endsWith(".save_need_draft")) {
					saves.push(new URLSearchParams(request.postData() || "").get("need") || "");
				}
			});
			await loginAsNdsFixtureAuthor(page);
			await gotoNeeds(page, "/new");
			await expectScreen(page, "editor");

			// Title only: the save goes through, the submit is refused server-side.
			await page.locator('[data-testid="nds-title"]').fill("Refused-then-corrected submit");
			await page.locator('[data-testid="nds-submit"]').click();
			await page.locator('[data-testid="nds-dialog-confirm"]').click();
			// §8.4 "Save succeeds, Submit fails": the saved draft is reported with
			// the server's actual reason, and Submit stays available to retry.
			const notice = page.locator('[data-testid="nds-partial-submit"]');
			await expect(notice).toContainText("Your draft was saved, but it was not submitted.");
			await expect(page.locator('[data-testid="nds-partial-submit-reason"]')).toContainText("Description");
			await expect(page.locator('[data-testid="nds-submit"]')).toBeEnabled();
			// §8.4 "New unsaved form" — the confirmed save replaced /new with the
			// saved Need's own route before the submit ran, so a refresh keeps it.
			await expect(page).toHaveURL(/\/departmental-needs\/NDS-[A-Z0-9-]+\/edit$/);
			const reference = page.url().split("/departmental-needs/")[1].split("/")[0];
			expect(saves).toEqual([""]);

			// A second attempt must target the Need the first save created.
			await page.locator('[data-testid="nds-description"]').fill("Corrected description for the retry.");
			await page.locator('[data-testid="nds-submit"]').click();
			await page.locator('[data-testid="nds-dialog-confirm"]').click();
			await expect.poll(() => saves.length).toBe(2);
			expect(saves[1], "the retry must update the Need the first save created").toBe(reference);
		} finally {
			purgeUntaggedNeedsSince(since);
		}
	});
	test("filters refresh the table in place — no skeleton flash", async ({ page }) => {
		/**
		 * Every search keystroke and status change used to re-enter the full
		 * loading state, swapping the band and table for the skeleton card on a
		 * round-trip each time (reported live 2026-08-30). Filter changes now
		 * load quietly (rows stay mounted) and typing is debounced, so
		 * data-loading must never flip while filtering.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page);
		await expectScreen(page, "workspace");
		const row = page.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"]`);
		await expect(row).toBeVisible();

		// The skeleton appears exactly when the shell's data-loading flips, so
		// zero observed flips proves the screen never flashed.
		await page.evaluate(() => {
			const shell = document.querySelector('[data-testid="nds-shell"]');
			(window as unknown as { __ktLoadingFlips: number }).__ktLoadingFlips = 0;
			new MutationObserver(() => {
				(window as unknown as { __ktLoadingFlips: number }).__ktLoadingFlips += 1;
			}).observe(shell as Node, { attributes: true, attributeFilter: ["data-loading"] });
		});
		let workspaceCalls = 0;
		page.on("request", (request) => {
			if (request.url().includes("get_needs_workspace")) workspaceCalls += 1;
		});

		await page
			.locator('[data-testid="nds-search"]')
			.pressSequentially("no-such-need", { delay: 40 });
		// Filtered-to-empty names the real situation, not "no needs yet".
		await expect(page.getByText("No needs match your filters")).toBeVisible();
		await expect(page.getByText("No departmental needs yet")).toHaveCount(0);

		await page.locator('[data-testid="nds-status-filter"]').selectOption("Draft");
		await page.getByRole("button", { name: "Clear filters" }).click();
		await expect(row).toBeVisible();

		// Typing was debounced: 12 keystrokes must not mean 12 round-trips.
		expect(workspaceCalls).toBeLessThanOrEqual(4);
		expect(
			await page.evaluate(
				() => (window as unknown as { __ktLoadingFlips: number }).__ktLoadingFlips,
			),
		).toBe(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
	test("a record detail route keeps the Procurement rail", async ({ page }) => {
		/**
		 * Frappe's sidebar resolves a 2-segment route through route[1] — here a
		 * Need reference, never a sidebar — then falls back through the Page's
		 * Module Def, which replaced the reviewer's rail with Frappe's "Build"
		 * module sidebar (observed live 2026-08-30). The route-first patch in
		 * procurement_sidebar_header.js resolves route[0]'s boot alias instead;
		 * this guards it for direct loads of record routes.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, `/${NEED}`);
		await expectScreen(page, "detail");
		const rail = page.locator(".body-sidebar");
		await expect(rail.locator(".sidebar-item-label", { hasText: "Departmental Needs" })).toBeVisible();
		await expect(rail.locator(".sidebar-item-label", { hasText: "Module Def" })).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
	test("the page-rail breadcrumb returns to the workspace", async ({ page }) => {
		/**
		 * PageRail's goRoute applies the crumb's route as frappe.set_route
		 * *segments*. This page passed a string ("/app/departmental-needs"),
		 * which Function.apply spread into single characters — the click was a
		 * garbage no-op (reported live 2026-08-30).
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, `/${NEED}`);
		await expectScreen(page, "detail");
		await page.locator(".kt-rail-crumb-link", { hasText: "Departmental Needs" }).click();
		await expectScreen(page, "workspace");
		await expect(page).toHaveURL(/\/desk\/departmental-needs$/);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});

