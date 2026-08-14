import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohBudgetOfficer,
	loginAsMohPlanApprover,
	loginAsMohPlanningOfficer,
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
		await expect(
			page.getByRole("heading", { name: /Review and approve procurement plan/i }),
		).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-summary")).toBeVisible();
		await expect(page.getByText("Finance Confirmed", { exact: true })).toBeVisible();
		await expect(page.locator(`${ROOT} th`, { hasText: "Finance" })).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-statutory")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui08-rail")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-trail")).toBeVisible();
		await expect(page.getByText("Professional approval")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-primary")).toContainText(/Recommend approval/i);
		await expect(page.getByTestId("kt-pln-ui08-return")).toContainText(/Return to planner/i);
		await expect(page.getByText("Statutory allocation coverage")).toHaveCount(0);
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

	test("Planner cannot act on the professional review task", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-review?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 45_000 });
		await expect(
			page.getByRole("heading", { name: /Review and approve procurement plan/i }),
		).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui08-primary")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui08-return")).toBeHidden();
	});

	test("Budget Officer has no Recommend or Approve controls", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohBudgetOfficer(page);
		await page.goto(
			`/desk/procurement-plan-review?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-pln-ui08-primary")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui08-return")).toBeHidden();
		await expect(page.getByRole("button", { name: /Recommend approval/i })).toHaveCount(0);
		await expect(page.getByRole("button", { name: /Approve plan/i })).toHaveCount(0);
	});

	test("Review subtitle binds the live plan title and In review version", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningReviewer(page);
		await page.goto(
			`/desk/procurement-plan-review?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 45_000 });
		const title = await page.evaluate(async (plan: string) => {
			const r = await (
				window as unknown as {
					frappe: {
						call: (o: {
							method: string;
							args: { plan: string };
						}) => Promise<{ message?: { title?: string } }>;
					};
				}
			).frappe.call({
				method:
					"kentender_procurement.procurement_planning.api.get_plan_review",
				args: { plan },
			});
			return r.message?.title || "";
		}, prep.empty_draft_plan || "");
		expect(title).toBeTruthy();
		expect(title).not.toBe("Annual Procurement Plan");
		await expect(page.locator("[data-kt-pln-review-secondary]")).toContainText(title);
		await expect(page.locator("[data-kt-pln-review-secondary]")).toContainText(
			/In review Version/i,
		);
		await expect(page.locator("[data-kt-pln-review-secondary]")).not.toHaveText(
			/^Version 1$/,
		);
	});
});
