import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

/**
 * Officer Bid Submissions Desk (docs/bids screens 1–2 smoke).
 * Route: /desk/bid-submissions
 */

test.describe("Officer Bid Submissions", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
	});

	test("landing root and filters render", async ({ page }) => {
		await page.goto("/desk/bid-submissions");
		await expect(page.getByTestId("kt-bid-submissions-root")).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByTestId("kt-bs-landing")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-bs-search")).toBeVisible();
		await expect(page.getByTestId("kt-bs-stage-filter")).toBeVisible();
		const row = page.getByTestId("kt-bs-landing-row").first();
		const empty = page.getByTestId("kt-bs-empty-landing");
		await expect(row.or(empty)).toBeVisible({ timeout: 20_000 });
	});

	test("landing action navigates to tender detail view", async ({ page }) => {
		await page.goto("/desk/bid-submissions");
		await expect(page.getByTestId("kt-bs-landing")).toBeVisible({ timeout: 30_000 });
		const action = page.locator("[data-action='open-row']").first();
		await expect(action).toBeVisible({ timeout: 20_000 });
		const pubId = await action.getAttribute("data-publication-id");
		expect(pubId).toBeTruthy();
		await action.click();
		await expect(page).toHaveURL(new RegExp(`/desk/bid-submissions/${pubId}`), {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-bs-landing")).toHaveCount(0, { timeout: 15_000 });
		const detail = page
			.getByTestId("kt-bs-receiving")
			.or(page.getByTestId("kt-bs-sealed"))
			.or(page.getByTestId("kt-bs-register"));
		await expect(detail).toBeVisible({ timeout: 20_000 });
	});

	test("closed-and-sealed landing rows omit bid counts", async ({ page }) => {
		await page.goto("/desk/bid-submissions");
		await expect(page.getByTestId("kt-bs-landing")).toBeVisible({ timeout: 30_000 });

		const listed = await page.evaluate(async () => {
			return await new Promise<{ rows?: Array<Record<string, unknown>> }>((resolve, reject) => {
				// @ts-expect-error frappe in desk
				frappe.call({
					method: "kentender_procurement.tender_configurations.list_bid_submission_tenders",
					args: { stage: "Closed and sealed", page: 1, page_size: 20 },
					callback: (r: { message?: { rows?: Array<Record<string, unknown>> }; exc?: string }) => {
						if (r.exc) {
							reject(new Error(String(r.exc)));
							return;
						}
						resolve(r.message || { rows: [] });
					},
				});
			});
		});

		const sealedRows = listed.rows || [];
		for (const row of sealedRows) {
			expect(row).not.toHaveProperty("active_bids_opened");
			const blob = JSON.stringify(row).toLowerCase();
			expect(blob).not.toContain("bidder_legal");
			expect(blob).not.toContain("receipt_code");
		}

		if (sealedRows.length) {
			const pubId = String(sealedRows[0].publication_id || "");
			await page.goto(`/desk/bid-submissions/${pubId}`);
			await expect(page.getByTestId("kt-bs-sealed")).toBeVisible({ timeout: 30_000 });
			await expect(page.getByTestId("kt-bs-vault")).toBeVisible();
			const vault = (await page.getByTestId("kt-bs-vault").innerText()).toLowerCase();
			expect(vault).toContain("sealed");
			expect(vault).not.toMatch(/\d+\s+bids?/);
		}
	});
});
