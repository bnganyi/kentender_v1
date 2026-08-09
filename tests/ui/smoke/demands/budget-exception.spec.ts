import { test, expect } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";

/**
 * DEM-UI-07 — Budget Confirmation exception variation (Insufficient Funding).
 * Route: /desk/demand-review/<name>
 */

const ROOT = '[data-testid="kt-dem-ui04-root"]';
const DEFAULT_SEED_PASSWORD = "Test@123";

async function prepareExceptionDemand(page: import("@playwright/test").Page): Promise<{
	demand: string;
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
							budget_officer?: string;
							current_stage?: string;
							exception_type?: string;
						};
					}>;
				};
			}
		).frappe.call({
			method: "kentender_procurement.demands.api.prepare_budget_exception_ui07",
		});
		return {
			demand: r.message?.demand || "",
			budgetOfficer: r.message?.budget_officer || "",
			stage: r.message?.current_stage || "",
			exceptionType: r.message?.exception_type || "",
		};
	});
	expect(prepared.demand).toBeTruthy();
	expect(prepared.budgetOfficer).toBeTruthy();
	expect(prepared.stage).toBe("Budget Confirmation");
	expect(prepared.exceptionType).toBe("Insufficient Funding");
	return { demand: prepared.demand, budgetOfficer: prepared.budgetOfficer };
}

test.describe("DEM-UI-07 Budget Exception", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("exception regions, Confirm locked, Return note required, Select-another → Adjust", async ({
		page,
	}) => {
		const { demand, budgetOfficer } = await prepareExceptionDemand(page);
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
		await expect(page.locator(ROOT)).toHaveAttribute(
			"data-kt-dem-review-stage",
			"Budget Confirmation",
		);
		await expect(page.getByTestId("kt-dem-ui06-root")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-root")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-notice")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-notice")).toContainText(
			/Funding Shortfall Detected/i,
		);
		await expect(page.getByTestId("kt-dem-ui07-shortfall-tiles")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-target-allocation")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-resolution")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-actions")).toBeVisible();

		// Routine confirm chrome hidden; Confirm permanently disabled.
		await expect(page.getByTestId("kt-dem-ui06-confirm-checkbox")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui07-confirm")).toBeDisabled();
		await expect(page.getByTestId("kt-dem-ui07-return")).toBeDisabled();

		const shortfall = page.locator('[data-kt-dem-label="funding_exc_shortfall_display"]');
		await expect(shortfall).toContainText(/KES/);
		await expect(shortfall).toContainText(/,/);

		// Split / External MVP stubs stay disabled.
		await expect(
			page.getByTestId("kt-dem-ui07-res-split").locator('input[type="radio"]'),
		).toBeDisabled();
		await expect(
			page.getByTestId("kt-dem-ui07-res-external").locator('input[type="radio"]'),
		).toBeDisabled();

		// Return path requires note + resolution choice.
		await page.getByTestId("kt-dem-ui07-res-return").locator('input[type="radio"]').check();
		await expect(page.getByTestId("kt-dem-ui07-return")).toBeDisabled();
		await page
			.getByTestId("kt-dem-ui07-return-note")
			.fill("Revise participant count — shortfall exceeds available line funding.");
		await expect(page.getByTestId("kt-dem-ui07-return")).toBeEnabled();
		await expect(page.getByTestId("kt-dem-ui07-confirm")).toBeDisabled();

		// Select another reveals existing Adjust panel.
		await page
			.getByTestId("kt-dem-ui07-res-select-another")
			.locator('input[type="radio"]')
			.check();
		await expect(page.getByTestId("kt-dem-ui06-adjust-panel")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui06-adjust-line")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-confirm")).toBeDisabled();
	});

	test("save resolution note keeps exception and Confirm blocked", async ({ page }) => {
		const { demand, budgetOfficer } = await prepareExceptionDemand(page);
		await page.context().clearCookies();
		await login(
			page,
			budgetOfficer,
			process.env.UI_BUDGET_OFFICER_PASSWORD || DEFAULT_SEED_PASSWORD,
		);
		await page.goto(`/desk/demand-review/${demand}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.getByTestId("kt-dem-ui07-root")).toBeVisible({ timeout: 30_000 });
		await page
			.getByTestId("kt-dem-ui07-return-note")
			.fill("Working note — awaiting revised estimate from Procurement.");
		await page.getByTestId("kt-dem-ui07-save-note").click();
		await expect(page.getByTestId("kt-dem-ui07-root")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-confirm")).toBeDisabled();
		await expect(page.locator(ROOT)).toHaveAttribute(
			"data-kt-dem-review-stage",
			"Budget Confirmation",
		);
	});
});

async function prepareMultipleMatchesDemand(
	page: import("@playwright/test").Page,
): Promise<{ demand: string; budgetOfficer: string }> {
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
							budget_officer?: string;
							current_stage?: string;
							exception_type?: string;
							candidate_count?: number;
						};
					}>;
				};
			}
		).frappe.call({
			method:
				"kentender_procurement.demands.api.prepare_budget_exception_multiple_matches_ui07",
		});
		return {
			demand: r.message?.demand || "",
			budgetOfficer: r.message?.budget_officer || "",
			stage: r.message?.current_stage || "",
			exceptionType: r.message?.exception_type || "",
			candidateCount: r.message?.candidate_count || 0,
		};
	});
	expect(prepared.demand).toBeTruthy();
	expect(prepared.budgetOfficer).toBeTruthy();
	expect(prepared.stage).toBe("Budget Confirmation");
	expect(prepared.exceptionType).toBe("Multiple Matches");
	expect(prepared.candidateCount).toBeGreaterThanOrEqual(2);
	return { demand: prepared.demand, budgetOfficer: prepared.budgetOfficer };
}

test.describe("DEM-UI-07 Multiple Matches", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("candidates list, Confirm locked, Select-another → Adjust", async ({ page }) => {
		const { demand, budgetOfficer } = await prepareMultipleMatchesDemand(page);
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
		await expect(page.locator(ROOT)).toHaveAttribute(
			"data-kt-dem-review-stage",
			"Budget Confirmation",
		);
		await expect(page.getByTestId("kt-dem-ui07-root")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-root")).toHaveAttribute(
			"data-kt-dem-ui07-mode",
			"multiple_matches",
		);
		await expect(page.getByTestId("kt-dem-ui07-notice")).toContainText(
			/Multiple Funding Matches/i,
		);
		await expect(page.getByTestId("kt-dem-ui07-shortfall-tiles")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui07-target-allocation")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui07-candidates")).toBeVisible();
		const candidateCount = await page
			.locator("[data-kt-dem-ui07-candidates-list] .kt-dem-ui07-candidate")
			.count();
		expect(candidateCount).toBeGreaterThanOrEqual(2);
		await expect(page.getByTestId("kt-dem-ui07-confirm")).toBeDisabled();
		await expect(page.getByTestId("kt-dem-ui07-resolution")).toBeVisible();

		await page
			.getByTestId("kt-dem-ui07-res-select-another")
			.locator('input[type="radio"]')
			.check();
		await expect(page.getByTestId("kt-dem-ui06-adjust-panel")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui07-confirm")).toBeDisabled();
	});
});
