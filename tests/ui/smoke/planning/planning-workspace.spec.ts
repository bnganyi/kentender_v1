import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUDITOR,
	AUTHOR,
	NOBODY,
	OUTSIDER,
	OU_NAME,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectFixtureYear,
	expectReady,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.12 Phase 3 (Slice A) — PLN-UI-01 workspace, the Financial
 * Year filter and the PLN-DES-16 Forbidden state, per role, in a real browser
 * on the D13 world (no Procuring Entity anywhere).
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("PLN-UI-01 Procurement Planning workspace", () => {
	test.beforeEach(() => {
		resetFixture("reset_workspace_fixture");
	});
	test.afterAll(() => restoreSite());

	test("author is offered Open departmental plan, opens it and sees the live re-render", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");

		// PLN-DES-01 masthead, exact copy; no header action button; the FY is a
		// plain inline filter, never a card; no Procuring Entity control.
		await expect(page.locator(".kt-page-kicker")).toHaveText("PROCUREMENT PLANNING");
		await expect(page.locator(".kt-page-title")).toHaveText("Annual procurement planning");
		await expect(page.locator(".pln-masthead button")).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-context-strip"]')).not.toHaveClass(/kt-card/);
		await expect(page.locator('[data-testid="pln-pe-select"]')).toHaveCount(0);
		await expectFixtureYear(page);

		// The one offered action for an empty department while intake is open.
		const rows = page.locator('[data-testid="pln-action-row"]');
		await expect(rows).toHaveCount(1);
		await expect(rows.first().locator(".pln-ready-headline")).toHaveText("Open departmental plan");
		await expect(rows.first().locator(".pln-ready-sub")).toHaveText(OU_NAME);
		await expect(page.locator('[data-testid="pln-count-label"]')).toHaveText("0 departmental plans");
		await expect(page.locator('[data-testid="pln-schedule-health"]')).toHaveCount(0);

		// A real §8.2 command from the button, then the interactive re-render.
		await page.locator('[data-testid="pln-work-action-0"]').click();
		await expect(rows.first().locator(".pln-ready-headline")).toHaveText("Continue departmental plan", { timeout: 30_000 });
		const planRow = page.locator('[data-testid="pln-departmental-plans"] tbody tr');
		await expect(planRow).toHaveCount(1);
		await expect(planRow).toContainText(OU_NAME);
		await expect(planRow.locator(".kt-status")).toHaveText("Draft");
		await expect(page.locator('[data-testid="pln-count-label"]')).toHaveText("1 departmental plan");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("planner sees Ready to consolidate after acceptance and Open Annual Plan routes to the plan", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_accepted_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expectFixtureYear(page);

		const card = page.locator('[data-testid="pln-actionable"]');
		await expect(card.locator(".kt-card-title")).toHaveText("Ready to consolidate");
		await expect(card.locator("table")).toHaveCount(0);
		const row = card.locator('[data-testid="pln-action-row"]');
		await expect(row).toHaveCount(1);
		await expect(row.locator(".pln-ready-headline")).toHaveText(
			"2 accepted departmental entries ready to consolidate"
		);
		await expect(row.locator(".pln-ready-sub")).toContainText("KES 100,000,000");
		await expect(page.locator('[data-testid="pln-plan-summary"]')).toHaveText("· Annual Plan · Draft Version 1");
		await expect(page.locator('[data-testid="pln-departmental-plans"] .kt-card-title')).toHaveText(
			"Departmental plans feeding this Annual Plan"
		);
		const planRows = page.locator('[data-testid="pln-departmental-plans"] tbody tr');
		await expect(planRows).toHaveCount(2);
		await expect(planRows.first().locator(".kt-status")).toHaveText("Accepted");
		await expect(page.locator('[data-testid="pln-count-label"]')).toHaveText("2 departmental plans");

		await row.locator("button").click();
		await expectReady(page, "plan");
		await expect(page).toHaveURL(new RegExp(`/annual-procurement-plan/${state.plan_reference}$`));
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("auditor reads the register but is offered no work at all", async ({ page }) => {
		resetFixture("reset_accepted_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expectFixtureYear(page);

		// Absence assertions: nothing decidable is offered, rows stay readable.
		await expect(page.locator('[data-testid="pln-actionable"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-plans"] tbody tr')).toHaveCount(2);
		await expect(page.locator('[data-testid="pln-departmental-plans"] tbody button')).toHaveCount(2);
		await expect(page.locator('[data-testid="pln-forbidden"]')).toHaveCount(0);
	});

	test("a stale Frappe Role without a responsibility assignment gets the Forbidden panel and nothing else (PLN-AC-111..113)", async ({ page }) => {
		await login(page, NOBODY, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");

		const card = page.locator('[data-testid="pln-forbidden"]');
		await expect(card.locator("h3")).toHaveText("You do not have access to Procurement Planning");
		await expect(card).toContainText(
			"This area needs one of these responsibilities: Procurement Planner, Finance Confirmation Officer, Accounting Officer"
		);
		await expect(card).toContainText("Ask your KenTender administrator to assign one in System setup.");
		await expect(card.locator("button")).toHaveCount(0);
		// Nothing else renders: no filter, no tables, no work.
		await expect(page.locator('[data-testid="pln-context-strip"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-departmental-plans"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-actionable"]')).toHaveCount(0);
	});

	test("an author from another department sees an empty register, never the other unit's plan", async ({ page }) => {
		resetFixture("reset_accepted_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OUTSIDER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expectFixtureYear(page);
		// their own Draft (opened by the fixture) and nothing of the other unit
		const rows = page.locator('[data-testid="pln-departmental-plans"] tbody tr');
		await expect(rows).toHaveCount(1);
		await expect(rows.first()).not.toContainText(OU_NAME);
		await expect(page.locator('[data-testid="pln-forbidden"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
