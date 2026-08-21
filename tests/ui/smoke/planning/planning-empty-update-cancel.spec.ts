import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { loginAsMohPlanningOfficer } from "../../helpers/planningRoles";

test("PLN-UI-05B cancels an empty successor and returns to the Approved Plan", async ({ page }) => {
	await loginAsAdministrator(page);
	await page.goto("/desk", { waitUntil: "domcontentloaded" });
	const prep = await page.evaluate(async () => {
		const response = await (window as any).frappe.call({
			method: "kentender_procurement.procurement_planning.api.prepare_planning_empty_update_ui",
		});
		return response.message || {};
	});
	expect(prep.ok).toBeTruthy();
	await page.context().clearCookies();
	await loginAsMohPlanningOfficer(page);
	await page.goto(`/desk/procurement-plan-builder?plan=${encodeURIComponent(prep.plan)}`, { waitUntil: "domcontentloaded" });
	await expect(page.locator('[data-testid="kt-pln-ui03-root"][data-kt-pln-live="1"]')).toBeVisible({ timeout: 45_000 });
	await page.locator('[data-kt-pln-action="cancel-update"]').click();
	const dialog = page.getByRole("dialog", { name: "Cancel empty Plan update?" });
	await expect(dialog).toBeVisible();
	await expect(dialog).toContainText("Current Approved Version");
	await expect(dialog).toContainText("Effective changes");
	await expect(dialog).toContainText("0");
	await page.getByRole("button", { name: "Cancel empty update" }).click();
	await expect(page).toHaveURL(/\/desk\/procurement-plan-approved/, { timeout: 30_000 });
	await expect(page.locator('[data-testid="kt-pln-ui09-root"][data-kt-pln-live="1"]')).toBeVisible({ timeout: 45_000 });
});
