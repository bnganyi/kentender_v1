import { test, expect } from "@playwright/test";
import { APPROVER, AUDITOR, CANONICAL_BUDGET, ClosureFixture, collectConsoleErrors, expectScreen, gotoBudget, login, resetFixture } from "./helpers";

/**
 * BUD-CHG-001 v1.9 — BUD-DES-17 year-end closure on BUD-UI-03 (§11.18,
 * §12.8; BUD19-AC-021/022): before year end, blocked, ready, confirm, closed.
 */
test.describe.configure({ mode: "serial" });

test("before the year ends the budget explains the date and offers no override", async ({ page }) => {
	resetFixture("reset_default");
	await login(page, APPROVER);
	await gotoBudget(page, `/${CANONICAL_BUDGET}`);
	await expectScreen(page, "detail");
	await expect(page.getByTestId("budget-detail-close-btn")).toHaveText("Close budget");
	await expect(page.getByTestId("budget-detail-close-note")).toContainText("This budget can be closed only after");
	await page.getByTestId("budget-detail-close-btn").click();
	await expectScreen(page, "closure");
	await expect(page.getByTestId("bud-close-before")).toContainText("This budget can be closed only after");
	await expect(page.getByTestId("bud-close-btn")).toBeDisabled();
});

test("a remaining hold blocks closure with the exact amount; Check again changes nothing", async ({ page }) => {
	const fx = resetFixture<ClosureFixture>("reset_close_blocked");
	await login(page, APPROVER);
	await gotoBudget(page, `/${fx.closure.budget_code}/close`);
	await expectScreen(page, "closure");
	await expect(page.getByTestId("bud-close-heading")).toHaveText(`Close budget for FY ${fx.closure.fiscal_year}`);
	await expect(page.getByTestId("bud-close-blocked")).toContainText("This budget cannot be closed yet.");
	await expect(page.getByTestId("bud-close-blocked")).toContainText("KES 20,000,000 remains reserved for requisitions.");
	await expect(page.getByTestId("bud-close-rows")).toContainText("Digital health infrastructure programme");
	await expect(page.getByTestId("bud-close-btn")).toBeDisabled();
	await expect(page.getByRole("button", { name: /release/i })).toHaveCount(0);
	await page.getByTestId("bud-close-check").click();
	await expect(page.getByTestId("bud-close-blocked")).toBeVisible();

	await login(page, AUDITOR);
	await gotoBudget(page, `/${fx.closure.budget_code}/close`);
	await expect(page.getByTestId("bud-close-forbidden")).toBeVisible();
});

test("zero holds with an active commitment permit closure through the focused confirmation", async ({ page }) => {
	const fx = resetFixture<ClosureFixture>("reset_close_ready");
	const errors = collectConsoleErrors(page);
	await login(page, APPROVER);
	await gotoBudget(page, `/${fx.closure.budget_code}/close`);
	await expectScreen(page, "closure");
	await expect(page.getByTestId("bud-close-ready")).toContainText("Closing stops new reservations, conversions and commitment increases. Existing commitments and history remain.");
	await expect(page.getByTestId("bud-close")).toContainText("KES 60,000,000");
	await page.getByTestId("bud-close-btn").click();
	await expect(page.getByTestId("bud-close-confirm")).toContainText(`Close budget for FY ${fx.closure.fiscal_year}?`);
	await page.getByTestId("bud-close-confirm-btn").click();
	await expect(page.getByTestId("bud-close-closed")).toContainText("Closed by", { timeout: 30_000 });
	await expect(page.getByTestId("bud-close-closed")).toContainText("Beatrice Kamau");
	await page.reload({ waitUntil: "domcontentloaded" });
	await expectScreen(page, "closure");
	await expect(page.getByTestId("bud-close-closed")).toBeVisible();
	await page.getByTestId("bud-close-back").click();
	await expectScreen(page, "detail");
	await expect(page.getByTestId("budget-detail-status")).toHaveText("Closed");
	await expect(page.getByTestId("budget-detail-closure")).toContainText("Beatrice Kamau");
	await expect(page.getByTestId("budget-detail-close-btn")).toHaveCount(0);
	expect(errors).toEqual([]);
});
