import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	loginAsMohPlanningViewer,
	preparePlanningGate06Approved,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui10-root"]';

test.describe("PLN-UI-10 Draft Plan update overview", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("Planner sees Stitch update canvas with Added change", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate06Approved(page, { withSuccessor: true });
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-update?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui10-root",
			primaryCtaTestId: "kt-pln-ui10-validate",
			primaryCtaStyle: "bordered",
		});
		await expect(page.getByRole("heading", { name: "Plan update" })).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui10-banner")).toContainText(
			"remains active until this update is approved",
		);
		await expect(page.getByTestId("kt-pln-ui10-summary")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui10-context")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui10-reason")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui10-changes-table")).toBeVisible();
		await expect(page.locator(`${ROOT} [data-kt-pln-ui10-row]`).getByText("Added")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui10-submit")).toBeDisabled();
		await expect(page.getByTestId("kt-pln-ui10-unchanged")).toBeVisible();
		await expect(page.locator(`${ROOT} nav`)).toHaveCount(0);
		await expect(page.getByText("Create Tender")).toHaveCount(0);
	});

	test("Viewer cannot validate, save, submit, or cancel", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate06Approved(page, { withSuccessor: true });
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningViewer(page);
		await page.goto(
			`/desk/procurement-plan-update?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui10-validate")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui10-save")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui10-submit")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui10-cancel")).toBeHidden();
		await expect(
			page.locator(`${ROOT} [data-kt-pln-action="remove-from-update"]`),
		).toHaveCount(0);
	});

	test("Removing the last Added item shows No changes remain", async ({ page }) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate06Approved(page, { withSuccessor: true });
		expect(prep.empty_draft_plan).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-update?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await page
			.locator(`${ROOT} [data-kt-pln-ui10-row] [data-kt-pln-action="row-overflow"]`)
			.click();
		const removeAction = page.locator(
			`${ROOT} [data-kt-pln-ui10-row] [data-kt-pln-action="remove-from-update"]`,
		);
		await expect(removeAction).toBeVisible();
		await removeAction.click();
		const dialog = page.getByRole("dialog", { name: /Remove Plan Item from draft/i });
		await expect(dialog).toBeVisible();
		await dialog.locator('[data-kt-field="reason"]').fill(
			"Added for demonstration; remove from this draft",
		);
		await dialog.getByTestId("kt-pln-ui05a-confirm").click();
		await expect(page.getByTestId("kt-pln-ui10-no-changes")).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui10-cancel")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui10-submit")).toBeHidden();
	});
});
