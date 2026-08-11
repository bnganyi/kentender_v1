import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanApprover,
	loginAsMohPlanningReviewer,
	preparePlanningGate05Approval,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui08-root"]';

test.describe("PLN-UI-08 Consolidated plan review and approval", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Reviewer sees Stitch regions; return requires inline comment", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		expect(prep.reviewer_user).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningReviewer(page);
		await page.goto(
			`/desk/procurement-plan-review?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 45_000 });
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui08-root",
			primaryCtaTestId: "kt-pln-ui08-primary",
		});
		await expect(page.getByRole("heading", { name: /Review annual procurement plan/i })).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-summary")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-statutory")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-rail")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-trail")).toBeVisible();
		await expect(page.getByText("Statutory allocation coverage")).toBeVisible();
		await expect(page.getByText(/approval matrix/i)).toHaveCount(0);

		await page.getByTestId("kt-pln-ui08-return").click();
		const inlineError = page.locator(
			`${ROOT} [data-kt-field-error="decision_comment"]:not(:empty)`,
		);
		await expect(inlineError).toBeVisible({ timeout: 10_000 });
		await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);
		await expect(page.locator(".msgprint")).toHaveCount(0);
	});

	test("Approver can approve recommended plan", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanApprover(page);
		await page.goto(
			`/desk/procurement-plan-review?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 45_000 });
		const primary = page.getByTestId("kt-pln-ui08-primary");
		await expect(primary).toContainText(/Approve plan/i);
		await expect(primary).toBeEnabled({ timeout: 15_000 });
		await primary.click();
		await expect(page).toHaveURL(/planning-workspace/, { timeout: 45_000 });
	});
});
