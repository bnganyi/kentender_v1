import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

/**
 * Cross-module Stitch Desk chrome contract.
 * Mirrors kentender_core.stitch_desk_chrome_registry — keep in sync when adding surfaces.
 */

const SURFACES = [
	{
		id: "budget-portfolio",
		route: "/desk/budget-funding",
		rootTestId: "kt-bud-portfolio",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-register-budget",
		secondaryCtaTestId: "kt-bud-open-performance",
		selectSelector: '[data-kt-bud-filter="status"]',
	},
	{
		id: "budget-register",
		route: "/desk/budget-register",
		rootTestId: "kt-bud-register",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-create-draft",
		secondaryCtaTestId: "kt-bud-register-cancel",
		selectSelector: '[data-kt-bud-field="fiscal_period"]',
	},
	{
		id: "strategy-portfolio",
		route: "/desk/strategy-alignment",
		rootTestId: "kt-str-portfolio",
		liveAttr: "data-kt-str-live",
		primaryCtaTestId: "kt-str-create-plan",
		selectSelector: '[data-testid="kt-str-pf-filters"] select',
	},
	{
		id: "budget-overview",
		route: "/desk/budget-overview/MOH-BUD-0001",
		rootTestId: "kt-bud-overview",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-overview-primary",
		secondaryCtaTestId: "kt-bud-view-performance",
	},
	{
		id: "budget-lines",
		route: "/desk/budget-lines/MOH-BUD-0001",
		rootTestId: "kt-bud-lines",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-overview-primary",
		secondaryCtaTestId: "kt-bud-view-performance",
	},
	{
		id: "budget-funding-activity",
		route: "/desk/budget-funding-activity/MOH-BUD-0001",
		rootTestId: "kt-bud-activity",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-overview-primary",
		secondaryCtaTestId: "kt-bud-view-performance",
		selectSelector: '[data-kt-bud-activity-filter="activity_type"]',
	},
] as const;

test.describe.configure({ mode: "serial" });

test.describe("Stitch Desk chrome baseline", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
		await loginAsAdministrator(page);
	});

	for (const surface of SURFACES) {
		test(`${surface.id} resists Desk button/select bleed`, async ({ page }) => {
			await page.goto(surface.route, { waitUntil: "domcontentloaded" });
			const root = page.locator(
				`[data-testid="${surface.rootTestId}"][${surface.liveAttr}="1"]`,
			);
			await expect(root).toBeVisible({ timeout: 45_000 });
			await assertStitchDeskChrome(page, {
				rootTestId: surface.rootTestId,
				primaryCtaTestId: surface.primaryCtaTestId,
				secondaryCtaTestId:
					"secondaryCtaTestId" in surface ? surface.secondaryCtaTestId : undefined,
				selectSelector:
					"selectSelector" in surface ? surface.selectSelector : undefined,
				headlineSelector:
					surface.id === "budget-overview" ||
					surface.id === "budget-lines" ||
					surface.id === "budget-funding-activity"
						? "[data-kt-bud-budget-title]"
						: undefined,
			});
		});
	}

	test("Material expand_more selects never stack SVG Forms chevron", async ({ page }) => {
		// Downstream filter bar is the chronic double-chevron surface (SVG + Material).
		await page.goto("/desk/strategy-plan-downstream-usage/MOH-SP-0001", {
			waitUntil: "domcontentloaded",
		});
		const down = page.locator('[data-testid="kt-str-downstream"]');
		await expect(down).toBeVisible({ timeout: 45_000 });
		const filters = down.locator("[data-kt-str-down-filters]");
		await expect(filters).toBeVisible();
		await expect(
			filters.locator(".material-symbols-outlined", { hasText: "expand_more" }),
		).toHaveCount(4);
		const rows = await filters.locator("select").evaluateAll((sels) =>
			sels.map((sel) => {
				const cs = getComputedStyle(sel);
				const sib = sel.nextElementSibling;
				const material =
					!!sib &&
					sib.classList.contains("material-symbols-outlined") &&
					(sib.textContent || "").trim() === "expand_more";
				return { bgImage: cs.backgroundImage, material };
			}),
		);
		expect(rows.length).toBeGreaterThanOrEqual(4);
		for (const row of rows) {
			expect(row.material, "filter select needs Material expand_more sibling").toBeTruthy();
			expect(
				row.bgImage === "none" || row.bgImage === "",
				"SVG Forms chevron must be suppressed when Material sibling owns glyph",
			).toBeTruthy();
		}
	});
});
