import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	loginAsMohPlanningViewer,
	loginAsPlanningSystemAdminNoScope,
	preparePlanningGate03,
	preparePlanningWorkspaceState,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui01-root"]';

test.describe("PLN-UI-01 Procurement Planning workspace", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("planner sees the approved Section 9.1 workspace composition", async ({ page }) => {
		await loginAsAdministrator(page);
		await preparePlanningWorkspaceState(page, "BASE");
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto("/desk/planning-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.locator(`${ROOT}.kt-stitch-canvas`)).toBeVisible();
		await expect(page.getByRole("heading", { name: "Procurement Planning" })).toBeVisible();
		await expect(page.locator(ROOT)).toContainText(
			/Turn approved needs into funded, approved Plan Items ready for tendering/i,
		);
		await expect(page.getByTestId("kt-pln-ui01-filters")).toBeVisible();
		await expect(page.locator('[data-kt-pln-pe-readonly]')).toContainText(/Ministry of Health/i);
		await expect(page.locator('[data-kt-pln-filter="procuring_entity"]')).toBeHidden();
		await expect(page.locator('[data-kt-pln-fy-readonly]')).toHaveText("2027/28");
		await expect(page.locator('[data-kt-pln-filter="financial_year"]')).toBeHidden();
		await expect(page.locator('[data-kt-pln-action="change-context"]')).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-plan-panel")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-plan-panel")).not.toContainText(/Current Plan/i);
		await expect(page.locator('[data-kt-pln-plan-title]')).toHaveText(
			"Ministry of Health Annual Procurement Plan 2027/28",
		);
		await expect(page.getByTestId("kt-pln-ui01-plan-panel")).toContainText(/Approved/i);
		await expect(page.getByTestId("kt-pln-ui01-work-section")).toBeVisible();
		await expect(page.locator('[data-kt-pln-filter="work_type"]')).toBeVisible();
		const workFilter = page.getByTestId("kt-pln-ui01-work-filter");
		await expect(workFilter).toContainText("All work");
		await expect(workFilter).toContainText("Approved Demands");
		await expect(workFilter).toContainText("Plan Items");
		await expect(workFilter).toContainText("Returned work");
		await expect(page.getByTestId("kt-pln-ui01-work-search")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-primary-action")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-primary-action")).toContainText(
			/View approved plan/i,
		);
		await expect(page.getByTestId("kt-pln-ui01-table").locator("thead th")).toHaveCount(7);
		await expect(page.locator('[data-kt-pln-work-body]')).toContainText(/Add to plan/i);
		await expect(page.getByTestId("kt-pln-ui01-waiting-section")).toBeVisible();
		await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);
		const sourceStyles = await page.locator(ROOT).evaluate((root) => {
			const style = (selector: string) => {
				const element = root.querySelector(selector) as HTMLElement;
				const computed = getComputedStyle(element);
				return {
					family: computed.fontFamily,
					size: computed.fontSize,
					lineHeight: computed.lineHeight,
					weight: computed.fontWeight,
					fill: computed.fontVariationSettings,
					paddingLeft: computed.paddingLeft,
					flexDirection: computed.flexDirection,
				};
			};
			return {
				headline: style('[data-testid="kt-pln-ui01-header"] h1'),
				body: style('[data-testid="kt-pln-ui01-header"] p'),
				planTitle: style('[data-kt-pln-plan-title]'),
				label: style('.kt-pln-metric .font-label-caps'),
				data: style('.kt-pln-data-value'),
				search: style('[data-kt-pln-work-search]'),
				sectionIcon: style('[data-testid="kt-pln-ui01-work-section"] .kt-pln-section-title .material-symbols-outlined'),
				versionIcon: style('.kt-pln-version-status .material-symbols-outlined'),
				emptyIcon: style('[data-kt-pln-waiting-empty] .material-symbols-outlined'),
				empty: style('[data-kt-pln-waiting-empty]'),
			};
		});
		expect(sourceStyles.headline).toMatchObject({ size: "30px", lineHeight: "38px", weight: "700" });
		expect(sourceStyles.headline.family).toContain("Manrope");
		expect(sourceStyles.body).toMatchObject({ size: "16px", lineHeight: "24px", weight: "400" });
		expect(sourceStyles.body.family).toContain("Inter");
		expect(sourceStyles.planTitle).toMatchObject({ size: "24px", lineHeight: "32px", weight: "600" });
		expect(sourceStyles.label).toMatchObject({ size: "12px", lineHeight: "16px", weight: "700" });
		expect(sourceStyles.data).toMatchObject({ size: "16px", lineHeight: "24px", weight: "500" });
		expect(sourceStyles.data.family).toContain("JetBrains Mono");
		expect(sourceStyles.search.paddingLeft).toBe("40px");
		expect(sourceStyles.sectionIcon.size).toBe("16px");
		expect(sourceStyles.versionIcon).toMatchObject({ size: "12px" });
		expect(sourceStyles.versionIcon.fill).toContain('"FILL" 1');
		expect(sourceStyles.emptyIcon.size).toBe("36px");
		expect(sourceStyles.empty.flexDirection).toBe("column");
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui01-root",
			primaryCtaTestId: "kt-pln-ui01-primary-action",
			primaryRadiusMin: 4,
			selectSelector: '[data-kt-pln-filter="work_type"]',
		});
		await page.locator('[data-kt-pln-action="change-context"]').click();
		const financialYear = page.locator('[data-kt-pln-filter="financial_year"]');
		await expect(financialYear).toBeVisible();
		await financialYear.selectOption("2027/28");
		await expect(financialYear).toBeHidden();

		await page.locator('[data-kt-pln-row-action="add_to_plan"]').click();
		await expect(page).toHaveURL(/\/desk\/procurement-plan-approved\//, {
			timeout: 30_000,
		});
		await expect(page.locator('[data-testid="kt-pln-ui09-root"][data-kt-pln-live="1"]')).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui04-dialog")).toBeVisible();
		await expect(page.locator('[data-kt-demand-select]:checked')).toHaveCount(1);
	});

	test("search and work filters refresh without showing the initial loader or shifting the workspace", async ({
		page,
	}) => {
		let delayNextWorkspaceRequest = false;
		await page.route(
			"**/api/method/kentender_procurement.procurement_planning.api.get_planning_workspace",
			async (route) => {
				if (delayNextWorkspaceRequest) {
					delayNextWorkspaceRequest = false;
					await new Promise((resolve) => setTimeout(resolve, 800));
				}
				await route.continue();
			},
		);
		await loginAsAdministrator(page);
		await preparePlanningWorkspaceState(page, "BASE");
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto("/desk/planning-workspace", { waitUntil: "domcontentloaded" });

		const root = page.getByTestId("kt-pln-ui01-root");
		const header = page.getByTestId("kt-pln-ui01-header");
		const loader = page.locator("[data-kt-pln-loading]");
		await expect(root).toHaveAttribute("data-kt-pln-live", "1", { timeout: 45_000 });
		await expect(loader).toBeHidden();
		const initialHeaderTop = (await header.boundingBox())?.y;
		expect(initialHeaderTop).toBeDefined();

		delayNextWorkspaceRequest = true;
		await page.getByTestId("kt-pln-ui01-work-search").fill("Digital health");
		await expect(root).toHaveAttribute("aria-busy", "true", { timeout: 2_000 });
		await expect(loader).toBeHidden();
		expect((await header.boundingBox())?.y).toBe(initialHeaderTop);
		await expect(root).toHaveAttribute("aria-busy", "false", { timeout: 5_000 });

		delayNextWorkspaceRequest = true;
		await page.getByTestId("kt-pln-ui01-work-filter").selectOption({
			label: "Approved Demands",
		});
		await expect(root).toHaveAttribute("aria-busy", "true", { timeout: 2_000 });
		await expect(loader).toBeHidden();
		expect((await header.boundingBox())?.y).toBe(initialHeaderTop);
		await expect(root).toHaveAttribute("aria-busy", "false", { timeout: 5_000 });
	});

	test("zero-scope admin sees blocked panel", async ({ page }) => {
		await loginAsAdministrator(page);
		await preparePlanningGate03(page);
		await page.context().clearCookies();
		await loginAsPlanningSystemAdminNoScope(page);
		await page.goto("/desk/planning-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui01-blocked")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-blocked")).toContainText(
			/authorised Procuring Entity|Planning assignment/i,
		);
	});

	test("Administrator support viewer must deliberately select an approved Plan", async ({ page }) => {
		await loginAsAdministrator(page);
		await preparePlanningGate03(page);
		await page.goto("/desk/planning-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-read-only", "1");
		await expect(page.getByTestId("kt-pln-ui01-blocked")).toBeHidden();
		const entitySelect = page.locator('[data-kt-pln-filter="procuring_entity"]');
		await expect(entitySelect).toBeVisible();
		await expect(entitySelect).not.toContainText(/All authorised entities/i);
		await expect(entitySelect).toHaveValue("");
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-can-create", "0");
		await entitySelect.selectOption("PE-MOH");
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-can-create", "0");
		await expect(page.getByTestId("kt-pln-ui01-plan-panel")).toContainText(/Approved/i);
		await expect(page.getByTestId("kt-pln-ui01-primary-action")).toContainText(
			/View approved plan/i,
		);
		await expect(page.locator('[data-kt-pln-work-body] tr')).toHaveCount(0);
		await expect(page.locator('[data-kt-pln-waiting-body] tr')).toHaveCount(0);
	});

	test("Viewer queue has no Confirm funding or Review return", async ({ page }) => {
		await loginAsAdministrator(page);
		await preparePlanningGate03(page);
		await page.context().clearCookies();
		await loginAsMohPlanningViewer(page);
		await page.goto("/desk/planning-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.locator('[data-kt-pln-queue-action="confirm_funding"]')).toHaveCount(0);
		await expect(page.locator('[data-kt-pln-queue-action="continue_item"]')).toHaveCount(0);
		const root = page.getByTestId("kt-pln-ui01-root");
		await expect(root).not.toContainText("Confirm funding");
		await expect(root).not.toContainText("Review return");
		await expect(page.locator('[data-kt-pln-work-body] tr')).toHaveCount(0);
		await expect(page.locator('[data-kt-pln-waiting-body] tr')).toHaveCount(0);
	});

	for (const scenario of [
		{ fixture: "A", state: "NO_PLAN", fy: "2028/29", action: "Create annual plan" },
		{ fixture: "B", state: "INITIAL_DRAFT_EMPTY", fy: "2028/29", action: "Continue planning" },
		{ fixture: "C", state: "DRAFT_WITH_PLANNER_ACTION", fy: "2027/28", action: "Continue plan update" },
		{ fixture: "D", state: "DRAFT_AWAITING_FINANCE", fy: "2027/28", action: "View plan update" },
		{ fixture: "E", state: "VERSION_AWAITING_PROFESSIONAL_REVIEW", fy: "2027/28", action: "View approved plan" },
		{ fixture: "F", state: "APPROVED_NO_WORK", fy: "2027/28", action: "View approved plan" },
	] as const) {
		test(`renders authoritative PLN-UI-01${scenario.fixture} state`, async ({ page }) => {
			await loginAsAdministrator(page);
			await preparePlanningWorkspaceState(page, scenario.fixture);
			await page.context().clearCookies();
			await loginAsMohPlanningOfficer(page);
			await page.goto(`/desk/planning-workspace?procuring_entity=PE-MOH&financial_year=${encodeURIComponent(scenario.fy)}`, { waitUntil: "domcontentloaded" });
			const root = page.getByTestId("kt-pln-ui01-root");
			await expect(root).toHaveAttribute("data-kt-pln-live", "1", { timeout: 45_000 });
			await expect(root).toHaveAttribute("data-kt-pln-state", scenario.state);
			await expect(page.getByTestId("kt-pln-ui01-primary-action")).toHaveText(new RegExp(scenario.action, "i"));
			await expect(page.locator("[data-kt-pln-context-helper]")).toContainText("do not change record ownership");

			if (scenario.fixture === "A") {
				await expect(page.locator("[data-kt-pln-no-plan-heading]")).toHaveText("No annual Procurement Plan");
				await expect(root).toContainText("Create the annual Plan before adding the 2 Approved Demands ready for Planning.");
				await expect(page.locator("[data-kt-pln-work-body] tr")).toHaveCount(0);
				await expect(page.locator("[data-kt-pln-work-controls]")).toBeHidden();
			}
			if (scenario.fixture === "B") {
				await expect(page.locator("[data-kt-pln-plan-reference]")).toHaveText("PLN-MOH-2028-001");
				await expect(page.locator("[data-kt-pln-work-body] tr")).toHaveCount(2);
				await expect(page.locator("[data-kt-pln-work-body]")).toContainText("DMD-MOH-2028-001");
				await expect(page.locator("[data-kt-pln-work-body]")).toContainText("DMD-MOH-2028-002");
			}
			if (scenario.fixture === "C") {
				await expect(page.locator("[data-kt-pln-work-body] tr")).toHaveCount(1);
				await expect(page.locator("[data-kt-pln-work-body]")).toContainText("PPI-MOH-2027-022");
				await expect(page.locator("[data-kt-pln-row-action=complete_item]")).toBeVisible();
			}
			if (scenario.fixture === "D") {
				await expect(page.locator("[data-kt-pln-work-body] tr")).toHaveCount(0);
				await expect(page.getByTestId("kt-pln-ui01-waiting-table").locator("thead th")).toHaveCount(4);
				await expect(page.locator("[data-kt-pln-waiting-body]")).toContainText("Awaiting confirmation");
				await expect(page.locator("[data-kt-pln-waiting-body] button, [data-kt-pln-waiting-body] a")).toHaveCount(0);
			}
			if (scenario.fixture === "E") {
				await expect(page.locator("[data-kt-pln-waiting-body]")).toContainText("Professional review");
				await expect(page.locator("[data-kt-pln-waiting-body]")).toContainText("Head of Procurement");
				await expect(page.locator("[data-kt-pln-waiting-body] button, [data-kt-pln-waiting-body] a")).toHaveCount(0);
				await expect(page.getByRole("button", { name: /^(Approve|Return)$/i })).toHaveCount(0);
			}
			if (scenario.fixture === "F") {
				await expect(page.locator("[data-kt-pln-work-body] tr")).toHaveCount(0);
				await expect(page.locator("[data-kt-pln-waiting-body] tr")).toHaveCount(0);
				await expect(root).not.toContainText(/Add Plan Item|Add to plan/i);
				await expect(page.getByTestId("kt-pln-ui01-plan-panel")).toContainText("KES 535,000,000");
			}
		});
	}

	for (const mobile of [
		{ fixture: "A", state: "NO_PLAN", family: "empty" },
		{ fixture: "B", state: "INITIAL_DRAFT_EMPTY", family: "actionable" },
		{ fixture: "D", state: "DRAFT_AWAITING_FINANCE", family: "waiting" },
	] as const) {
		test(`supports keyboard focus and mobile ${mobile.family} reflow`, async ({ page }) => {
			await page.setViewportSize({ width: 390, height: 844 });
			await loginAsAdministrator(page);
			await preparePlanningWorkspaceState(page, mobile.fixture);
			await page.context().clearCookies();
			await loginAsMohPlanningOfficer(page);
			const fy = mobile.fixture === "A" || mobile.fixture === "B" ? "2028/29" : "2027/28";
			await page.goto(`/desk/planning-workspace?procuring_entity=PE-MOH&financial_year=${encodeURIComponent(fy)}`, { waitUntil: "domcontentloaded" });
			const root = page.getByTestId("kt-pln-ui01-root");
			await expect(root).toHaveAttribute("data-kt-pln-state", mobile.state, { timeout: 45_000 });
			const primary = page.getByTestId("kt-pln-ui01-primary-action");
			await primary.focus();
			await expect(primary).toBeFocused();
			const box = await root.boundingBox();
			expect(box).not.toBeNull();
			expect((box?.x || 0) + (box?.width || 0)).toBeLessThanOrEqual(391);
			if (mobile.family === "actionable") {
				await expect(page.locator("[data-kt-pln-work-body] tr")).toHaveCount(2);
			}
			if (mobile.family === "waiting") {
				await expect(page.locator("[data-kt-pln-waiting-table] thead th")).toHaveCount(4);
				await expect(page.locator("[data-kt-pln-waiting-body] button")).toHaveCount(0);
			}
		});
	}
});
