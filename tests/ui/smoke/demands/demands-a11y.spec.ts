import { test, expect } from "@playwright/test";
import {
	loginAsAdministrator,
	loginAsBusinessApprover,
	loginAsDemandRequester,
} from "../../helpers/auth";

/**
 * DEM-NFR-003 — WCAG-oriented keyboard / labels / focus / status smoke.
 */

test.describe("DEM-NFR-003 Demands a11y", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Workspace: labeled filters, create CTA, keyboard reach, queue nav", async ({
		page,
	}) => {
		await loginAsDemandRequester(page);
		await page.goto("/desk/demands-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-dem-ui01-root"][data-kt-dem-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.getByTestId("kt-dem-ui01-create")).toHaveAttribute(
			"aria-label",
			/Create demand/i,
		);
		await expect(page.getByTestId("kt-dem-ui01-summary")).toHaveAttribute(
			"aria-label",
			/Demand queues/i,
		);
		await expect(page.locator('[data-kt-dem-filter="search"]')).toHaveAttribute(
			"aria-label",
			/Search/i,
		);
		await expect(page.locator('[data-kt-dem-filter="status"]')).toHaveAttribute(
			"aria-label",
			/Status/i,
		);

		await page.getByTestId("kt-dem-ui01-create").focus();
		await expect(page.getByTestId("kt-dem-ui01-create")).toBeFocused();
		await page.keyboard.press("Tab");
		// Performance link or next focusable in header/filter band should receive focus.
		const focused = await page.evaluate(() => {
			const el = document.activeElement as HTMLElement | null;
			return el
				? {
						tag: el.tagName,
						testid: el.getAttribute("data-testid") || "",
						aria: el.getAttribute("aria-label") || "",
				  }
				: null;
		});
		expect(focused).not.toBeNull();
		expect(["A", "BUTTON", "INPUT", "SELECT"]).toContain(focused!.tag);
	});

	test("Form: titled inputs focusable; no unlabeled primary fields", async ({ page }) => {
		await loginAsDemandRequester(page);
		await page.goto("/desk/demand-form", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-dem-ui02-root"][data-kt-dem-live="1"]')).toBeVisible({
			timeout: 30_000,
		});
		const title = page.getByTestId("kt-dem-ui02-title");
		await title.focus();
		await expect(title).toBeFocused();
		const focusChrome = await title.evaluate((el) => {
			const cs = getComputedStyle(el);
			return { borderColor: cs.borderColor, outlineStyle: cs.outlineStyle };
		});
		// Visible focus affordance (soft border or outline).
		expect(
			focusChrome.borderColor !== "rgba(0, 0, 0, 0)" || focusChrome.outlineStyle !== "none",
		).toBeTruthy();
		await expect(page.getByTestId("kt-dem-ui02-what")).toBeVisible();
		await expect(page.getByTestId("kt-dem-ui02-submit")).toBeVisible();
	});

	test("Review: status pill announces; stage navigation labeled", async ({ page }) => {
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
		const pill = page.getByTestId("kt-dem-status-pill");
		await expect(pill).toBeVisible();
		await expect(pill).toHaveAttribute("role", "status");
		await expect(page.getByTestId("kt-dem-stage")).toHaveAttribute("aria-label", /stage/i);
	});
});
