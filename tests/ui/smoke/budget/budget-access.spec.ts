import { test, expect } from "@playwright/test";
import { ADMIN, CANONICAL_BUDGET, CANONICAL_FY, NOBODY, SuccessorFixture, expectNoFrappeModal, expectScreen, gotoBudget, login, resetFixture, selectYear } from "./helpers";

/**
 * BUD-CHG-001 v1.9 — access and shared states (§7.1, §11.16, §11.20, §12.1,
 * §12.5; BUD19-AC-023/024/025/026): Forbidden paints nothing protected,
 * technical read reaches every route without decision controls, and the
 * compositions survive a narrow viewport and keyboard use.
 */
test.describe.configure({ mode: "serial" });

test("an actor with no Budget responsibility sees only the inline Forbidden panel on every route", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_successor_submitted");
	await login(page, NOBODY);
	for (const route of ["", `/${fx.budget_code}`, `/${fx.budget_code}/version/${fx.v2_number}/edit`, `/review/${fx.v2_code}`, `/line/${fx.dhi_code}`, `/${fx.budget_code}/close`, "/new"]) {
		await gotoBudget(page, route);
		await expect(page.locator('[data-testid$="forbidden"]').first()).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("budget-fy-filter")).toHaveCount(0);
		await expect(page.locator("text=KES")).toHaveCount(0);
		await expectNoFrappeModal(page);
	}
});

test("a technical reader reads every route, including Draft and Submitted versions, with no business controls", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_successor_submitted");
	await login(page, ADMIN);
	await gotoBudget(page);
	await selectYear(page, CANONICAL_FY);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	await expect(page.getByTestId("budget-pending-action-btn")).toHaveText("View version (read-only)");
	await gotoBudget(page, `/${fx.budget_code}/version/${fx.v2_number}/edit`);
	await expectScreen(page, "editor");
	await expect(page.getByTestId("bud-editor-readonly")).toBeVisible();
	await gotoBudget(page, `/review/${fx.v2_code}`);
	await expectScreen(page, "review");
	await expect(page.getByTestId("bud-task-footer")).toHaveCount(0);
	await gotoBudget(page, `/${fx.budget_code}`);
	await expectScreen(page, "detail");
	await expect(page.getByTestId("budget-detail-update-btn")).toHaveCount(0);
	await gotoBudget(page, `/line/${fx.dhi_code}`);
	await expectScreen(page, "line");
});

test("narrow screens keep the line name, amount and blocker; tabs work from the keyboard", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_live_breach");
	await login(page, "beatrice.kamau@moh.example.test");
	await gotoBudget(page, `/review/${fx.v2_code}`);
	await expectScreen(page, "review");
	await page.setViewportSize({ width: 400, height: 900 });
	await expect(page.getByTestId("bud-task-breach")).toBeVisible();
	await expect(page.getByTestId("bud-task-changes-table")).toContainText("Digital health infrastructure programme");
	const overflow = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2);
	expect(overflow).toBe(false);
	await page.getByTestId("bud-task-tab-lines").focus();
	await page.keyboard.press("Enter");
	await expect(page).toHaveURL(/\/lines$/);
	await expect(page.getByTestId("bud-task-lines-table")).toBeVisible();
});
