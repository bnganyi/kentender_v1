import { test, expect } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";

/**
 * DEM-UI-08 — Final Approval on shared demand-review.
 * Route: /desk/demand-review/<name>
 */

const ROOT = '[data-testid="kt-dem-ui04-root"]';
const DEFAULT_SEED_PASSWORD = "Test@123";

async function prepareFinalApprovalDemand(
	page: import("@playwright/test").Page,
): Promise<{
	demand: string;
	procurementApprover: string;
	budgetOfficer: string;
}> {
	await loginAsAdministrator(page);
	await page.goto("/desk", { waitUntil: "domcontentloaded" });
	const prepared = await page.evaluate(async () => {
		const r = await (
			window as unknown as {
				frappe: {
					call: (o: { method: string }) => Promise<{
						message?: {
							demand?: string;
							ok?: boolean;
							procurement_approver?: string;
							budget_officer?: string;
							current_stage?: string;
						};
					}>;
				};
			}
		).frappe.call({
			method: "kentender_procurement.demands.api.prepare_final_approval_ui08",
		});
		return {
			demand: r.message?.demand || "",
			procurementApprover: r.message?.procurement_approver || "",
			budgetOfficer: r.message?.budget_officer || "",
			stage: r.message?.current_stage || "",
		};
	});
	expect(prepared.demand).toBeTruthy();
	expect(prepared.procurementApprover).toBeTruthy();
	expect(prepared.stage).toBe("Final Approval");
	return {
		demand: prepared.demand,
		procurementApprover: prepared.procurementApprover,
		budgetOfficer: prepared.budgetOfficer,
	};
}

test.describe("DEM-UI-08 Final Approval", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Stitch regions, checkbox gates Approve, approve → workspace", async ({
		page,
	}) => {
		const { demand, procurementApprover } = await prepareFinalApprovalDemand(page);
		await page.context().clearCookies();
		await login(
			page,
			procurementApprover,
			process.env.UI_PROCUREMENT_APPROVER_PASSWORD ||
				process.env.UI_PAA_PASSWORD ||
				DEFAULT_SEED_PASSWORD,
		);
		await page.goto(`/desk/demand-review/${demand}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator(ROOT)).toHaveAttribute(
			"data-kt-dem-review-stage",
			"Final Approval",
		);
		await expect(page.getByTestId("kt-dem-record-header")).toBeVisible();
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Final approval/i);
		await expect(page.getByTestId("kt-dem-stage")).toContainText(/Current/i);
		await expect(page.getByTestId("kt-dem-business-host")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui05-root")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui06-root")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui08-root")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui08-readiness")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui08-demand-summary")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui08-strategy")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui08-funding")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui08-planning")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui08-decision")).toBeVisible();

		const estimate = page.locator('[data-kt-dem-label="fa_estimate_display"]');
		await expect(estimate).toContainText(/KES/);
		await expect(estimate).toContainText(/,/);

		const budgetLine = page.locator('[data-kt-dem-label="fa_budget_line_display"]');
		await expect(budgetLine).not.toHaveText(/^—$/);
		await expect(budgetLine).not.toHaveText(/^[a-f0-9]{10,}$/i);

		// Enrichment / budget confirm hosts stay in DOM but must not be visible.
		await expect(page.getByTestId("kt-dem-ui05-root")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui06-root")).toBeHidden();
		await expect(
			page.locator('select[data-kt-dem-field="procurement_category"]'),
		).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui06-confirm")).toBeHidden();

		const approve = page.getByTestId("kt-dem-ui08-approve");
		await expect(approve).toBeDisabled();
		await page.getByTestId("kt-dem-ui08-approve-checkbox").check();
		await expect(approve).toBeEnabled();
		// Checked mark must be visible (Desk focus must not force white fill over navy).
		const checkChrome = await page
			.getByTestId("kt-dem-ui08-approve-checkbox")
			.evaluate((el) => {
				const input = el as HTMLInputElement;
				const mark = input.nextElementSibling as HTMLElement | null;
				const ics = getComputedStyle(input);
				const mcs = mark ? getComputedStyle(mark) : null;
				return {
					checked: input.checked,
					bg: ics.backgroundColor,
					markOpacity: mcs?.opacity || "",
					markColor: mcs?.color || "",
				};
			});
		expect(checkChrome.checked).toBe(true);
		expect(checkChrome.bg).toMatch(/rgb\(0,\s*31,\s*72\)/);
		expect(parseFloat(checkChrome.markOpacity || "0")).toBeGreaterThanOrEqual(1);
		expect(checkChrome.markColor).toMatch(/rgb\(255,\s*255,\s*255\)/);

		await approve.click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 30_000 });
	});

	test("Budget Officer cannot Approve; Return invalidates BO sign-off path opens modal", async ({
		page,
	}) => {
		const { demand, budgetOfficer, procurementApprover } =
			await prepareFinalApprovalDemand(page);

		await page.context().clearCookies();
		await login(
			page,
			budgetOfficer,
			process.env.UI_BUDGET_OFFICER_PASSWORD || DEFAULT_SEED_PASSWORD,
		);
		await page.goto(`/desk/demand-review/${demand}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByTestId("kt-dem-ui08-root")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui08-approve")).toBeDisabled();
		await expect(page.getByTestId("kt-dem-ui08-approve-checkbox")).toBeDisabled();
		await expect(page.getByTestId("kt-dem-ui08-return")).toBeDisabled();
		await expect(page.getByTestId("kt-dem-ui08-reject")).toBeDisabled();

		await page.context().clearCookies();
		await login(
			page,
			procurementApprover,
			process.env.UI_PROCUREMENT_APPROVER_PASSWORD ||
				process.env.UI_PAA_PASSWORD ||
				DEFAULT_SEED_PASSWORD,
		);
		await page.goto(`/desk/demand-review/${demand}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await page.getByTestId("kt-dem-ui08-return").click();
		await expect(page.locator("[data-kt-dem-reason-modal]")).toBeVisible();
		await page.locator("[data-kt-dem-reason-comment]").fill(
			"Return to Budget Confirmation — funding line needs recheck",
		);
		await page.locator("[data-kt-dem-reason-confirm]").click();
		await expect(page).toHaveURL(/demands-workspace/, { timeout: 30_000 });
	});
});
