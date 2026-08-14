import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohPlanningOfficer,
	preparePlanningGate04,
	preparePlanningGate05Approval,
} from "../../helpers/planningRoles";
import { assertStitchDeskChrome } from "../../helpers/stitchDeskChrome";

const ROOT = '[data-testid="kt-pln-ui06-root"]';

test.describe("PLN-UI-06 Plan Item editor", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("loads Stitch editor, inline errors, and Request Finance completeness", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate04(page, { withPlanItem: true });
		expect(prep.plan_item).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-item-editor?plan_item=${encodeURIComponent(prep.plan_item || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		const lifecycle = page.getByTestId("kt-pln-ui06-lifecycle");
		const title = page.getByTestId("kt-pln-ui06-title");
		await expect(lifecycle).toBeVisible();
		await expect(lifecycle).toHaveText(/Proposed/i);
		const lifeBox = await lifecycle.boundingBox();
		const titleBox = await title.boundingBox();
		expect(lifeBox && titleBox && lifeBox.x > titleBox.x).toBeTruthy();

		const sidebar = page.getByTestId("kt-pln-ui06-source-sidebar");
		await expect(sidebar).toBeVisible();
		await expect(sidebar).toContainText("Approved source");
		await expect(sidebar).toContainText(/Not requested/i);
		await expect(sidebar).toContainText(
			/Business scope, quantity, owner, delivery requirement and approved value/i,
		);
		await expect(sidebar).toContainText(/Amend those facts on the Demand in Demands/i, {
			timeout: 15_000,
		});
		const viewDemand = page.getByTestId("kt-pln-ui06-view-demand");
		await expect(viewDemand).toBeVisible();
		await expect
			.poll(async () => (await viewDemand.getAttribute("href")) || "")
			.toMatch(/\/desk\/demand-(detail|form)\//);
		expect((await viewDemand.getAttribute("href")) || "").not.toContain("/app/demand/");
		const sticky = await sidebar.evaluate((el) => getComputedStyle(el).position);
		expect(sticky).toBe("sticky");

		await expect(page.locator(ROOT)).toContainText("Procurement approach");
		await expect(page.locator(ROOT)).toContainText("Indicative lotting");
		await expect(page.locator(ROOT)).toContainText("Planned schedule");
		await expect(page.locator(ROOT)).toContainText("Invitation published");
		await expect(page.locator(ROOT)).toContainText("Delivery and completion");
		await expect(page.getByTestId("kt-pln-ui06-save-draft")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui06-request-finance")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui06-cancel")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui06-footer")).toBeInViewport();
		await expect(page.getByTestId("kt-pln-ui06-request-finance")).toBeInViewport();
		await expect(page.getByTestId("kt-pln-ui06-lotting-multiple")).toBeChecked();
		await expect(page.getByTestId("kt-pln-ui06-lotting-details")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui06-add-another")).toHaveCount(0);
		await expect(page.locator(ROOT)).not.toContainText("Planning approach");
		await expect(page.locator(ROOT)).not.toContainText("Source Demand");
		await expect(page.locator(ROOT)).not.toContainText("Save and return to Plan update");
		await expect(page.locator(`${ROOT} nav[aria-label='Breadcrumb']`)).toHaveCount(0);

		await assertStitchDeskChrome(page, {
			rootTestId: "kt-pln-ui06-root",
			primaryCtaTestId: "kt-pln-ui06-request-finance",
			selectSelector: `${ROOT} [data-kt-pln-field="procurement_method"]`,
			assertEditableInputs: true,
			assertHeadline: false,
			headlineSelector: "[data-kt-pln-editor-title]",
		});

		const method = page.locator(`${ROOT} [data-kt-pln-field="procurement_method"]`);
		await method.selectOption("Restricted tender");
		await page.locator(`${ROOT} [data-kt-pln-field="method_override_grounds"]`).fill("");
		await page.locator(`${ROOT} [data-kt-pln-field="method_override_reason"]`).fill("");
		await page.locator(`${ROOT} [data-kt-pln-field="method_override_evidence"]`).fill("");
		await page.getByTestId("kt-pln-ui06-save-draft").click();

		const inlineError = page.locator(
			`${ROOT} [data-kt-field-error="method_override_grounds"]:not([hidden])`,
		);
		await expect(inlineError).toBeVisible({ timeout: 15_000 });
		await expect(
			page.locator(`${ROOT} [data-kt-field="method_override_grounds"]`),
		).toHaveClass(/kt-field-invalid/);
		await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);
		await expect(page.locator(".msgprint")).toHaveCount(0);
		await expect(page.locator("body")).not.toContainText("Value missing for");

		await page.getByTestId("kt-pln-ui06-ms_invitation_published").fill("2027-09-15");
		await page.getByTestId("kt-pln-ui06-ms_tender_opening").fill("2027-10-20");
		await page.getByTestId("kt-pln-ui06-ms_evaluation_completed").fill("2027-10-10");
		await page.getByTestId("kt-pln-ui06-ms_award_approval").fill("2027-12-15");
		await page.getByTestId("kt-pln-ui06-ms_contract_signature").fill("2028-01-15");
		await page.getByTestId("kt-pln-ui06-ms_delivery_completion").fill("2028-03-31");
		await page.getByTestId("kt-pln-ui06-save-draft").click();
		const msError = page.locator(
			`${ROOT} [data-kt-field-error="ms_evaluation_completed"]:not([hidden])`,
		);
		await expect(msError).toBeVisible({ timeout: 15_000 });
		await expect(msError).toContainText(/chronolog/i);
		await expect(
			page.getByTestId("kt-pln-ui06-ms_evaluation_completed"),
		).toHaveClass(/kt-field-invalid/);
		await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui06-ms_evaluation_completed")).toHaveValue(
			"2027-10-10",
		);

		await expect(page.locator(ROOT)).not.toContainText("Preference and reservation");
		await expect(page.getByTestId("kt-pln-ui06-pref-none")).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui06-pref-section")).toHaveCount(0);
		await expect(page.locator(ROOT)).toContainText("Strategy target");
		await expect(page.getByTestId("kt-pln-ui06-lotting-details")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui06-lotting-multiple")).toBeChecked();
		await page.getByTestId("kt-pln-ui06-lotting-single").check();
		await expect(page.getByTestId("kt-pln-ui06-lotting-details")).toBeHidden();
		await page.getByTestId("kt-pln-ui06-lotting-multiple").check();
		await expect(page.getByTestId("kt-pln-ui06-lotting-details")).toBeVisible();

		await page.getByTestId("kt-pln-ui06-request-finance").click();
		await expect(page.getByTestId("kt-pln-ui06-issue")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-pln-ui06-issue")).toContainText(
			/Confirm all milestone dates before requesting Finance confirmation/i,
		);
		await expect(page).toHaveURL(/procurement-plan-item-editor/);
		await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);

		const issue = page.getByTestId("kt-pln-ui06-issue");
		const issueBody = issue.locator("[data-kt-pln-editor-issue-copy]");
		if (await issue.isVisible()) {
			await expect(issueBody).not.toHaveText(/^Ready$/);
		}
		await expect(page.locator(ROOT)).not.toContainText("Statutory and strategy treatment");
		await expect(page.locator(ROOT)).not.toContainText("Statutory allocation treatment");
		await expect(page.locator(ROOT)).not.toContainText("Combine in this Plan Item");
		await expect(page.locator(ROOT)).not.toContainText("Keep separate");
		await expect(page.locator(`${ROOT} [name="aggregation_decision"]`)).toHaveCount(0);
		await expect(page.getByTestId("kt-pln-ui06-package-structure")).toHaveCount(0);
	});

	test("In review Plan Item shows why Save is blocked — no silent no-op", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05Approval(page);
		expect(prep.plan_item).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohPlanningOfficer(page);
		await page.goto(
			`/desk/procurement-plan-item-editor?plan_item=${encodeURIComponent(prep.plan_item || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${ROOT}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});
		await expect(page.getByTestId("kt-pln-ui06-issue")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-pln-ui06-issue")).toContainText(/In review/i);
		await expect(page.getByTestId("kt-pln-ui06-save-draft")).toHaveAttribute("hidden", "hidden");
		await expect(page.getByTestId("kt-pln-ui06-request-finance")).toHaveAttribute(
			"hidden",
			"hidden",
		);
		await expect(page.getByTestId("kt-pln-ui06-save-draft")).not.toBeInViewport();
		await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);
		await expect(page.locator(".msgprint")).toHaveCount(0);
	});
});
