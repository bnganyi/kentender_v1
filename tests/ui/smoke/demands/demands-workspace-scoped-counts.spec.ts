import { test, expect } from "@playwright/test";
import { loginAsDemandRequester } from "../../helpers/auth";

/**
 * DEM-AC-022 — workspace summary counts match scoped source rows.
 */

const ROOT = '[data-testid="kt-dem-ui01-root"]';

test.describe("DEM-AC-022 Workspace scoped counts", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsDemandRequester(page);
	});

	test("Summary chip totals equal scoped queue totals from same API", async ({ page }) => {
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-dem-live="1"]`)).toBeVisible({ timeout: 30_000 });

		const consistency = await page.evaluate(async () => {
			const frappe = (
				window as unknown as {
					frappe: {
						call: (o: {
							method: string;
							args?: Record<string, unknown>;
						}) => Promise<{ message?: Record<string, unknown> }>;
					};
				}
			).frappe;
			const all = await frappe.call({
				method: "kentender_procurement.demands.api.list_demands_workspace",
				args: { page: 1, page_size: 500 },
			});
			const summary = (all.message?.summary || {}) as Record<string, number>;
			const drafts = await frappe.call({
				method: "kentender_procurement.demands.api.list_demands_workspace",
				args: { queue: "my_drafts", page: 1, page_size: 500 },
			});
			const returned = await frappe.call({
				method: "kentender_procurement.demands.api.list_demands_workspace",
				args: { queue: "returned_to_me", page: 1, page_size: 500 },
			});
			const codes = ((all.message?.rows as Array<{ demand_code?: string }>) || []).map(
				(r) => r.demand_code || "",
			);
			return {
				summary,
				draftTotal: Number(drafts.message?.total || 0),
				returnedTotal: Number(returned.message?.total || 0),
				codes,
			};
		});

		expect(consistency.draftTotal).toBe(consistency.summary.my_drafts);
		expect(consistency.returnedTotal).toBe(consistency.summary.returned_to_me);
		expect(consistency.codes).not.toContain("DMD-CGK-2027-006");

		const chipDraft = page.getByTestId("kt-dem-ui01-queue-my_drafts");
		await expect(chipDraft).toBeVisible();
		await expect(chipDraft).toContainText(String(consistency.summary.my_drafts));
	});
});
