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
		await expect(
			page.getByTestId("kt-pln-ui03-header").locator("[data-kt-pln-builder-version]"),
		).toContainText(/Draft Version/i);
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
		await expect(page.getByTestId("kt-pln-ui03-header")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-header")).toBeHidden();
		await expect(page.locator(`${ROOT} nav[aria-label='Breadcrumb']`)).toHaveCount(0);
		const emptyPadTop = await page
			.locator(`${ROOT} main > .max-w-7xl`)
			.evaluate((el) => parseFloat(getComputedStyle(el).paddingTop));
		expect(emptyPadTop).toBeLessThanOrEqual(8);
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
		await expect(page.locator(ROOT)).toHaveAttribute("data-kt-pln-builder-state", "populated");
		await expect(page.getByTestId("kt-pln-ui03-empty")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui03-header")).toBeHidden();
		await expect(page.getByTestId("kt-pln-ui05-header")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-header").locator("nav[aria-label='Breadcrumb']")).toHaveCount(0);
		await expect(page.locator(`${ROOT} nav[aria-label='Breadcrumb']`)).toHaveCount(0);
		const popPadTop = await page
			.locator(`${ROOT} main > .max-w-7xl`)
			.evaluate((el) => parseFloat(getComputedStyle(el).paddingTop));
		expect(popPadTop).toBeLessThanOrEqual(8);
		await expect(page.getByTestId("kt-pln-ui05-header")).toContainText(/Add approved demands/i);
		await expect(page.getByTestId("kt-pln-ui05-header")).toContainText(/Open Plan/i);
		await expect(page.getByTestId("kt-pln-ui05-header")).toContainText(/Draft Version/i);
		await expect(page.getByTestId("kt-pln-ui05-lifecycle")).toContainText(/Open Plan/i);
		await expect(page.getByTestId("kt-pln-ui03-items")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-table")).toBeVisible();
		const headers = page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead th`);
		await expect(headers).toHaveCount(8);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead`)).toContainText(
			/Requirement/i,
		);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead`)).toContainText(
			/Organisation Unit/i,
		);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead`)).toContainText(
			/Planned Value/i,
		);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead`)).toContainText(/Method/i);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead`)).toContainText(
			/Schedule/i,
		);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead`)).toContainText(/Finance/i);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead`)).toContainText(
			/Validation/i,
		);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead`)).toContainText(/Action/i);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] thead`)).not.toContainText(
			/Category/i,
		);
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui05-table"] tfoot`)).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui05-table")).toContainText(/Not requested/i);
		await expect(page.getByTestId("kt-pln-ui05-table")).toContainText(/Not completed/i);
		await expect(page.getByTestId("kt-pln-ui05-table")).toContainText(
			/No further plan items added yet/i,
		);
		await expect(page.getByTestId("kt-pln-ui05-run-validation")).toBeEnabled();
		await expect(page.getByTestId("kt-pln-ui05-row-continue").first()).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-issue-strip")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui05-issue-strip")).toContainText(
			/Complete the Plan Item before requesting Finance confirmation/i,
		);
		await page.getByTestId("kt-pln-ui05-run-validation").click();
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible();
		await expect(page.locator("[data-kt-pln-builder-version]").first()).toContainText(/Draft Version/i);
		await expect(page.getByTestId("kt-pln-ui05-submit-review")).toContainText(/Submit for review/i);
		await expect(page.getByTestId("kt-pln-ui05-submit-review")).toBeDisabled();
		await expect(page.locator(`${ROOT} [data-testid="kt-pln-ui03-summary"]`)).not.toContainText(
			/Preference and reservation/i,
		);
		await expect(page.getByTestId("kt-pln-ui03-filters")).toBeHidden();
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui03-root",
			primaryCtaTestId: "kt-pln-ui05-add-demand",
			assertHeadline: false,
		});
		await page.getByTestId("kt-pln-ui05-row-continue").first().click();
		await expect(page).toHaveURL(/procurement-plan-item-editor/, { timeout: 30_000 });
	});

	test("overflow Remove from draft opens 05A and requires a reason", async ({ page }) => {
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
		await expect(page.getByTestId("kt-pln-ui05-row-overflow").first()).toBeVisible();
		const overflow = page.getByTestId("kt-pln-ui05-row-overflow").first();
		await overflow.click();
		const menuItem = page.getByTestId("kt-pln-ui05-remove-from-draft").first();
		await expect(menuItem).toBeVisible();
		await expect(menuItem).toContainText("Remove from draft");
		await expect(menuItem.locator(".material-symbols-outlined")).toHaveText("delete");
		const btnBox = await overflow.boundingBox();
		const menuBox = await menuItem.boundingBox();
		expect(btnBox).toBeTruthy();
		expect(menuBox).toBeTruthy();
		expect(menuBox.y).toBeGreaterThan(btnBox.y);
		expect(menuBox.y).toBeLessThan(btnBox.y + 72);
		await menuItem.click();
		const dialog = page.getByTestId("kt-pln-ui05a-dialog");
		await expect(dialog).toBeVisible();
		const draft = dialog.locator('[data-kt-pln-05a-variant="draft"]');
		await expect(draft).toBeVisible();
		await expect(draft.getByTestId("kt-pln-ui05a-title")).toContainText(
			/Remove Plan Item from draft/i,
		);
		await expect(draft.getByTestId("kt-pln-ui05a-confirm")).toBeVisible();
		await draft.getByTestId("kt-pln-ui05a-confirm").click();
		await expect(draft.locator('[data-kt-field-error="reason"]').first()).toBeVisible();
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
		await draft.locator('[data-kt-field="reason"]').first().fill(
			"Added in error; remove from this draft",
		);
		await draft.getByTestId("kt-pln-ui05a-confirm").click();
		await expect(dialog).toBeHidden({ timeout: 20_000 });
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui03-empty")).toBeVisible();
		await expect(page.locator(`${ROOT} [data-kt-pln-item-row]`)).toHaveCount(0);
		await expect(page.getByRole("dialog", { name: "Message" })).toHaveCount(0);
	});
});
