import { expect, test } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { loginAsMohPlanningOfficer, preparePlanningGate04 } from "../../helpers/planningRoles";

const EDITOR_ROOT = '[data-testid="kt-pln-ui06-root"]';
const WORKSPACE_ROOT = '[data-testid="kt-pln-ui01-root"]';
const BUILDER_ROOT = '[data-testid="kt-pln-ui03-root"]';

async function expectSingleVisiblePage(page: import("@playwright/test").Page) {
	const visiblePages = await page.locator(".page-container").evaluateAll((pages) =>
		pages.filter((item) => {
			const style = window.getComputedStyle(item);
			return style.display !== "none" && style.visibility !== "hidden";
		}).length,
	);
	expect(visiblePages).toBe(1);
}

test("Planning SPA navigation clears departing layout state", async ({ page }) => {
	await page.setViewportSize({ width: 1400, height: 900 });
	await loginAsAdministrator(page);
	const prep = await preparePlanningGate04(page, { withPlanItem: true });
	expect(prep.plan_item).toBeTruthy();
	expect(prep.eligible_demand).toBeTruthy();
	await page.context().clearCookies();
	await loginAsMohPlanningOfficer(page);

	await page.goto(
		`/desk/procurement-plan-item-editor?plan_item=${encodeURIComponent(prep.plan_item || "")}`,
		{ waitUntil: "domcontentloaded" },
	);
	await expect(page.locator(`${EDITOR_ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
		timeout: 45_000,
	});
	await expect(page.locator("body")).toHaveClass(/kt-pln-editor-active/);
	await expectSingleVisiblePage(page);

	await page.evaluate(() => {
		(window as unknown as { frappe: { set_route: (route: string) => void } }).frappe.set_route(
			"planning-workspace",
		);
	});
	await expect(page).toHaveURL(/\/desk\/planning-workspace/, { timeout: 30_000 });
	await expect(page.locator(`${WORKSPACE_ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
		timeout: 45_000,
	});
	await expect(page.locator(EDITOR_ROOT)).toBeHidden();
	await expect(page.locator("body")).toHaveClass(/kt-pln-ws-active/);
	await expect(page.locator("body")).not.toHaveClass(/kt-pln-editor-active/);
	await expectSingleVisiblePage(page);

	await page.locator('[data-kt-pln-action="change-context"]').click();
	await page
		.locator('[data-kt-pln-filter="financial_year"]')
		.selectOption(prep.empty_draft_fy || "2029/30");
	const continuePlanning = page.getByTestId("kt-pln-ui01-primary-action");
	await expect(continuePlanning).toContainText(/Continue (planning|plan update)/i, { timeout: 30_000 });
	await continuePlanning.click();
	await expect(page).toHaveURL(/\/desk\/procurement-plan-builder(?:[/?#]|$)/, {
		timeout: 30_000,
	});
	await expect(page.locator(`${BUILDER_ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
		timeout: 45_000,
	});
	await expect(page.locator(WORKSPACE_ROOT)).toBeHidden();
	await expect(page.locator("body")).not.toHaveClass(/kt-pln-ws-active/);
	await expectSingleVisiblePage(page);
});
