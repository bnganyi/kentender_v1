import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanApprover,
	loginAsMohPlanningOfficer,
	preparePlanningGate05Approval,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui08-root"]';

test.describe("PLN-UI-08 assigned professional decision", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("assigned professional approves the submitted update and opens UI-09", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.review_task).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanApprover(page);
		await page.goto(prep.review_route || "", { waitUntil: "domcontentloaded" });

		await expect(page.locator(ROOT)).toBeVisible({ timeout: 45_000 });
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui08-root",
			primaryCtaTestId: "kt-pln-ui08-primary",
		});
		await expect(page.getByRole("heading", { name: "Review Plan update" })).toBeVisible();
		await expect(page.getByText("Professional decision", { exact: true })).toBeVisible();
		await expect(
			page.getByTestId("kt-pln-ui08-summary").getByText("Finance", { exact: true }),
		).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-primary")).toContainText("Approve update");
		await page.getByTestId("kt-pln-ui08-primary").click();
		await expect(page).toHaveURL(/procurement-plan-approved/, { timeout: 45_000 });
		await expect(page.locator('[data-testid="kt-pln-ui09-root"][data-kt-pln-live="1"]')).toBeVisible({ timeout: 45_000 });
	});

	test("return requires a reason and resumes the ordinary UI-05 builder", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.review_task).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanApprover(page);
		await page.goto(prep.review_route || "", { waitUntil: "domcontentloaded" });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 45_000 });

		await page.getByTestId("kt-pln-ui08-return").click();
		await expect(page.locator('[data-kt-pln-review-error]')).toContainText("A return reason is required.");
		await page.locator('[data-kt-pln-review-note]').fill("Clarify the implementation schedule.");
		await page.getByTestId("kt-pln-ui08-return").click();
		await expect(page).toHaveURL(/procurement-plan-builder/, { timeout: 45_000 });
		await expect(page.locator('[data-testid="kt-pln-ui03-root"][data-kt-pln-live="1"]')).toBeVisible({ timeout: 45_000 });
		await expect(page.locator('[data-testid="kt-pln-ui03-root"]')).toHaveAttribute("data-kt-pln-builder-state", "PLN-UI-05");
	});

	test("an unassigned planner cannot read or act on the protected task", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(prep.review_route || "", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT} [role="alert"]`)).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-pln-ui08-primary")).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui08-return")).toHaveCount(0);
	});
});
