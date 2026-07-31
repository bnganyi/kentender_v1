/**
 * Budget Hub — Stitch layout contract (docs/misc/budget_home_code.html).
 *
 * Main column (header → KPIs → guardrails host → envelopes → analytics)
 * + right rail (Recent Movements → Strategic Alignment).
 * Fake Stitch left nav / mobile bottom nav must not appear.
 */
import { expect, test } from "@playwright/test";

import { loginAsAdministrator } from "../../helpers/auth";

test.describe("Budget Hub — Stitch layout (misc design)", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 900 });
		await loginAsAdministrator(page);
	});

	test("canvas is main + aside; section order and Stitch table headers", async ({ page }) => {
		test.setTimeout(120_000);
		await page.goto("/desk/budget-hub", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("kt-bgt-workbench")).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId("kt-bgt-canvas")).toBeVisible();
		await expect(page.getByTestId("kt-bgt-main")).toBeVisible();
		await expect(page.getByTestId("kt-bgt-aside")).toBeVisible();

		await expect.poll(async () => page.title()).toMatch(/KenTender\s*\|\s*Budget Hub/);

		// No Stitch fake chrome left over from the HTML mock.
		const workbench = page.getByTestId("kt-bgt-workbench");
		await expect(workbench).not.toContainText("Financial Catalyst");
		await expect(workbench).not.toContainText("New Request");

		const order = await page.evaluate(() => {
			const main = document.querySelector('[data-testid="kt-bgt-main"]');
			const aside = document.querySelector('[data-testid="kt-bgt-aside"]');
			if (!main || !aside) return null;
			const mainIds = [
				".kt-bgt-page-hdr",
				"[data-testid='kt-bgt-kpis']",
				"[data-testid='kt-bgt-guardrails-section']",
				"[data-testid='kt-bgt-envelopes']",
				".kt-bgt-analytics-grid",
			];
			const mainTops = mainIds
				.map((sel) => {
					const el = main.querySelector(sel) as HTMLElement | null;
					if (!el) return null;
					const style = window.getComputedStyle(el);
					if (style.display === "none" || style.visibility === "hidden") return null;
					return Math.round(el.getBoundingClientRect().top);
				})
				.filter((t): t is number => t !== null);
			const mov = aside.querySelector(".kt-bgt-movements-panel") as HTMLElement | null;
			const align = aside.querySelector(".kt-bgt-alignment-card") as HTMLElement | null;
			return {
				mainTops,
				movTop: mov ? Math.round(mov.getBoundingClientRect().top) : -1,
				alignTop: align ? Math.round(align.getBoundingClientRect().top) : -1,
			};
		});
		expect(order).not.toBeNull();
		expect(order!.mainTops.length).toBeGreaterThanOrEqual(4);
		for (let i = 1; i < order!.mainTops.length; i++) {
			expect(order!.mainTops[i]).toBeGreaterThanOrEqual(order!.mainTops[i - 1]);
		}
		expect(order!.movTop).toBeGreaterThanOrEqual(0);
		expect(order!.alignTop).toBeGreaterThan(order!.movTop);

		const headers = await page.locator(".kt-bgt-table thead th").allTextContents();
		expect(headers.map((h) => h.trim())).toEqual([
			"Entity / Budget Name",
			"Consumption",
			"Available (KES)",
			"Status",
			"Actions",
		]);

		// Procurement rail remains (not Stitch fake aside).
		await expect(page.locator(".body-sidebar .sidebar-header .header-title")).toHaveText(
			/^\s*Procurement\s*$/i,
		);

		// Desktop: right rail sits beside main (not stacked under it).
		const sideBySide = await page.evaluate(() => {
			const main = document.querySelector('[data-testid="kt-bgt-main"]') as HTMLElement;
			const aside = document.querySelector('[data-testid="kt-bgt-aside"]') as HTMLElement;
			const mr = main.getBoundingClientRect();
			const ar = aside.getBoundingClientRect();
			return ar.left >= mr.right - 8 && Math.abs(ar.top - mr.top) < 80;
		});
		expect(sideBySide).toBe(true);

		// Stitch subtleties: Filter by always visible; KPI label-caps 12px;
		// continuous timeline rail when movements exist.
		await expect(page.getByTestId("kt-bgt-entity-filter-wrap")).toBeVisible();
		const polish = await page.evaluate(() => {
			const label = document.querySelector(".kt-bgt-kpi-label") as HTMLElement | null;
			const th = document.querySelector(".kt-bgt-table thead th") as HTMLElement | null;
			const tl = document.querySelector('[data-testid="kt-bgt-timeline"]') as HTMLElement | null;
			const hasItem = !!document.querySelector(".kt-bgt-tl-item");
			const rail = tl ? getComputedStyle(tl, "::before") : null;
			return {
				kpiLabelSize: label ? getComputedStyle(label).fontSize : null,
				thFontSize: th ? getComputedStyle(th).fontSize : null,
				thPadLeft: th ? getComputedStyle(th).paddingLeft : null,
				timelineRail:
					hasItem && rail
						? rail.content !== "none" && parseFloat(rail.width || "0") >= 1
						: null,
			};
		});
		expect(polish.kpiLabelSize).toBe("12px");
		expect(polish.thFontSize).toBe("12px");
		expect(polish.thPadLeft).toBe("24px");
		if (polish.timelineRail !== null) {
			expect(polish.timelineRail).toBe(true);
		}
	});
});
