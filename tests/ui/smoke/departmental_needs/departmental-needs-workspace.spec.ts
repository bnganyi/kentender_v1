import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureAuthor } from "../../helpers/auth";
import {
	clearFixtures,
	collectConsoleErrors,
	expectScreen,
	gotoNeeds,
	resetFixture,
	selectContext,
} from "./helpers";

/**
 * NDS-CHG-001 v1.1 — NDS-UI-01 requester workspace (`/app/departmental-needs`)
 * and NDS-UI-03 need editor (`/app/departmental-needs/new`).
 *
 * Replaces the pre-v1.1 workspace/create/edit specs, which drove the retired
 * NDS-CHG-002 routes and screens (`departmental-needs-new`, the items table,
 * attachments, indicative cost) that §1.1 removed outright.
 *
 * Fixture: `reset_open_intake_fixture` — an Open intake window and one Draft
 * under PE-CGKIS, because §5.1 gates creation on an Open window and the
 * fixture entity's default window is deliberately Scheduled (the NDS-UI-08
 * spec rewrites that one).
 */

const NEED = "NDS-CGKIS-2027-0001";

test.describe.configure({ mode: "serial" });

test.describe("NDS-UI-01 workspace and NDS-UI-03 editor", () => {
	test.beforeEach(() => resetFixture("reset_open_intake_fixture"));
	test.afterAll(() => clearFixtures());

	test("the workspace lists the author's needs with one action each", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "workspace");

		// §1.1 replaced four summary cards and split action/waiting sections with
		// one role-appropriate table, so exactly one table is the assertion.
		await expect(page.locator('[data-testid="nds-needs-table"]')).toHaveCount(1);
		const row = page.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"]`);
		await expect(row).toBeVisible();
		await expect(row).toHaveAttribute("data-status", "Draft");
		// Complete visibility of authorship: the workspace also serves the
		// reviewer through the main rail entry, where rows are not their own.
		await expect(
			page.locator('[data-testid="nds-needs-table"] th', { hasText: "Requested by" }),
		).toBeVisible();
		await expect(row).toContainText("Playwright Author");
		// §12.1 — a Draft belongs to its author, so the row offers Continue.
		await expect(row.locator('[data-testid="nds-row-action"]')).toHaveAttribute(
			"data-action",
			"edit",
		);
		await expect(page.locator('[data-testid="nds-count"]')).toContainText("need");

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Create need is offered while intake is Open and opens the editor", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page, "CGK-DEPT-HEALTH");
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

	test("a Draft opens in the editor and saves", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		await selectContext(page, "CGK-DEPT-HEALTH");
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
	test("an unparseable typed date blocks the submit with a field error", async ({ page }) => {
		/**
		 * A native date input holding text that does not parse (the reported
		 * case: 31/09/2026) keeps the text visible but reports value "" — the
		 * old behaviour silently dropped it and the server answered
		 * "Required-by date is required." for a field that looked filled in.
		 * The editor now refuses to emit and names the real problem.
		 */
		resetFixture("reset_open_intake_fixture");
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
		resetFixture("reset_open_intake_fixture");
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
		resetFixture("reset_open_intake_fixture");
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

