import { test, expect } from "@playwright/test";
import { ADMIN, APPROVER, OFFICER, PendingFixture, SuccessorFixture, RETURN_REASON, collectConsoleErrors, expectScreen, gotoBudget, login, resetFixture } from "./helpers";

/**
 * BUD-CHG-001 v1.9 — BUD-UI-04: the decision and its evidence together
 * (§11.8–§11.13, §12.5; BUD19-AC-011/012/013/014/026).
 */
test.describe.configure({ mode: "serial" });

test("review registered allocation: complete set, evidence, one approval activates", async ({ page }) => {
	const fx = resetFixture<PendingFixture>("reset_initial_submitted");
	const errors = collectConsoleErrors(page);
	await login(page, APPROVER);
	await gotoBudget(page, `/review/${fx.pending.version_code}`);
	await expectScreen(page, "review");
	await expect(page.getByRole("heading", { level: 1 })).toHaveText("Review registered allocation");
	await expect(page.getByTestId("bud-task-initial-table")).toContainText("Submitted amount");
	await expect(page.getByTestId("bud-task-initial-table")).toContainText("KES 160,000,000");
	await expect(page.getByTestId("bud-task-evidence")).toContainText("Approved allocation");
	await expect(page.locator("text=Readiness")).toHaveCount(0);
	await expect(page.getByTestId("bud-task-consequence")).toContainText("does not approve the public budget or release cash");
	await page.getByTestId("bud-task-tab-changes").click();
	await expect(page.getByTestId("bud-task-changes-baseline")).toBeVisible();
	await page.getByTestId("bud-task-tab-overview").click();
	await expect(page.getByTestId("bud-task-approve-btn")).toHaveText("Approve registered allocation");
	await page.getByTestId("bud-task-approve-btn").click();
	await expect(page.getByTestId("bud-task-status")).toHaveText("Approved and activated", { timeout: 30_000 });
	await expect(page.getByTestId("bud-task-footer")).toHaveCount(0);
	await expect(page.locator(".modal.show")).toHaveCount(0);
	expect(errors).toEqual([]);
});

test("review allocation changes: changes first, live protection, return with a reason the Officer sees", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_successor_submitted");
	await login(page, APPROVER);
	await gotoBudget(page, `/review/${fx.v2_code}`);
	await expectScreen(page, "review");
	await expect(page.getByRole("heading", { level: 1 })).toHaveText("Review allocation changes");
	await expect(page.getByTestId("bud-task-status")).toContainText("Transfer");
	await expect(page.getByTestId("bud-task-changes-table")).toContainText("− KES 10,000,000");
	await expect(page.getByTestId("bud-task-summary")).toContainText("KES 10,000,000 moves from");
	const protection = page.getByTestId("bud-task-protection-table");
	await expect(protection).toContainText("Reserved + committed");
	await expect(protection).toContainText("Available after update");
	await expect(protection).toContainText("KES 80,000,000");
	await expect(protection).toContainText("KES 10,000,000");
	await expect(page.locator("text=Current floor")).toHaveCount(0);
	await expect(page.locator("text=Headroom")).toHaveCount(0);
	await expect(page.getByTestId("bud-task-live-caption")).toContainText("KenTender checks these amounts again when you approve.");
	await page.getByTestId("bud-task-tab-lines").click();
	await expect(page.getByTestId("bud-task-lines-table")).toContainText("Reserved + committed");
	await page.getByTestId("bud-task-tab-changes").click();
	await expect(page.getByTestId("bud-task-evidence-changes")).toContainText("MOH-FIN-BUD-2027-02 (Demo)");
	await page.goBack();
	await expect(page).toHaveURL(/\/lines$/);
	await page.getByTestId("bud-task-tab-overview").click();

	await page.getByTestId("bud-task-return-btn").click();
	await expect(page.getByTestId("bud-task-return-dialog")).toContainText("What needs to change?");
	await expect(page.getByTestId("bud-task-return-confirm")).toBeDisabled();
	await page.getByTestId("bud-task-return-reason").fill(RETURN_REASON);
	await page.getByTestId("bud-task-return-confirm").click();
	await expect(page.getByTestId("bud-task-status")).toHaveText("Returned for correction", { timeout: 30_000 });
	await expect(page.getByTestId("bud-task-decided")).toContainText(RETURN_REASON);

	await login(page, OFFICER);
	await gotoBudget(page, `/${fx.budget_code}/version/${fx.v2_number}/edit`);
	await expectScreen(page, "editor");
	await expect(page.getByTestId("bud-editor-returned")).toContainText(RETURN_REASON);
});

test("a live breach shows the exact shortfall and blocks approval while Return stays", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_live_breach");
	await login(page, APPROVER);
	await gotoBudget(page, `/review/${fx.v2_code}`);
	await expectScreen(page, "review");
	await expect(page.getByTestId("bud-task-breach")).toContainText("cannot be reduced to KES 90,000,000 because KES 95,000,000 is already reserved or committed. Shortfall: KES 5,000,000.");
	await expect(page.getByTestId("bud-task-protection-table")).toContainText("Shortfall KES 5,000,000");
	await expect(page.getByTestId("bud-task-protection-table")).not.toContainText("−");
	await expect(page.getByTestId("bud-task-approve-btn")).toBeDisabled();
	await expect(page.getByTestId("bud-task-return-btn")).toBeEnabled();
});

test("a technical reader inspects the exact review read-only; a stale approve is a typed result", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_successor_submitted");
	await login(page, ADMIN);
	await gotoBudget(page, `/review/${fx.v2_code}`);
	await expectScreen(page, "review");
	await expect(page.getByTestId("bud-task-technical")).toBeVisible();
	await expect(page.getByTestId("bud-task-footer")).toHaveCount(0);
	await expect(page.getByTestId("bud-task-changes-table")).toBeVisible();

	await login(page, APPROVER);
	await gotoBudget(page, `/review/${fx.v2_code}`);
	await expectScreen(page, "review");
	await page.route("**/api/method/kentender_budget.api.budget_api.approve_budget_version", (route) =>
		route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: { ok: false, code: "BUDGET_STALE_WRITE", errors: { expected_modified: "This budget has changed since you opened it. Refresh to see the current details." } } }) })
	);
	await page.getByTestId("bud-task-approve-btn").click();
	await expect(page.getByTestId("bud-task-stale")).toContainText("This budget has changed since you opened it.");
	await expect(page.locator(".modal.show")).toHaveCount(0);
});
