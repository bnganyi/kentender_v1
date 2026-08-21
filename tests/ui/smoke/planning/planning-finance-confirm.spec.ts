import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohBudgetOfficer,
	loginAsMohPlanningOfficer,
	loginAsMohPlanningViewer,
	preparePlanningFinance,
	preparePlanningFinanceShortfall,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui03-root"]';

function builderFinanceUrl(plan: string, task: string) {
	return `/desk/procurement-plan-builder?plan=${encodeURIComponent(plan)}&finance_task=${encodeURIComponent(task)}`;
}

test.describe("PLN-UI-07 Finance confirmation (sufficient)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Budget Officer opens the drawer and confirms funding", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningFinance(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		expect(prep.finance_task).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohBudgetOfficer(page);
		await page.goto(builderFinanceUrl(prep.empty_draft_plan || "", prep.finance_task || ""), {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		const drawer = page.getByTestId("kt-pln-ui07-drawer");
		await expect(drawer).toBeVisible({ timeout: 20_000 });
		await expect(drawer.getByTestId("kt-pln-ui07-title")).toContainText(
			/Confirm Plan Item funding/i,
		);
		await expect(drawer.getByTestId("kt-pln-ui07-money")).toBeVisible();
		await expect(drawer.getByTestId("kt-pln-ui07-money")).toContainText(/KES /);
		await expect(drawer.getByTestId("kt-pln-ui07-confirm")).toBeVisible();
		await expect(drawer.getByTestId("kt-pln-ui07-return")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui07a-title")).toBeHidden();
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui03-root",
			primaryCtaTestId: "kt-pln-ui07-confirm",
			assertHeadline: false,
		});
		await drawer.getByTestId("kt-pln-ui07-confirm").click();
		await expect(drawer).toBeHidden({ timeout: 20_000 });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-table")).toContainText(/Confirmed/i);
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
	});

	test("Viewer cannot open the Finance Confirm drawer", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningFinance(page);
		expect(prep.finance_task).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningViewer(page);
		await page.goto(builderFinanceUrl(prep.empty_draft_plan || "", prep.finance_task || ""), {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui07-drawer")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui07-confirm")).toBeHidden();
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
	});

	test("planner cannot open the Finance drawer", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningFinance(page);
		expect(prep.finance_task).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(builderFinanceUrl(prep.empty_draft_plan || "", prep.finance_task || ""), {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui07-drawer")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui07-confirm")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui05-open-finance")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
	});

	test("return without a reason shows an inline error, not a Message dialog", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningFinance(page);
		expect(prep.finance_task).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohBudgetOfficer(page);
		await page.goto(builderFinanceUrl(prep.empty_draft_plan || "", prep.finance_task || ""), {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		const drawer = page.getByTestId("kt-pln-ui07-drawer");
		await expect(drawer).toBeVisible({ timeout: 20_000 });
		const sufficient = drawer.locator('[data-kt-pln-07-variant="sufficient"]');
		await sufficient.getByTestId("kt-pln-ui07-return").click();
		await expect(sufficient.locator('[data-kt-field-error="reason"]').first()).toBeVisible();
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
		await expect(drawer).toBeVisible();
	});
});

test.describe("PLN-UI-07A Finance confirmation (shortfall)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Budget Officer sees 80/25/55 shortfall and no Confirm funding", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningFinanceShortfall(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		expect(prep.finance_task).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohBudgetOfficer(page);
		await page.goto(builderFinanceUrl(prep.empty_draft_plan || "", prep.finance_task || ""), {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		const drawer = page.getByTestId("kt-pln-ui07-drawer");
		await expect(drawer).toBeVisible({ timeout: 20_000 });
		const shortfall = drawer.locator('[data-kt-pln-07-variant="shortfall"]');
		await expect(shortfall.getByTestId("kt-pln-ui07a-title")).toContainText(/Funding shortfall/i);
		await expect(shortfall.getByTestId("kt-pln-ui07a-money")).toContainText(/KES 80,000,000/);
		await expect(shortfall.getByTestId("kt-pln-ui07a-money")).toContainText(/KES 25,000,000/);
		await expect(shortfall.getByTestId("kt-pln-ui07a-money")).toContainText(/KES 55,000,000/);
		await expect(shortfall).toContainText(/Insufficient funding/i);
		await expect(shortfall.locator('[data-testid="kt-pln-ui07-confirm"]')).toHaveCount(0);
		await expect(drawer.getByTestId("kt-pln-ui07-confirm")).toBeHidden();
		const resolve = shortfall.getByTestId("kt-pln-ui07a-resolve");
		await expect(resolve).toBeVisible();
		await expect(resolve).toHaveAttribute("href", /budget-funding-activity\//);
		await expect(shortfall.getByTestId("kt-pln-ui07a-return")).toBeVisible();
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui03-root",
			primaryCtaTestId: "kt-pln-ui07a-resolve",
			assertHeadline: false,
		});
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(builderFinanceUrl(prep.empty_draft_plan || "", prep.finance_task || ""), {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui07-drawer")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui07a-title")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui07-confirm")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui05-open-finance")).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
	});

	test("shortfall return without a reason shows an inline error, not a Message dialog", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningFinanceShortfall(page);
		expect(prep.finance_task).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohBudgetOfficer(page);
		await page.goto(builderFinanceUrl(prep.empty_draft_plan || "", prep.finance_task || ""), {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		const drawer = page.getByTestId("kt-pln-ui07-drawer");
		await expect(drawer).toBeVisible({ timeout: 20_000 });
		const shortfall = drawer.locator('[data-kt-pln-07-variant="shortfall"]');
		await shortfall.getByTestId("kt-pln-ui07a-return").click();
		await expect(shortfall.locator('[data-kt-field-error="reason"]').first()).toBeVisible();
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
		await expect(drawer).toBeVisible();
	});

	test("releasing the competing hold revalidates the same task to Confirm funding", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningFinanceShortfall(page);
		expect(prep.finance_task).toBeTruthy();
		const hold = prep.hold || "RSV-MOH-SHORT-001";
		await page.context().clearCookies();
		await loginAsMohBudgetOfficer(page);
		await page.goto(builderFinanceUrl(prep.empty_draft_plan || "", prep.finance_task || ""), {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui07a-title")).toBeVisible({ timeout: 20_000 });
		const released = await page.evaluate(async (reservationId: string) => {
			const r = await (
				window as unknown as {
					frappe: {
						call: (o: {
							method: string;
							args: { reservation_id: string };
						}) => Promise<{ message?: { ok?: boolean } }>;
					};
				}
			).frappe.call({
				method: "kentender_budget.api.dia_budget_control.release_reservation",
				args: { reservation_id: reservationId },
			});
			return r.message || {};
		}, hold);
		expect(released.ok).toBeTruthy();
		await page.goto(builderFinanceUrl(prep.empty_draft_plan || "", prep.finance_task || ""), {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui07-drawer")).toBeVisible({ timeout: 20_000 });
		await expect(page.getByTestId("kt-pln-ui07-title")).toContainText(
			/Confirm Plan Item funding/i,
		);
		await expect(page.getByTestId("kt-pln-ui07-confirm")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui07a-title")).toBeHidden();
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
	});
});
