import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureAuthor, loginAsNdsFixturePlanner } from "../../helpers/auth";
import { collectConsoleErrors, expectScreen, gotoNeeds, resetFixture, selectContext } from "./helpers";

/**
 * NDS-CHG-001 v1.1 — NDS-UI-08 intake window
 * (`/app/departmental-needs/intake-window`).
 *
 * The third of the four screens DEBT-06 recorded as unproven. Its audience is
 * the Procurement Planner alone: NDS-AC-043 gives the Planner the window and
 * no Need decision at all, and §10 shows the menu entry only to that role.
 *
 * The window under test belongs to PE-CGKIS, not the §14.1 MoH window
 * (DEBT-07) — precisely so the spec can save over it without changing what the
 * Python suite asserts.
 */

test.describe.configure({ mode: "serial" });

test.describe("NDS-UI-08 intake window", () => {
	test.beforeEach(() => resetFixture("reset_intake_window_fixture"));

	test("the planner maintains only the two instants", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixturePlanner(page);
		await gotoNeeds(page, "/intake-window");
		// §12.1 — two Financial Years are selectable, so the year must be
		// resolved before rows are listed even though this actor has one department.
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "intake");

		// §12.7 — only the open and close instants. No status command, no
		// approval lifecycle, no Need list.
		await expect(page.locator('[data-testid="nds-opens-at"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-closes-at"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-save-window"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-needs-table"]')).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("saving a valid window succeeds", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixturePlanner(page);
		await gotoNeeds(page, "/intake-window");
		// §12.1 — two Financial Years are selectable, so the year must be
		// resolved before rows are listed even though this actor has one department.
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "intake");

		await page.locator('[data-testid="nds-opens-at"]').fill("2026-09-01T00:00");
		await page.locator('[data-testid="nds-closes-at"]').fill("2026-10-31T23:59");
		await page.locator('[data-testid="nds-save-window"]').click();

		await expect(page.locator('[data-testid="nds-error-summary"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a close before the open is refused by the server", async ({ page }) => {
		/**
		 * §4.6 orders the two instants in the DocType controller, so the refusal
		 * is a real server rejection surfaced in the error summary — not a
		 * client-side guard the user could bypass by typing the route.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixturePlanner(page);
		await gotoNeeds(page, "/intake-window");
		// §12.1 — two Financial Years are selectable, so the year must be
		// resolved before rows are listed even though this actor has one department.
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "intake");

		await page.locator('[data-testid="nds-opens-at"]').fill("2026-10-31T23:59");
		await page.locator('[data-testid="nds-closes-at"]').fill("2026-09-01T00:00");
		await page.locator('[data-testid="nds-save-window"]').click();

		await expect(page.locator('[data-testid="nds-error-summary"]')).toBeVisible();
		// §12.6 — the refusal renders once, inline. frappe.call would also raise
		// Frappe's own "Message" modal from _server_messages unless the adapter
		// passes silent: true, covering the screen with a second copy. The modal
		// mounts a tick *after* the summary renders (the rejection reaches the
		// component before request.js shows messages), so an immediate
		// zero-count check races past it — hence the bounded grace wait.
		await page.waitForTimeout(500);
		await expect(page.locator(".msgprint")).not.toBeVisible();
	});

	test("the rail entry opens the window in place, from the configuration group", async ({
		page,
		context,
	}) => {
		/**
		 * Two rail contracts, both invisible to the Python export tests because
		 * those read `procurement.json` rather than the rendered sidebar:
		 *
		 * 1. Frappe hard-codes `target="_blank"` on every `URL` sidebar row
		 *    (`sidebar_item.html`), which opened NDS-UI-08 in a second browser
		 *    tab. A sub-route cannot be a `Page` link — `link_to` is a Dynamic
		 *    Link validated against a real `Page` record — so the row stays
		 *    `URL` and `procurement_sidebar_header.js` strips the target for
		 *    same-origin paths. A Frappe upgrade that reshapes
		 *    `TypeLink.prototype.make` turns that patch into a silent no-op.
		 * 2. NDS-UI-08 is configuration, so it is a child of the
		 *    "Configuration and Governance" section rather than a flat row
		 *    beside its module (see FOLLOW_UPS FU-08).
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixturePlanner(page);
		await gotoNeeds(page);

		const section = page.locator(
			'.body-sidebar .sidebar-item-container.section-item[data-id="Configuration and Governance"]',
		);
		await expect(section).toBeVisible();
		const entry = section.locator(
			'a.item-anchor[href="/desk/departmental-needs/intake-window"]',
		);
		await expect(entry).toHaveCount(1);
		await expect(entry).not.toHaveAttribute("target", /.+/);

		// The group ships collapsed (`keep_closed`), but its state is remembered
		// per browser, so only expand when the entry is actually hidden.
		if (!(await entry.isVisible())) {
			await section.locator(".item-anchor.section-break").first().click();
		}
		const tabsBefore = context.pages().length;
		await entry.click();

		await expect(page).toHaveURL(/\/desk\/departmental-needs\/intake-window$/);
		expect(context.pages().length, "the rail must not open a second tab").toBe(tabsBefore);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("an author who types the route gets no window editor", async ({ page }) => {
		/**
		 * NDS-AC-043 / §17 — hiding the menu entry is presentation. The control
		 * is that the author cannot save a window, and the screen gives her
		 * nothing to save with.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "/intake-window");
		await expect(page.locator('[data-testid="nds-shell"]')).toHaveAttribute(
			"data-loading",
			"false",
			{ timeout: 30_000 },
		);
		await expect(page.locator('[data-testid="nds-save-window"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
