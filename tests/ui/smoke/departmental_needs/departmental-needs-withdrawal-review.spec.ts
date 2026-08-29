import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureReviewer } from "../../helpers/auth";
import { clearFixtures, collectConsoleErrors, expectScreen, gotoNeeds, resetFixture, selectContext } from "./helpers";

/**
 * NDS-CHG-001 v1.1 — NDS-UI-07 withdrawal review
 * (`/app/departmental-needs/review/{review_task_id}/withdrawal`).
 *
 * The second of the four screens DEBT-06 recorded as unproven. Its audience is
 * the Head of User Department only.
 *
 * Fixtures are `reset_withdrawal_blocked_fixture` / `_cleared_fixture` under
 * PE-CGKIS (DEBT-07), rebuilt per test, so these specs execute a real Approve
 * without touching the §14.3 demo Needs.
 *
 * §12.6 is the rule under test: the screen reads the Planning dependency
 * **fresh** on every load and never trusts a cached button state, because the
 * dependency can clear or appear between the request and the decision.
 */

const NEED = "NDS-CGKIS-2027-0001";

test.describe.configure({ mode: "serial" });

test.describe("NDS-UI-07 withdrawal review", () => {
	test.afterAll(() => clearFixtures());

	async function openWithdrawal(page: import("@playwright/test").Page) {
		await gotoNeeds(page, "/review");
		// §12.1 — two Financial Years are selectable, so the year must be
		// resolved before rows are listed even though this actor has one department.
		await selectContext(page, "CGK-DEPT-HEALTH");
		await expectScreen(page, "review");
		// §12.2 — an open withdrawal is a decision this reviewer holds, so it
		// reaches them through the same queue; §10 gives it no other entry.
		await page
			.locator(
				`[data-testid="nds-need-row"][data-reference="${NEED}"] [data-testid="nds-row-action"][data-action="withdrawal"]`,
			)
			.click();
		await expectScreen(page, "withdrawal");
	}

	test("an Active Plan dependency blocks the decision (NDS-DES-12a)", async ({ page }) => {
		resetFixture("reset_withdrawal_blocked_fixture");
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await openWithdrawal(page);

		// NDS-AC-019 — the dependency is shown, and Approve is simply absent
		// rather than present-and-disabled: §12.6 gives the blocked variant only
		// Close, so there is no control to mis-click.
		await expect(page.locator('[data-testid="nds-view-plan-item"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-withdrawal-close"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-withdrawal-approve"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="nds-withdrawal-decline"]')).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a cleared dependency allows Approve and Decline (NDS-DES-12b)", async ({ page }) => {
		resetFixture("reset_withdrawal_cleared_fixture");
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await openWithdrawal(page);

		await expect(page.locator('[data-testid="nds-withdrawal-approve"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-withdrawal-decline"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-view-plan-item"]')).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("approving a cleared withdrawal completes it", async ({ page }) => {
		resetFixture("reset_withdrawal_cleared_fixture");
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await openWithdrawal(page);

		await page.locator('[data-testid="nds-withdrawal-approve"]').click();
		await page.locator('[data-testid="nds-dialog-confirm"]').click();

		// §5.3 — the decision completes the task, so the queue no longer offers
		// it. Landing anywhere other than an errored page is the assertion; the
		// resulting Need state is covered by the service tests.
		await expect(page.locator('[data-testid="nds-shell"]')).toHaveAttribute(
			"data-loading",
			"false",
			{ timeout: 30_000 },
		);
		await expect(page.locator('[data-testid="nds-error-summary"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
