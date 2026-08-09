import { test, expect } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";

/**
 * DEM-UI-10 — Demand performance.
 * Route: /desk/demand-performance
 */

const ROOT = '[data-testid="kt-dem-ui10-root"]';
const DEFAULT_SEED_PASSWORD = "Test@123";

async function preparePerformance(page: import("@playwright/test").Page): Promise<{
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
							ok?: boolean;
							procurement_approver?: string;
							approved_demand?: string;
							returned_demand?: string;
							exception_demand?: string;
						};
					}>;
				};
			}
		).frappe.call({
			method: "kentender_procurement.demands.api.prepare_demand_performance_ui10",
		});
		return {
			ok: r.message?.ok,
			procurementApprover: r.message?.procurement_approver || "",
			approved: r.message?.approved_demand || "",
			returned: r.message?.returned_demand || "",
			exception: r.message?.exception_demand || "",
		};
	});
	expect(prepared.ok).toBeTruthy();
	expect(prepared.procurementApprover).toBeTruthy();
	expect(prepared.approved).toBeTruthy();
	expect(prepared.returned).toBeTruthy();
	expect(prepared.exception).toBeTruthy();
	return { procurementApprover: prepared.procurementApprover };
}

test.describe("DEM-UI-10 Demand performance", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("strip, flow, funding, planning, strategy, methodology + Apply/Clear", async ({
		page,
	}) => {
		const { procurementApprover } = await preparePerformance(page);
		await page.context().clearCookies();
		await login(
			page,
			procurementApprover,
			process.env.UI_PROCUREMENT_APPROVER_PASSWORD ||
				process.env.UI_PAA_PASSWORD ||
				DEFAULT_SEED_PASSWORD,
		);
		await page.goto("/desk/demand-performance", {
			waitUntil: "domcontentloaded",
		});
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});

		await expect(page.getByTestId("kt-dem-ui10-header")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui10-filters")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui10-strip")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui10-flow")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui10-funding")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui10-planning")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui10-strategy")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui10-methodology")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui10-methodology")).toContainText(
			/do not prove realised/i,
		);

		const strip = page.getByTestId("kt-dem-ui10-strip");
		await expect(strip.locator('[data-kt-dem-label="strip_demands"]')).not.toHaveText("0");
		await expect(
			strip.locator('[data-kt-dem-label="strip_approved_value"]'),
		).toContainText(/KES/);
		await expect(
			strip.locator('[data-kt-dem-label="strip_approved_value"]'),
		).toContainText(/,/);

		// Desk lock: thead primary-fixed #d7e2ff
		const theadBg = await page
			.getByTestId("kt-dem-ui10-flow")
			.locator("th")
			.first()
			.evaluate((el) => getComputedStyle(el).backgroundColor);
		expect(theadBg).toBe("rgb(215, 226, 255)");

		await expect(
			page.getByTestId("kt-dem-ui10-funding").locator('[data-kt-dem-label="fund_unfunded"]'),
		).toContainText(/KES/);

		const viewExc = page.getByTestId("kt-dem-ui10-view-exception");
		if (await viewExc.isVisible()) {
			await viewExc.click();
			await expect(page).toHaveURL(/demand-review/, { timeout: 15_000 });
			await page.goto("/desk/demand-performance", {
				waitUntil: "domcontentloaded",
			});
			await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
				timeout: 45_000,
			});
		}

		await page.getByTestId("kt-dem-ui10-apply").click();
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});
		await page.getByTestId("kt-dem-ui10-clear").click();
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({
			timeout: 30_000,
		});

		// No large KPI card grid / charts.
		await expect(page.locator(".kt-dem-ui10-kpi-card")).toHaveCount(0);
		await expect(page.locator("canvas")).toHaveCount(0);
	});
});
