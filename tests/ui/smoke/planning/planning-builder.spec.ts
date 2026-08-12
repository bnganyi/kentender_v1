import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	preparePlanningGate03,
	preparePlanningGate04,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui03-root"]';

test.describe("PLN-UI-03 Empty Draft plan builder", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("empty draft shows Stitch regions + Add approved Demand CTA", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate03(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-builder?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui03-lifecycle")).toContainText(/Open Plan/i);
		await expect(page.locator("[data-kt-pln-builder-version]")).toContainText(/Draft Version/i);
		await expect(page.getByTestId("kt-pln-ui03-summary")).toContainText(/Plan Items/i);
		await expect(page.getByTestId("kt-pln-ui03-summary")).toContainText(/Total Planned Value/i);
		await expect(page.getByTestId("kt-pln-ui03-summary")).toContainText(/Finance Confirmed/i);
		await expect(page.getByTestId("kt-pln-ui03-summary")).toContainText(/Validation Status/i);
		await expect(page.getByTestId("kt-pln-ui03-summary")).toContainText(/0 of 0/i);
		await expect(page.getByTestId("kt-pln-ui03-summary")).toContainText(/Not run/i);
		await expect(page.getByTestId("kt-pln-ui03-summary").locator(".h-8.w-px").first()).toBeAttached();
		await expect(page.getByTestId("kt-pln-ui03-filters")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-filters").getByLabel("Organisation Unit")).toContainText(
			/All permitted units/i,
		);
		await expect(page.getByTestId("kt-pln-ui03-filters").getByPlaceholder("Search Plan Items")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-empty")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-empty")).toContainText(/No Plan Items yet/i);
		await expect(page.getByTestId("kt-pln-ui03-empty")).toContainText(
			/Add an Approved Demand to begin building this annual Plan/i,
		);
		await expect(page.getByTestId("kt-pln-ui03-empty").locator("span", { hasText: "assignment_late" })).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-add-demand")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-add-pending")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-items")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui05-footer")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-run-validation")).toBeDisabled();
		await expect(page.getByTestId("kt-pln-ui05-submit-review")).toBeDisabled();
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui03-root",
			primaryCtaTestId: "kt-pln-ui03-add-demand",
		});
	});
});

test.describe("PLN-UI-05 Populated Draft plan builder", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("shows Plan Item row, Continue, and Run validation", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate04(page, { withPlanItem: true });
		expect(prep.empty_draft_plan).toBeTruthy();
		expect(prep.plan_item).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-builder?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui03-empty")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui03-items")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-table")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-run-validation")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-row-continue").first()).toBeVisible();
		await page.getByTestId("kt-pln-ui05-run-validation").click();
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible();
		// Shared header: Open Plan pill + Draft Version label (UI-03 Stitch).
		await expect(page.getByTestId("kt-pln-ui03-lifecycle")).toContainText(/Open Plan/i);
		await expect(page.locator("[data-kt-pln-builder-version]")).toContainText(/Draft Version/i);
		await expect(page.getByTestId("kt-pln-ui05-submit-review")).toContainText(/Submit for review/i);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui03-summary"]`)).not.toContainText(
			/Preference and reservation/i,
		);
		await expect(page.getByTestId("kt-pln-ui03-filters")).toBeHidden();
		const issueStrip = page.getByTestId("kt-pln-ui05-issue-strip");
		const submit = page.getByTestId("kt-pln-ui05-submit-review");
		if (await issueStrip.isVisible()) {
			await expect(issueStrip).toContainText(/needs attention/i);
		} else {
			await expect(submit).toBeDisabled();
			const title = (await submit.getAttribute("title")) || "";
			expect(title.length).toBeGreaterThan(0);
		}
		await page.getByTestId("kt-pln-ui05-row-continue").first().click();
		await expect(page).toHaveURL(/procurement-plan-item-editor/, { timeout: 30_000 });
	});
});
