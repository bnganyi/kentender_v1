import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	loginAsPlanningSystemAdminNoScope,
	preparePlanningGate03,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui01-root"]';

test.describe("PLN-UI-01 Procurement Planning workspace", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("planner sees Stitch v1.9 regions, chrome, footer", async ({ page }) => {
		await loginAsAdministrator(page);
		await preparePlanningGate03(page);
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
		await expect(page.getByTestId("kt-pln-ui01-scope-helper")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-scope-helper")).toContainText(
			/define the workspace scope|filter visibility/i,
		);
		await expect(page.locator('[data-kt-pln-filter="procuring_entity"]')).toBeVisible();
		const peValues = await page
			.locator('[data-kt-pln-filter="procuring_entity"] option')
			.evaluateAll((opts) => opts.map((o) => (o as HTMLOptionElement).value));
		expect(peValues.filter(Boolean)).toEqual(expect.arrayContaining(["PE-MOH"]));
		expect(peValues.join(" ")).not.toMatch(/PE-CGK|Kisumu/i);
		await expect(page.locator('[data-kt-pln-filter="financial_year"]')).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-plan-panel")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-plan-panel")).toContainText(/Plan Items/i);
		await expect(page.getByTestId("kt-pln-ui01-queue")).toBeVisible();
		await expect(page.locator('[data-kt-pln-filter="work_type"]')).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-work-search")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-open-plan")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-open-plan")).toContainText(/Open current plan/i);
		await expect(page.getByTestId("kt-pln-ui01-table-footer")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-table-footer")).toContainText(/Showing/i);
		await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui01-root",
			primaryCtaTestId: "kt-pln-ui01-open-plan",
			selectSelector: '[data-kt-pln-filter="financial_year"]',
		});
	});

	test("zero-scope admin sees blocked panel", async ({ page }) => {
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

	test("Administrator support viewer sees sample data read-only", async ({ page }) => {
		await loginAsAdministrator(page);
		await preparePlanningGate03(page);
		await page.goto("/desk/planning-workspace", { waitUntil: "domcontentloaded" });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-read-only", "1");
		await expect(page.getByTestId("kt-pln-ui01-blocked")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui01-readonly")).toHaveCount(0);
		await expect(page.locator('[data-kt-pln-filter="procuring_entity"]')).toContainText(
			/All authorised entities/i,
		);
		await expect(page.getByTestId("kt-pln-ui01-plan-panel")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui01-register")).toBeHidden();
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-can-create", "0");
		// Support viewer must never be sent to register via a fake "Open" CTA when empty.
		await page.locator('[data-kt-pln-filter="procuring_entity"]').selectOption("PE-MOH");
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-can-create", "0");
		const hasPlan = await page.locator(ROOT).getAttribute("data-kt-pln-plan");
		if (!hasPlan) {
			await expect(page.getByTestId("kt-pln-ui01-open-plan")).toBeHidden();
			await expect(page.getByTestId("kt-pln-ui01-no-plan")).toBeVisible();
			await expect(page.getByTestId("kt-pln-ui01-no-plan")).toContainText(
				/Support viewers can browse existing plans only/i,
			);
			await expect(page.getByTestId("kt-pln-ui01-header-create")).toBeHidden();
		} else {
			await expect(page.getByTestId("kt-pln-ui01-open-plan")).toBeVisible();
		}
	});
});
