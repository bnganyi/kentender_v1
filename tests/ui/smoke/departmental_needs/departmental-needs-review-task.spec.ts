import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureAuthor, loginAsNdsFixtureReviewer } from "../../helpers/auth";
import { collectConsoleErrors, expectScreen, gotoNeeds, resetFixture, selectContext } from "./helpers";

/**
 * NDS-CHG-001 v1.1 — NDS-UI-05 review task
 * (`/app/departmental-needs/review/{review_task_id}`).
 *
 * One of the four screens DEBT-06 recorded as built but unproven: its only
 * audience is the Head of User Department, and an interactive session on this
 * site cannot switch users (the logout endpoints return 403 and the session
 * cookie is httpOnly). Playwright logs in per role, which is the whole reason
 * these specs exist.
 *
 * Fixture: `reset_review_task_fixture` — a Submitted Need under PE-CGKIS with
 * one Open `Initial acceptance` task, rebuilt before each test. It is not the
 * §14.3 demo data (DEBT-07), so these tests may decide the task freely.
 */

const NEED = "NDS-CGKIS-2027-0001";

test.describe.configure({ mode: "serial" });

test.describe("NDS-UI-05 review task", () => {
	test.beforeEach(() => resetFixture("reset_review_task_fixture"));

	test("reviewer opens the task from the queue and sees the full submitted version", async ({
		page,
	}) => {
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "/review");
		// §12.1 — two Financial Years are selectable, so the year must be
		// resolved before rows are listed even though this actor has one department.
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "review");

		// §12.2 — the queue's rows are the open decisions this reviewer holds,
		// and the server decided which action each row exposes.
		const row = page.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"]`);
		await expect(row).toBeVisible();
		await row.locator('[data-testid="nds-row-action"][data-action="review"]').click();

		await expectScreen(page, "task");
		// §12.5 — the complete submitted version, not a summary.
		await expect(page.getByText("County health records digitisation")).toBeVisible();
		await expect(page.locator('[data-testid="nds-decision-return"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-decision-decline"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-decision-accept"]')).toBeVisible();

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Return asks for a reason and Accept does not", async ({ page }) => {
		/**
		 * NDS-AC-011 / NDS-AC-012 — Return and Decline require a reason; Accept
		 * collects none. Both dialogs are opened and cancelled, so the task is
		 * left open for the next run.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await gotoNeeds(page, "/review");
		// §12.1 — two Financial Years are selectable, so the year must be
		// resolved before rows are listed even though this actor has one department.
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "review");
		await page
			.locator(`[data-testid="nds-need-row"][data-reference="${NEED}"] [data-testid="nds-row-action"]`)
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
		 * the service tests. §17 forbids inferring authority from a route, so
		 * the author reaches /review directly and is still offered nothing to
		 * decide — the server withheld the action, the page did not hide it.
		 */
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureAuthor(page);
		await gotoNeeds(page, "/review");
		// §12.1 — two Financial Years are selectable, so the year must be
		// resolved before rows are listed even though this actor has one department.
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "review");

		const decision = page.locator(
			`[data-testid="nds-need-row"][data-reference="${NEED}"] [data-testid="nds-row-action"][data-action="review"]`,
		);
		await expect(decision).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
