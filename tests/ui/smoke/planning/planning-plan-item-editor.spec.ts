import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	preparePlanningGate04,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui06-root"]';

test.describe("PLN-UI-06 Plan Item editor", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("loads editor and shows inline field errors (no Message dialog)", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate04(page, { withPlanItem: true });
		expect(prep.plan_item).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-item-editor?plan_item=${encodeURIComponent(prep.plan_item || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui06-root",
			primaryCtaTestId: "kt-pln-ui06-save-return",
			selectSelector: `${ROOT} [data-kt-pln-field="procurement_method"]`,
			assertEditableInputs: true,
			assertHeadline: false,
			headlineSelector: "[data-kt-pln-editor-title]",
		});

		// Force AC-012 validation: alternative method without grounds.
		const method = page.locator(`${ROOT} [data-kt-pln-field="procurement_method"]`);
		await method.selectOption("Restricted tender");
		await page.locator(`${ROOT} [data-kt-pln-field="method_override_grounds"]`).fill("");
		await page.locator(`${ROOT} [data-kt-pln-field="method_override_reason"]`).fill("");
		await page.locator(`${ROOT} [data-kt-pln-field="method_override_evidence"]`).fill("");
		await page.getByTestId("kt-pln-ui06-save-draft").click();

		const inlineError = page.locator(
			`${ROOT} [data-kt-field-error="method_override_grounds"]:not([hidden])`,
		);
		await expect(inlineError).toBeVisible({ timeout: 15_000 });
		await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.locator("body")).not.toContainText("Value missing for");
		await expect(page.getByTestId("kt-pln-ui06-add-another")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui06-source-allocation")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui06-source-demand")).toBeVisible();
		await expect(page.locator(ROOT)).toContainText("Planning approach");
		await expect(page.locator(ROOT)).toContainText("Planned schedule");
		await expect(page.locator(ROOT)).toContainText("Statutory and strategy treatment");
		await expect(page.locator(ROOT)).toContainText("Source Demand");
		await expect(page.locator(ROOT)).not.toContainText("Combine in this Plan Item");
		await expect(page.locator(ROOT)).not.toContainText("Keep separate");
		await expect(page.locator(`${ROOT} [name="aggregation_decision"]`)).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui06-package-structure")).toHaveCount(0);
	});
});
