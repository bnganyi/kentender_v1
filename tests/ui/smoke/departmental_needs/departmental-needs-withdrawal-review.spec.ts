import { test, expect } from "@playwright/test";

import { loginAsNdsFixtureReviewer } from "../../helpers/auth";
import { clearFixtures, collectConsoleErrors, expectScreen, gotoNeeds, resetFixture, selectContext } from "./helpers";

/**
 * NDS-CHG-001 v1.6 — NDS-UI-07 withdrawal review
 * (`/app/departmental-needs/review/{review_task_id}/withdrawal`).
 *
 * The second of the four screens DEBT-06 recorded as unproven. Its audience is
 * the Head of User Department only.
 *
 * Fixtures are `reset_withdrawal_blocked_fixture` / `_cleared_fixture` under
 * the dedicated Playwright Organisation Unit (DEBT-07), rebuilt per test, so
 * these specs execute a real Approve without touching the §14.3 demo Needs.
 *
 * §12.6 is the rule under test: the screen reads the Planning dependency
 * **fresh** on every load and never trusts a cached button state, because the
 * dependency can clear or appear between the request and the decision.
 */

let NEED = "";

test.describe.configure({ mode: "serial" });

test.describe("NDS-UI-07 withdrawal review", () => {
	test.afterAll(() => clearFixtures());

	async function openWithdrawal(page: import("@playwright/test").Page) {
		await gotoNeeds(page, "");
		// §12.1 — defensive no-op here: this actor holds exactly one department
		// grant, so the workspace resolves straight to "workspace" with no
		// picker to select (see selectContext's own doc comment in helpers.ts).
		await selectContext(page);
		await expectScreen(page, "workspace");
		// §12.2 — an open withdrawal is a decision this reviewer holds; the
		// workspace's role-aware row (like My Work) leads to NDS-UI-07.
		await page
			.locator(
				`[data-testid="nds-need-row"][data-reference="${NEED}"] [data-testid="nds-row-action"][data-action="withdrawal"]`,
			)
			.click();
		await expectScreen(page, "withdrawal");
	}

	test("an Active Plan dependency blocks the decision (NDS-DES-12a)", async ({ page }) => {
		NEED = resetFixture<{ need: string }>("reset_withdrawal_blocked_fixture").need;
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
		NEED = resetFixture<{ need: string }>("reset_withdrawal_cleared_fixture").need;
		const errors = collectConsoleErrors(page);
		await loginAsNdsFixtureReviewer(page);
		await openWithdrawal(page);

		await expect(page.locator('[data-testid="nds-withdrawal-approve"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-withdrawal-decline"]')).toBeVisible();
		await expect(page.locator('[data-testid="nds-view-plan-item"]')).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("approving a cleared withdrawal completes it", async ({ page }) => {
		NEED = resetFixture<{ need: string }>("reset_withdrawal_cleared_fixture").need;
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
