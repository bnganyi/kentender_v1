import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	loginAsMohPlanningViewer,
	preparePlanningGate06Approved,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui09-root"]';

test.describe("PLN-UI-09 Approved Plan and implementation", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Planner sees Stitch approved canvas; publication is not invented", async ({
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
		await expect(page.locator("[data-kt-pln-ui09-version]")).toContainText(
			"Approved Version",
		);
		await expect(page.getByText("Approved baseline is read-only")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-add-item")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-export")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-summary")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-filters")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-implementation-table")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui09-publication")).toBeVisible();
		await expect(
			page.getByRole("heading", { name: "Publication Evidence" }),
		).toBeVisible();
		await expect(page.locator("[data-kt-pln-ui09-pub-status]")).toHaveText(
			"Not published",
		);
		await expect(page.getByText("Published", { exact: true })).toHaveCount(0);
		await expect(page.locator(`${ROOT} nav`)).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui09-successor-notice")).toBeHidden();
		await expect(page.getByText("Create Tender")).toHaveCount(0);
	});

	test("Successor banner Continue update opens the draft update canvas", async ({
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
		await expect(page).toHaveURL(/procurement-plan-update/, { timeout: 45_000 });
	});

	test("Viewer cannot add, export, or propose removal", async ({ page }) => {
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
		await expect(page.getByTestId("kt-pln-ui09-export")).toBeHidden();
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
});
