import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	loginAsPlanningMultiPlanner,
	loginAsPlanningSystemAdminNoScope,
	preparePlanningGate03,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui02-root"]';

test.describe("PLN-UI-02 Register annual plan", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("single PE: Stitch regions, no budget, stitch chrome", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate03(page);
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto("/desk/procurement-plan-register", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(
			page.getByRole("heading", { name: "Create annual procurement plan" }),
		).toBeVisible();
		await expect(page.getByText("1. Plan ownership")).toBeVisible();
		await expect(page.getByText("2. Plan details")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui02-period")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui02-period")).toContainText(/Plan period:/i);
		const currency = page.getByTestId("kt-pln-ui02-currency");
		await expect(currency).toBeVisible();
		await expect(currency).toContainText("KES - Kenyan Shilling");
		await expect(currency.locator('option[value="USD"]')).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui02-actions")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui02-submit")).toContainText(/Create plan/i);
		await expect(page.getByTestId("kt-pln-ui02-pe-readonly")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui02-pe-readonly")).toContainText(
			/Ministry|PE-MOH|Health/i,
		);
		await expect(page.locator("[data-kt-pln-pe-helper]")).toContainText(
			/Assigned from your authorised scope/i,
		);
		await expect(page.locator('[data-kt-field="budget"]')).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui02-no-budget")).toHaveCount(0);
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui02-root",
			primaryCtaTestId: "kt-pln-ui02-submit",
			selectSelector: '[data-kt-field="financial_year"]',
		});

		// Inline validation — no Message dialog.
		await page.locator('[data-kt-field="coordinating_org_unit"]').evaluate((el) => {
			(el as HTMLSelectElement).value = "";
		});
		await page.getByTestId("kt-pln-ui02-submit").click();
		await expect(page.locator('[data-kt-field-error="coordinating_org_unit"]')).toBeVisible({
			timeout: 10_000,
		});
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);

		// Happy path create → builder.
		const fy = prep.create_fy || "2028/29";
		await page.locator('[data-kt-field="financial_year"]').selectOption(fy);
		// FY change reloads scope — wait for live form again.
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 15_000,
		});
		const ou = page.locator('[data-kt-field="coordinating_org_unit"]');
		await expect(ou.locator("option")).not.toHaveCount(0, { timeout: 10_000 });
		const firstOu = await ou.locator("option").first().getAttribute("value");
		await ou.selectOption(firstOu || { index: 0 });
		await page.getByTestId("kt-pln-ui02-submit").click();
		await expect(page).toHaveURL(/procurement-plan-builder/, { timeout: 45_000 });
		await expect(page.locator('[data-testid="kt-pln-ui03-root"][data-kt-pln-live="1"]')).toBeVisible({
			timeout: 45_000,
		});
	});

	test("multi PE: searchable select required", async ({ page }) => {
		await loginAsAdministrator(page);
		await preparePlanningGate03(page);
		await page.context().clearCookies();
		await loginAsPlanningMultiPlanner(page);
		await page.goto("/desk/procurement-plan-register", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.locator(`${ROOT}`)).toHaveAttribute(
			"data-kt-pln-mode",
			"multi_required",
		);
		await expect(page.getByTestId("kt-pln-ui02-pe")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui02-pe-readonly")).toBeHidden();
		const options = page.locator('[data-kt-field="procuring_entity"] option');
		expect(await options.count()).toBeGreaterThanOrEqual(2);
	});

	test("zero scope: registration blocked", async ({ page }) => {
		await loginAsPlanningSystemAdminNoScope(page);
		await page.goto("/desk/procurement-plan-register", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui02-blocked")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui02-form")).toBeHidden();
	});
});
