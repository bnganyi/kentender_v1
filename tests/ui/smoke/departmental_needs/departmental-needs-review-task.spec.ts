import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureAuthor, loginAsNdsFixtureReviewer } from "../../helpers/auth";
import { collectConsoleErrors, expectScreen, gotoNeeds, resetFixture, selectContext } from "./helpers";

/**
 * NDS-CHG-001 v1.1 — NDS-UI-05 review task
 * (`/app/departmental-needs/review/{review_task_id}`).
 *
 * The dedicated queue landing (`/review` with no task) was removed on
 * 2026-08-30: the "Review tasks" sidebar entry was a §10 specification defect.
 * A reviewer reaches an open decision through the shared My Work queue, a
 * notification deep link, or the workspace's own role-aware rows — all three
 * end on the same protected task route, which is unchanged.
 *
 * Fixture: `reset_review_task_fixture` — a Submitted Need under PE-CGKIS with
 * one Open `Initial acceptance` task, rebuilt before each test. It is not the
 * §14.3 demo data (DEBT-07), so these tests may decide the task freely.
 */

const NEED = "NDS-CGKIS-2027-0001";

test.describe.configure({ mode: "serial" });

test.describe("NDS-UI-05 review task", () => {
	test.beforeEach(() => resetFixture("reset_review_task_fixture"));

	test("reviewer opens the task from My Work and sees the full submitted version", async ({
		page,
	}) => {
		/**
		 * The corrected pattern: submitted Needs register with the established
		 * My Work queue (kt_my_work_providers), and the row's action lands on
		 * the exact decision screen.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await page.goto("/app/my-work");
		const row = page.locator(".kt-mw-row", { hasText: NEED });
		await expect(row).toBeVisible();
		await expect(row).toContainText("Departmental Needs");
		await row.locator("[data-open]").click();

		await expectScreen(page, "task");
		// §12.5 — the complete submitted version, not a summary. Scoped to the
		// shell: frappe keeps the previous page container (My Work, still
		// holding the row title) in the DOM.
		await expect(
			page.locator('[data-testid="nds-shell"]').getByText("County health records digitisation"),
		).toBeVisible();
		await expect(page.locator('[data-testid="nds-decision-return"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-decision-decline"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-decision-accept"]')).toBeVisible();

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Return asks for a reason and Accept does not", async ({ page }) => {
		/**
		 * NDS-AC-011 / NDS-AC-012 — Return and Decline require a reason; Accept
		 * collects none. Both dialogs are opened and cancelled, so the task is
		 * left open for the next run. Reached through the workspace's own
		 * role-aware row, the in-module route to a decision.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "");
		// §12.1 — two Financial Years are selectable, so the year must be
		// resolved before rows are listed even though this actor has one department.
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "workspace");
		await page
			.locator(
				`[data-testid="nds-need-row"][data-reference="${NEED}"] [data-testid="nds-row-action"][data-action="review"]`,
			)
			.click();
		await expectScreen(page, "task");

		await page.locator('[data-testid="nds-decision-return"]').click();
		await expect(page.locator('[data-testid="nds-dialog-reason"]')).toBeVisible();
		await page.locator('[data-testid="nds-dialog-cancel"]').click();
		await expect(page.locator('[data-testid="nds-dialog-reason"]')).toHaveCount(0);

		await page.locator('[data-testid="nds-decision-accept"]').click();
		await expect(page.locator('[data-testid="nds-dialog-confirm"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-dialog-reason"]')).toHaveCount(0);
		await page.locator('[data-testid="nds-dialog-cancel"]').click();

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the author who submitted the version is offered no decision", async ({ page }) => {
		/**
		 * NDS-AC-010 maker-checker, proved from the browser rather than only in
		 * the service tests. §17 forbids inferring authority from a route: the
		 * author's own workspace row carries no decision action — the server
		 * withheld it, the page did not hide it.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "");
		// §12.1 — two Financial Years are selectable, so the year must be
		// resolved before rows are listed even though this actor has one department.
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "workspace");

		const row = page.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"]`);
		await expect(row).toBeVisible();
		await expect(
			row.locator('[data-testid="nds-row-action"][data-action="review"]'),
		).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the retired queue URL redirects to the workspace", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "/review");
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "workspace");
		await expect(page).toHaveURL(/\/departmental-needs$/);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
