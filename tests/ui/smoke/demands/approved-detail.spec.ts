import { test, expect } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";

/**
 * DEM-UI-09 / 09A–D — Approved Demand detail tabs.
 * Route: /desk/demand-detail/<name>
 */

const ROOT = '[data-testid="kt-dem-ui09-root"]';
const DEFAULT_SEED_PASSWORD = "Test@123";

async function prepareApprovedDetail(page: import("@playwright/test").Page): Promise<{
	demand: string;
	procurementApprover: string;
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
							status?: string;
							planning_usage?: string;
						};
					}>;
				};
			}
		).frappe.call({
			method: "kentender_procurement.demands.api.prepare_approved_detail_ui09",
		});
		return {
			demand: r.message?.demand || "",
			procurementApprover: r.message?.procurement_approver || "",
			status: r.message?.status || "",
			planningUsage: r.message?.planning_usage || "",
		};
	});
	expect(prepared.demand).toBeTruthy();
	expect(prepared.procurementApprover).toBeTruthy();
	expect(prepared.status).toBe("Approved");
	expect(prepared.planningUsage).toBe("Fully planned");
	return {
		demand: prepared.demand,
		procurementApprover: prepared.procurementApprover,
	};
}

test.describe("DEM-UI-09 Approved Demand detail", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Overview + tabs, lock banner, no edit controls, Cancel hidden when Fully planned", async ({
		page,
	}) => {
		const { demand, procurementApprover } = await prepareApprovedDetail(page);
		await page.context().clearCookies();
		await login(
			page,
			procurementApprover,
			process.env.UI_PROCUREMENT_APPROVER_PASSWORD ||
				process.env.UI_PAA_PASSWORD ||
				DEFAULT_SEED_PASSWORD,
		);
		await page.goto(`/desk/demand-detail/${demand}`, {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByTestId("kt-dem-ui09-header")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui09-lock")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui09-lock")).toContainText(/locked/i);
		await expect(page.getByTestId("kt-dem-ui09-tabs")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui09-overview")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui09-position")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui09-print")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui09-cancel")).toBeHidden();

		const estimate = page.locator('[data-kt-dem-label="detail_estimate"]');
		await expect(estimate).toContainText(/KES/);
		await expect(estimate).toContainText(/,/);

		// No stage stepper / enrichment edit chrome.
		await expect(page.getByTestId("kt-dem-stage")).toHaveCount(0);
		await expect(page.locator('input[type="text"]')).toHaveCount(0);
		await expect(page.locator('select[data-kt-dem-field]')).toHaveCount(0);

		await page.getByTestId("kt-dem-ui09-tab-scope").click();
		await expect(page.getByTestId("kt-dem-ui09a-scope")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui09-overview")).toBeHidden();
		await expect(page.getByTestId("kt-dem-ui09a-items")).toBeVisible();
		await expect(page.locator('[data-kt-dem-label="sc_total"]')).toContainText(/KES/);
		// Desk lock: thead primary-fixed #d7e2ff (not Stitch muted #f4f3f9).
		const theadBg = await page
			.getByTestId("kt-dem-ui09a-items")
			.locator("th")
			.first()
			.evaluate((el) => getComputedStyle(el).backgroundColor);
		expect(theadBg).toBe("rgb(215, 226, 255)");

		await page.getByTestId("kt-dem-ui09-tab-strategy").click();
		await expect(page.getByTestId("kt-dem-ui09b-strategy")).toBeVisible();
		await expect(page.locator('[data-kt-dem-label="st_confirmed"]')).toContainText(
			/Confirmed at approval/i,
		);

		await page.getByTestId("kt-dem-ui09-tab-funding").click();
		await expect(page.getByTestId("kt-dem-ui09c-funding")).toBeVisible();
		const line = page.locator('[data-kt-dem-label="fu_line"]');
		await expect(line).not.toHaveText(/^—$/);
		await expect(line).not.toHaveText(/^[a-f0-9]{10,}$/i);
		await expect(page.locator('[data-kt-dem-label="fu_alloc"]')).toContainText(/KES/);

		await page.getByTestId("kt-dem-ui09-tab-lifecycle").click();
		await expect(page.getByTestId("kt-dem-ui09d-lifecycle")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui09d-downstream")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui09d-decisions")).toBeVisible();
		await page.getByTestId("kt-dem-ui09-view-audit").click();
		await expect(page.getByTestId("kt-dem-ui09-audit-modal")).toBeVisible();
		await page
			.getByTestId("kt-dem-ui09-audit-modal")
			.getByRole("button", { name: "Close" })
			.click();
		await expect(page.getByTestId("kt-dem-ui09-audit-modal")).toBeHidden();

		// Control summary link switches tabs.
		await page.getByTestId("kt-dem-ui09-tab-overview").click();
		await page.getByTestId("kt-dem-ui09-goto-scope").click();
		await expect(page.getByTestId("kt-dem-ui09a-scope")).toBeVisible();
	});
});
