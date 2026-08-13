import { test, expect } from "@playwright/test";
import {
	loginAsAdministrator,
	loginAsDemandRequester,
} from "../../helpers/auth";
import {
	loginAsMohPlanApprover,
	loginAsMohPlanningOfficer,
	loginAsMohPlanningReviewer,
	loginAsMohPlanningViewer,
	loginAsPlanningSystemAdminNoScope,
	preparePlanningGate05Approval,
} from "../../helpers/planningRoles";

const ROOT = '[data-testid="kt-pln-ui08-root"]';

async function openReview(page: import("@playwright/test").Page, plan: string) {
	await page.goto(`/desk/procurement-plan-review?plan=${encodeURIComponent(plan)}`, {
		waitUntil: "domcontentloaded",
	});
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 45_000 });
}

async function expectNoTaskCtas(page: import("@playwright/test").Page) {
	await expect(page.getByTestId("kt-pln-ui08-primary")).toBeHidden({ timeout: 30_000 });
	await expect(page.getByTestId("kt-pln-ui08-return")).toBeHidden();
	await expect(page.locator('[data-testid="kt-pln-ui08-primary"][disabled]')).toHaveCount(0);
}

test.describe("PLN-GATE-C01 Planning task route denial", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Requester: no Approve/Return CTAs on review route", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsDemandRequester(page);
		await openReview(page, prep.empty_draft_plan || "");
		await expect(
			page.locator(`${ROOT}[data-kt-pln-error="1"], ${ROOT}[data-kt-pln-surface="denied"]`),
		).toBeVisible({ timeout: 30_000 });
		await expectNoTaskCtas(page);
	});

	test("Viewer: neutral surface — no professional Approve/Return", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningViewer(page);
		await openReview(page, prep.empty_draft_plan || "");
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-task", "0", {
			timeout: 30_000,
		});
		await expectNoTaskCtas(page);
	});

	test("Planner: no professional Approve CTA", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await openReview(page, prep.empty_draft_plan || "");
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-task", "0", {
			timeout: 30_000,
		});
		await expectNoTaskCtas(page);
	});

	test("Reviewer: Recommend approval, not Approve plan", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningReviewer(page);
		await openReview(page, prep.empty_draft_plan || "");
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-task", "1", {
			timeout: 30_000,
		});
		const primary = page.getByTestId("kt-pln-ui08-primary");
		await expect(primary).toBeVisible();
		await expect(primary).toContainText(/Recommend approval/i);
		await expect(primary).not.toContainText(/Approve plan/i);
		await expect(page.getByTestId("kt-pln-ui08-return")).toBeVisible();
	});

	test("Approver: task CTAs present", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanApprover(page);
		await openReview(page, prep.empty_draft_plan || "");
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-task", "1", {
			timeout: 30_000,
		});
		const primary = page.getByTestId("kt-pln-ui08-primary");
		await expect(primary).toBeVisible();
		await expect(primary).toContainText(/Approve plan/i);
		await expect(primary).toBeEnabled();
	});

	test("Admin without Planning USA: review task denied", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsPlanningSystemAdminNoScope(page);
		await openReview(page, prep.empty_draft_plan || "");
		await expectNoTaskCtas(page);
		await expect(
			page.locator(`${ROOT}[data-kt-pln-error="1"], ${ROOT}[data-kt-pln-surface="denied"]`),
		).toBeVisible({ timeout: 30_000 });
	});
});
