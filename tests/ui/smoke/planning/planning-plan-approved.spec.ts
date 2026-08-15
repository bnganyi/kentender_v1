import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	loginAsMohPlanningViewer,
	preparePlanningGate06Approved,
	preparePlanningScnAdd,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui09-root"]';
const BUILDER = '[data-testid="kt-pln-ui03-root"]';

test.describe("PLN-UI-09 Approved Plan and implementation", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("retired UI-10 route is absent and has no compatibility canvas", async ({ page }) => {
		await loginAsMohPlanningOfficer(page);
		await page.goto("/desk/procurement-plan-update", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-pln-ui10-root"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-pln-ui03-root"]')).toHaveCount(0);
	});

	test("Planner sees the current Approved Version without Planning publication", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate06Approved(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-approved?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui09-root",
			primaryCtaTestId: "kt-pln-ui09-add-item",
			selectSelector: `${ROOT} [data-kt-pln-ui09-filter="ou"]`,
		});
		await expect(page.getByTestId("kt-pln-ui09-header")).toBeVisible();
		const liveTitle = await page.locator("[data-kt-pln-ui09-title]").innerText();
		expect(liveTitle.trim()).toBeTruthy();
		expect(liveTitle.trim()).not.toBe("Annual Procurement Plan");
		expect(liveTitle.trim()).not.toBe("Approved procurement plan");
		await expect(page.locator("[data-kt-pln-ui09-version]")).toContainText(
			"Approved Version",
		);
		await expect(page.getByTestId("kt-pln-ui09-add-item")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-export")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-summary")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-filters")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-implementation-table")).toBeVisible();
		await expect(page.getByRole("heading", { name: "Version history" })).toBeVisible();
		await expect(page.getByText("Publication Evidence")).toHaveCount(0);
		await expect(page.locator(`${ROOT} nav`)).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui09-successor-notice")).toBeHidden();
		await expect(page.getByText("Create Tender")).toHaveCount(0);
	});

	test("Successor banner Continue update opens the ordinary populated builder", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate06Approved(page, { withSuccessor: true });
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-approved?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui09-successor-notice")).toBeVisible();
		await expect(page.getByText(/Draft Version .* in progress/i)).toBeVisible();
		await page.getByTestId("kt-pln-ui09-continue").click();
		await expect(page).toHaveURL(/procurement-plan-builder/, { timeout: 45_000 });
		await expect(page.locator('[data-testid="kt-pln-ui03-root"]')).toHaveAttribute(
			"data-kt-pln-builder-state",
			"PLN-UI-05",
		);
	});

	test("PLN-UI-05 successor awaiting Finance matches the approved state", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningScnAdd(page, "awaiting_finance");
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(prep.update_route || "", { waitUntil: "domcontentloaded" });
		const builder = page.locator(`${BUILDER}[data-kt-pln-live="1"]`);
		await expect(builder).toBeVisible({ timeout: 45_000 });
		await expect(builder).toHaveAttribute("data-kt-pln-builder-state", "PLN-UI-05");
		const summary = page.getByTestId("kt-pln-ui05-successor-summary");
		await expect(summary).toContainText("Draft Plan Items");
		await expect(summary).toContainText("2");
		await expect(summary).toContainText("KES 535,000,000");
		await expect(summary).toContainText("KES 80,000,000 added");
		await expect(summary).toContainText("2 of 2");
		await expect(summary).toContainText("1 of 2");
		await expect(summary).toContainText("Needs attention");
		await expect(builder).toContainText(
			"Approved Version 1 remains active while this update is prepared and reviewed.",
		);
		await expect(builder.locator("[data-kt-pln-update-reason]")).toHaveValue(
			"Add the approved digital-health technical staff certification programme to the FY 2027/28 Plan so delivery can begin before 31 December 2027.",
		);
		await expect(builder).toContainText("Funding confirmation is still required for PPI-MOH-2027-022");
		await expect(builder).toContainText(
			"1 unchanged Active Plan Item remains operational in Approved Version 1 · Tender TND-MOH-2027-008 remains active",
		);
		await expect(page.getByTestId("kt-pln-ui05-table")).toContainText("View Plan Item");
		await expect(builder.getByRole("button", { name: "Submit for review" })).toBeHidden();
		await expect(builder.locator("nav")).toHaveCount(0);
	});

	test("PLN-UI-05 successor Ready exposes the single professional submission action", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningScnAdd(page, "finance_confirmed");
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(prep.update_route || "", { waitUntil: "domcontentloaded" });
		const builder = page.locator(`${BUILDER}[data-kt-pln-live="1"]`);
		await expect(builder).toBeVisible({ timeout: 45_000 });
		const summary = page.getByTestId("kt-pln-ui05-successor-summary");
		await expect(summary).toContainText("2 of 2");
		await expect(summary).toContainText("Ready");
		await expect(builder).toContainText("All required Planning validation and Finance confirmations are ready.");
		await expect(builder.getByRole("button", { name: "Save draft" })).toBeVisible();
		await expect(builder.getByRole("button", { name: "Submit for review" })).toBeVisible();
	});

	test("Viewer cannot add or propose removal but may export the Approved projection", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate06Approved(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningViewer(page);
		await page.goto(
			`/desk/procurement-plan-approved?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui09-add-item")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui09-export")).toBeVisible();
		await expect(
			page.locator(
				`${ROOT} [data-kt-pln-ui09-row] [data-kt-pln-action="propose-removal"]`,
			),
		).toHaveCount(0);
	});

	test("Handoff take-up is visible and Propose removal is omitted", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate06Approved(page, { withHandoff: true });
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-approved?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(
			page.locator(`${ROOT} [data-kt-pln-ui09-row]`).getByText("TND-MOH-TEST-008"),
		).toHaveCount(1);
		await expect(
			page.locator(`${ROOT} [data-kt-pln-ui09-row]`).getByText("Tender active"),
		).toBeVisible();
		await expect(
			page.locator(
				`${ROOT} [data-kt-pln-ui09-row] [data-kt-pln-action="propose-removal"]`,
			),
		).toHaveCount(0);
	});

	test("AC-013: Approved V1 and Tender stay live while Draft V2 exists", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningScnAdd(page);
		expect(prep.plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-approved?plan=${encodeURIComponent(prep.plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.locator("[data-kt-pln-ui09-version]")).toContainText(
			"Approved Version",
		);
		await expect(page.locator("[data-kt-pln-ui09-total]")).toContainText(
			"455,000,000",
		);
		await expect(
			page.locator(`${ROOT} [data-kt-pln-ui09-row]`).getByText("TND-MOH-2027-008"),
		).toHaveCount(1);
		await expect(page.getByTestId("kt-pln-ui09-successor-notice")).toBeVisible();
	});
});
