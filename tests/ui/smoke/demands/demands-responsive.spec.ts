import { test, expect } from "@playwright/test";
import {
	loginAsAdministrator,
	loginAsBusinessApprover,
	loginAsDemandRequester,
} from "../../helpers/auth";

/**
 * DEM-NFR-004 — tablet layouts usable without page-level horizontal scroll.
 */

async function assertNoPageHorizontalScroll(page: import("@playwright/test").Page) {
	const metrics = await page.evaluate(() => {
		const doc = document.documentElement;
		const body = document.body;
		return {
			scrollWidth: Math.max(doc.scrollWidth, body.scrollWidth),
			clientWidth: doc.clientWidth,
		};
	});
	expect(
		metrics.scrollWidth,
		`page H-scroll: scrollWidth=${metrics.scrollWidth} clientWidth=${metrics.clientWidth}`,
	).toBeLessThanOrEqual(metrics.clientWidth + 1);
}

test.describe("DEM-NFR-004 Demands responsive", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1024, height: 768 });
	});

	test("Workspace at tablet has no page H-scroll", async ({ page }) => {
		await loginAsDemandRequester(page);
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-dem-ui01-root"][data-kt-dem-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await assertNoPageHorizontalScroll(page);
		await expect(page.getByTestId("kt-dem-ui01-create")).toBeVisible();
	});

	test("Form at tablet has no page H-scroll", async ({ page }) => {
		await loginAsDemandRequester(page);
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-dem-ui02-root"][data-kt-dem-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await assertNoPageHorizontalScroll(page);
	});

	test("Review at tablet has no page H-scroll", async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const demandName = await page.evaluate(async () => {
			const r = await (
				window as unknown as {
					frappe: {
						call: (o: { method: string }) => Promise<{ message?: { demand?: string } }>;
					};
				}
			).frappe.call({
				method: "kentender_procurement.demands.api.prepare_business_review_ui04",
			});
			return r.message?.demand || "";
		});
		expect(demandName).toBeTruthy();
		await page.context().clearCookies();
		await loginAsBusinessApprover(page);
		await page.goto(`/desk/demand-review/${demandName}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-dem-ui04-root"][data-kt-dem-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await assertNoPageHorizontalScroll(page);
	});

	test("Approved detail at tablet has no page H-scroll", async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		const demandName = await page.evaluate(async () => {
			const r = await (
				window as unknown as {
					frappe: {
						call: (o: { method: string }) => Promise<{ message?: { demand?: string } }>;
					};
				}
			).frappe.call({
				method: "kentender_procurement.demands.api.prepare_approved_detail_ui09",
			});
			return r.message?.demand || "";
		});
		expect(demandName).toBeTruthy();
		await page.goto(`/desk/demand-detail/${demandName}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-dem-ui09-root"][data-kt-dem-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await assertNoPageHorizontalScroll(page);
	});
});
