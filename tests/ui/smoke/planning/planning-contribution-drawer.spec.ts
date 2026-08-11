import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	loginAsMohHod,
	preparePlanningGate05,
} from "../../helpers/planningRoles";

const BUILDER = '[data-testid="kt-pln-ui05-root"], [data-testid="kt-pln-ui03-root"]';
const DRAWER = '[data-testid="kt-pln-ui07-root"]';

test.describe("PLN-UI-07 Departmental contribution drawer", () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
	});

	test("HoD opens drawer, sees inline declaration error, then submits", async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const prep = await preparePlanningGate05(page);
		expect(prep.empty_draft_plan).toBeTruthy();
		expect(prep.hod_user).toBeTruthy();
		await page.context().clearCookies();
		await loginAsMohHod(page, prep.hod_user);
		await page.goto(
			`/desk/procurement-plan-builder?plan=${encodeURIComponent(prep.empty_draft_plan || "")}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator(`${BUILDER}[data-kt-pln-live="1"]`)).toBeVisible({
			timeout: 45_000,
		});

		const submit = page.getByTestId("kt-pln-ui05-submit-dept");
		await expect(submit).toBeEnabled({ timeout: 15_000 });
		await submit.click();

		await expect(page.locator(`${DRAWER}:not([hidden])`)).toBeVisible({
			timeout: 15_000,
		});
		await expect(page.getByText("Submit departmental contribution")).toBeVisible();
		await expect(page.getByText("Included Items")).toBeVisible();
		await expect(page.getByTestId("kt-pln-ui07-footer")).toBeVisible();
		const confirm = page.getByTestId("kt-pln-ui07-confirm");
		await expect(confirm).toBeVisible();
		const confirmBorder = await confirm.evaluate((el) => getComputedStyle(el).border);
		expect(confirmBorder.toLowerCase()).not.toContain("outset");
		await expect(page.getByTestId("kt-pln-ui05-submit-dept")).toContainText(/Submit for sign-off/i);
		await expect(page.getByTestId("kt-pln-ui03-lifecycle")).toHaveText(/Draft/i);

		await page.getByTestId("kt-pln-ui07-confirm").click();
		const inlineError = page.locator(
			`${DRAWER} [data-kt-field-error="declaration"]:not([hidden])`,
		);
		await expect(inlineError).toBeVisible({ timeout: 10_000 });
		await expect(page.getByRole("dialog", { name: /^Message$/i })).toHaveCount(0);
		await expect(page.locator(".msgprint")).toHaveCount(0);

		await page.getByTestId("kt-pln-ui07-declaration").check();
		await page.getByTestId("kt-pln-ui07-note").fill("Signed off for consolidation");
		await page.getByTestId("kt-pln-ui07-confirm").click();

		await expect(page.locator(`${DRAWER}[hidden], ${DRAWER}.hidden`)).toBeAttached({
			timeout: 15_000,
		});
		await expect(page.locator(BUILDER)).toContainText("Submitted", { timeout: 15_000 });
	});
});
