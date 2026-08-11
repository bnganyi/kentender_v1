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

	test("empty draft shows guidance + Add approved demand CTA", async ({ page }) => {
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
		await expect(page.getByTestId("kt-pln-ui03-empty")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-empty")).toContainText(/No plan items yet/i);
		await expect(page.getByTestId("kt-pln-ui03-add-demand")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-add-pending")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-items")).toBeHidden();
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
		// Stitch PLN-UI-05: Draft chip (not plan OPEN), footer "Submit for sign-off".
		await expect(page.getByTestId("kt-pln-ui03-lifecycle")).toHaveText(/Draft/i);
		await expect(page.getByTestId("kt-pln-ui05-submit-dept")).toContainText(/Submit for sign-off/i);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui03-summary"]`)).not.toContainText(
			/Preference and reservation/i,
		);
		await expect(page.getByTestId("kt-pln-ui03-filters")).toBeHidden();
		const issueStrip = page.getByTestId("kt-pln-ui05-issue-strip");
		const submit = page.getByTestId("kt-pln-ui05-submit-dept");
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
