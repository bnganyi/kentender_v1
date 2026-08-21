import { test, expect } from "@playwright/test";
import {
	loginAsAdministrator,
	loginAsBusinessApprover,
	loginAsDemandRequester,
	loginAsDepartmentalNeedsRequester,
} from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	loginAsMohPlanningReviewer,
} from "../../helpers/planningRoles";
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
		assertPrimaryHover: true,
	},
	{
		id: "budget-register",
		route: "/desk/budget-register",
		rootTestId: "kt-bud-register",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-create-draft",
		secondaryCtaTestId: "kt-bud-register-cancel",
		selectSelector: '[data-kt-bud-field="fiscal_period"]',
		assertPrimaryHover: true,
		assertEditableInputs: true,
	},
	{
		id: "strategy-portfolio",
		route: "/desk/strategy-alignment",
		rootTestId: "kt-str-portfolio",
		liveAttr: "data-kt-str-live",
		primaryCtaTestId: "kt-str-create-plan",
		selectSelector: '[data-testid="kt-str-pf-filters"] select',
		assertPrimaryHover: true,
	},
	{
		id: "strategy-plan-create",
		route: "/desk/strategy-plan-create",
		rootTestId: "kt-str-create-plan",
		liveAttr: "data-kt-str-live",
		primaryCtaTestId: "kt-str-create-plan-submit",
		selectSelector: '[data-kt-str-field="plan_type"]',
		assertEditableInputs: true,
	},
	{
		id: "budget-overview",
		route: "/desk/budget-overview/MOH-BUD-2027-2028",
		rootTestId: "kt-bud-overview",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-overview-primary",
		secondaryCtaTestId: "kt-bud-view-performance",
		assertPrimaryHover: true,
	},
	{
		id: "budget-lines",
		route: "/desk/budget-lines/MOH-BUD-2027-2028",
		rootTestId: "kt-bud-lines",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-overview-primary",
		secondaryCtaTestId: "kt-bud-view-performance",
		assertPrimaryHover: true,
	},
	{
		id: "budget-funding-activity",
		route: "/desk/budget-funding-activity/MOH-BUD-2027-2028",
		rootTestId: "kt-bud-activity",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-overview-primary",
		secondaryCtaTestId: "kt-bud-view-performance",
		assertPrimaryHover: true,
		selectSelector: '[data-kt-bud-activity-filter="activity_type"]',
	},
	{
		id: "budget-downstream",
		route: "/desk/budget-downstream/MOH-BUD-2027-2028",
		rootTestId: "kt-bud-downstream",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-overview-primary",
		secondaryCtaTestId: "kt-bud-view-performance",
		assertPrimaryHover: true,
		selectSelector: '[data-kt-bud-downstream-filter="status"]',
	},
	{
		id: "budget-review",
		route: "/desk/budget-review/MOH-BUD-2027-2028",
		rootTestId: "kt-bud-review",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-overview-primary",
		secondaryCtaTestId: "kt-bud-view-performance",
		assertPrimaryHover: true,
	},
	{
		id: "budget-audit",
		route: "/desk/budget-audit/MOH-BUD-2027-2028",
		rootTestId: "kt-bud-audit",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-audit-export",
		primaryCtaStyle: "bordered" as const,
		selectSelector: '[data-kt-bud-audit-filter="event_type"]',
	},
	{
		id: "budget-funding-performance",
		route: "/desk/budget-funding-performance",
		rootTestId: "kt-bud-performance",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-performance-export",
		primaryCtaStyle: "bordered" as const,
		selectSelector: '[data-kt-bud-perf-filter="fiscal_period"]',
	},
	{
		id: "budget-check-reserve",
		route: "/desk/budget-check-reserve",
		rootTestId: "kt-bud-check-reserve",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-check-reserve-reserve",
		selectSelector: '[data-kt-bud-cr-filter="budget_line"]',
	},
	{
		id: "budget-revisions",
		route: "/desk/budget-revisions/MOH-BUD-2027-2028",
		rootTestId: "kt-bud-revisions",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-overview-primary",
		secondaryCtaTestId: "kt-bud-view-performance",
	},
	{
		id: "budget-revision-create",
		route: "/desk/budget-revision-create/MOH-BUD-2027-2028",
		rootTestId: "kt-bud-revision-create",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-rev-submit",
		assertEditableInputs: true,
	},
	{
		id: "budget-revision-review",
		route: "/desk/budget-revision-review/BR-MOH-0002",
		rootTestId: "kt-bud-revision-review",
		liveAttr: "data-kt-bud-live",
		primaryCtaTestId: "kt-bud-rev-review-apply",
	},
	{
		id: "demands-workspace",
		route: "/desk/demands-workspace",
		rootTestId: "kt-dem-ui01-root",
		liveAttr: "data-kt-dem-live",
		primaryCtaTestId: "kt-dem-ui01-create",
		selectSelector: '[data-kt-dem-filter="status"]',
	},
	{
		id: "demand-form",
		route: "/desk/demand-form",
		rootTestId: "kt-dem-ui02-root",
		liveAttr: "data-kt-dem-live",
		primaryCtaTestId: "kt-dem-ui02-submit",
		selectSelector: '[data-kt-dem-field="demand_route"]',
	},
	{
		id: "demand-review",
		route: "/desk/demand-review",
		rootTestId: "kt-dem-ui04-root",
		liveAttr: "data-kt-dem-live",
		primaryCtaTestId: "kt-dem-ui04-support",
	},
	{
		id: "departmental-needs-new",
		route: "/desk/departmental-needs-new",
		rootTestId: "departmental-needs-new",
		liveAttr: "data-kt-nds-live",
		primaryCtaTestId: "kt-nds-create-submit",
		assertEditableInputs: true,
	},
	{
		id: "planning-workspace",
		route: "/desk/planning-workspace",
		rootTestId: "kt-pln-ui01-root",
		liveAttr: "data-kt-pln-live",
		primaryCtaTestId: "kt-pln-ui01-primary-action",
		// PLN-UI-01.html uses Tailwind `rounded` (4px) for this CTA.
		primaryRadiusMin: 4,
		selectSelector: '[data-kt-pln-filter="financial_year"]',
	},
	{
		id: "procurement-plan-register",
		route: "/desk/procurement-plan-register",
		rootTestId: "kt-pln-ui02-root",
		liveAttr: "data-kt-pln-live",
		primaryCtaTestId: "kt-pln-ui02-submit",
		selectSelector: '[data-kt-field="financial_year"]',
	},
	{
		id: "procurement-plan-builder",
		route: "/desk/procurement-plan-builder",
		rootTestId: "kt-pln-ui03-root",
		liveAttr: "data-kt-pln-live",
		primaryCtaTestId: "kt-pln-ui03-add-demand",
	},
	{
		id: "procurement-plan-item-editor",
		route: "/desk/procurement-plan-item-editor",
		rootTestId: "kt-pln-ui06-root",
		liveAttr: "data-kt-pln-live",
		primaryCtaTestId: "kt-pln-ui06-request-finance",
		selectSelector: '[data-kt-pln-field="procurement_method"]',
		assertEditableInputs: true,
		assertHeadline: false,
	},
	{
		id: "procurement-plan-review",
		route: "/desk/procurement-plan-review",
		rootTestId: "kt-pln-ui08-root",
		liveAttr: "data-kt-pln-live",
		primaryCtaTestId: "kt-pln-ui08-primary",
	},
	{
		id: "procurement-plan-approved",
		route: "/desk/procurement-plan-approved",
		rootTestId: "kt-pln-ui09-root",
		liveAttr: "data-kt-pln-live",
		primaryCtaTestId: "kt-pln-ui09-add-item",
		selectSelector: '[data-kt-pln-ui09-filter="ou"]',
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
			// Demands create ownership is Requester-pair scoped — Admin alone is blocked.
			if (surface.id === "demand-form" || surface.id === "demands-workspace") {
				await page.context().clearCookies();
				await loginAsDemandRequester(page);
			}
			// Administrator has no Departmental Needs operational assignment at all.
			if (surface.id === "departmental-needs-new") {
				await page.context().clearCookies();
				await loginAsDepartmentalNeedsRequester(page);
			}
			let route = surface.route;
			if (surface.id === "demand-review") {
				await page.goto("/desk", { waitUntil: "domcontentloaded" });
				const demandName = await page.evaluate(async () => {
					const r = await (
						window as unknown as {
							frappe: {
								call: (o: { method: string }) => Promise<{
									message?: { demand?: string };
								}>;
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
				route = `/desk/demand-review/${demandName}`;
			}
			if (
				surface.id === "planning-workspace" ||
				surface.id === "procurement-plan-register" ||
				surface.id === "procurement-plan-builder"
			) {
				await page.goto("/desk", { waitUntil: "domcontentloaded" });
				const prep = await page.evaluate(async () => {
					const r = await (
						window as unknown as {
							frappe: {
								call: (o: { method: string }) => Promise<{
									message?: {
										builder_route?: string;
										empty_draft_plan?: string;
									};
								}>;
							};
						}
					).frappe.call({
						method:
							"kentender_procurement.procurement_planning.api.prepare_planning_gate03_ui",
					});
					return r.message || {};
				});
				await page.context().clearCookies();
				await loginAsMohPlanningOfficer(page);
				if (surface.id === "procurement-plan-builder") {
					const plan = prep.empty_draft_plan || "";
					expect(plan).toBeTruthy();
					route = `/desk/procurement-plan-builder?plan=${encodeURIComponent(plan)}`;
				}
			}
			if (surface.id === "procurement-plan-item-editor") {
				await page.goto("/desk", { waitUntil: "domcontentloaded" });
				const prep = await page.evaluate(async () => {
					const r = await (
						window as unknown as {
							frappe: {
								call: (o: {
									method: string;
									args?: Record<string, unknown>;
								}) => Promise<{
									message?: { plan_item?: string };
								}>;
							};
						}
					).frappe.call({
						method:
							"kentender_procurement.procurement_planning.api.prepare_planning_gate04_ui",
						args: { with_plan_item: 1 },
					});
					return r.message || {};
				});
				await page.context().clearCookies();
				await loginAsMohPlanningOfficer(page);
				const item = prep.plan_item || "";
				expect(item).toBeTruthy();
				route = `/desk/procurement-plan-item-editor?plan_item=${encodeURIComponent(item)}`;
			}
			if (surface.id === "procurement-plan-review") {
				await page.goto("/desk", { waitUntil: "domcontentloaded" });
				const prep = await page.evaluate(async () => {
					const r = await (
						window as unknown as {
							frappe: {
								call: (o: { method: string }) => Promise<{
									message?: { empty_draft_plan?: string };
								}>;
							};
						}
					).frappe.call({
						method:
							"kentender_procurement.procurement_planning.api.prepare_planning_gate05_approval_ui",
					});
					return r.message || {};
				});
				await page.context().clearCookies();
				await loginAsMohPlanningReviewer(page);
				const plan = prep.empty_draft_plan || "";
				expect(plan).toBeTruthy();
				route = `/desk/procurement-plan-review?plan=${encodeURIComponent(plan)}`;
			}
			if (surface.id === "procurement-plan-approved") {
				await page.goto("/desk", { waitUntil: "domcontentloaded" });
				const prep = await page.evaluate(async () => {
					const r = await (
						window as unknown as {
							frappe: {
								call: (o: { method: string }) => Promise<{
									message?: { empty_draft_plan?: string };
								}>;
							};
						}
					).frappe.call({
						method:
							"kentender_procurement.procurement_planning.api.prepare_planning_gate06_approved_ui",
					});
					return r.message || {};
				});
				await page.context().clearCookies();
				await loginAsMohPlanningOfficer(page);
				const plan = prep.empty_draft_plan || "";
				expect(plan).toBeTruthy();
				route = `/desk/procurement-plan-approved?plan=${encodeURIComponent(plan)}`;
			}
			await page.goto(route, { waitUntil: "domcontentloaded" });
			const root = page.locator(
				`[data-testid="${surface.rootTestId}"][${surface.liveAttr}="1"]`,
			);
			await expect(root).toBeVisible({ timeout: 45_000 });
			await assertStitchDeskChrome(page, {
				rootTestId: surface.rootTestId,
				primaryCtaTestId: surface.primaryCtaTestId,
				primaryCtaStyle:
					"primaryCtaStyle" in surface ? surface.primaryCtaStyle : "filled",
				secondaryCtaTestId:
					"secondaryCtaTestId" in surface ? surface.secondaryCtaTestId : undefined,
				selectSelector:
					"selectSelector" in surface ? surface.selectSelector : undefined,
				assertPrimaryHover:
					"assertPrimaryHover" in surface ? surface.assertPrimaryHover : false,
				assertEditableInputs:
					"assertEditableInputs" in surface ? surface.assertEditableInputs : false,
				assertHeadline:
					"assertHeadline" in surface ? surface.assertHeadline : true,
				primaryRadiusMin:
					"primaryRadiusMin" in surface ? surface.primaryRadiusMin : undefined,
				headlineSelector:
					surface.id === "budget-overview" ||
					surface.id === "budget-lines" ||
					surface.id === "budget-funding-activity" ||
					surface.id === "budget-downstream" ||
					surface.id === "budget-review" ||
					surface.id === "budget-audit" ||
					surface.id === "budget-revisions"
						? "[data-kt-bud-budget-title]"
						: surface.id === "budget-revision-create"
							? ".kt-bud-rev-create-title"
							: surface.id === "budget-revision-review"
								? ".kt-bud-rev-review-title"
								: surface.id === "demand-review"
									? ".kt-dem-review h1, [data-testid='kt-dem-ui04-root'] h1"
									: surface.id === "procurement-plan-item-editor"
										? "[data-kt-pln-editor-title]"
										: undefined,
			});
		});
	}

	test("Material expand_more selects never stack SVG Forms chevron", async ({ page }) => {
		// Downstream filter bar is the chronic double-chevron surface (SVG + Material).
		await page.goto("/desk/strategy-plan-downstream-usage/MOH-SP-2026-2030", {
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
