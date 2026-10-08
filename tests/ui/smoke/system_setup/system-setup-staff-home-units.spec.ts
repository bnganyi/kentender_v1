import { test, expect, Page } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";
import { resetResponsibilities, restoreSite, type ResponsibilitiesWorld } from "./helpers";

/**
 * AUTH-ADR-001 v1.12 §12, §13.12–13.13, §14.7 and CFG-CHG-002 v0.19 §11.1 —
 * the Staff home units tab of Users and responsibilities, in a real browser:
 * it opens by its own link and survives reload and Back; a person with no
 * home unit reads Not recorded; setting one through the dialog shows it in
 * the register and clears the Not recorded filter for that person; clearing it
 * puts the person back. A home unit grants nothing, so the register has no
 * responsibility column.
 *
 * Writes: one fixture user (reset_responsibilities), removed by restoreSite.
 */
const SERVER = { timeout: 20_000 };

function hash(page: Page): string {
	return decodeURIComponent(new URL(page.url()).hash);
}

test.describe.serial("System setup — Staff home units", () => {
	let world: ResponsibilitiesWorld;
	test.beforeAll(() => {
		world = resetResponsibilities();
	});
	test.afterAll(() => restoreSite());

	test("opens by its link, sets and clears a home unit, and keeps its place on reload and Back", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = collectPageErrors(page);
		await page.goto("/app/system-setup#users-and-responsibilities/staff-home-units", { waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-home-table"]', SERVER);
		expect(hash(page)).toBe("#users-and-responsibilities/staff-home-units");
		await expect(page.locator('[data-testid="kt-ura-tab-staff-home-units"]')).toHaveAttribute("aria-selected", "true");
		await expect(page.locator('[data-testid="kt-home-table"] thead th')).toHaveText(["Staff member", "Home organisation unit", "Action"]);

		// The fixture user has no home unit: Not recorded, with the Set action.
		await page.fill('[data-testid="kt-home-search"]', world.user);
		const row = page.locator(`[data-testid="kt-home-row-${world.user}"]`);
		await expect(row).toBeVisible(SERVER);
		await expect(page.locator(`[data-testid="kt-home-unit-${world.user}"]`)).toHaveText("Not recorded");
		await expect(page.locator(`[data-testid="kt-home-edit-${world.user}"]`)).toHaveText("Set home unit");

		// AUTH-DES-11: set it. Nothing about a responsibility is asked or shown.
		await page.locator(`[data-testid="kt-home-edit-${world.user}"]`).click();
		const dialog = page.locator('[data-testid="kt-home-unit-dialog"]');
		await expect(dialog.locator(".dialog-title")).toHaveText("Set home unit");
		await expect(dialog).toContainText("This records where the person works. It does not grant any responsibility or access.");
		await expect(dialog.locator('[data-testid="kt-home-unit-clear"]')).toHaveCount(0);
		const options = await dialog.locator('[data-testid="kt-home-unit-select"] option').allTextContents();
		const label = options.find((o) => o.endsWith(world.unit_name));
		expect(label, `a unit named ${world.unit_name} among ${options.join(" | ")}`).toBeTruthy();
		await dialog.locator('[data-testid="kt-home-unit-select"]').selectOption({ label });
		await dialog.locator('[data-testid="kt-home-unit-save"]').click();
		await expect(dialog).toHaveCount(0, SERVER);
		await expect(page.locator(`[data-testid="kt-home-unit-${world.user}"]`)).toHaveText(world.unit_name);
		await expect(page.locator(`[data-testid="kt-home-edit-${world.user}"]`)).toHaveText("Change");

		// Reload keeps the tab and the person; Back returns to the register of responsibilities.
		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-home-table"]', SERVER);
		expect(hash(page)).toBe("#users-and-responsibilities/staff-home-units");
		await page.locator('[data-testid="kt-ura-tab-responsibilities"]').click();
		await page.waitForSelector('[data-testid="kt-ura-table"]', SERVER);
		expect(hash(page)).toBe("#users-and-responsibilities");
		await page.goBack();
		await page.waitForSelector('[data-testid="kt-home-table"]', SERVER);
		expect(hash(page)).toBe("#users-and-responsibilities/staff-home-units");
		await page.goForward();
		await page.waitForSelector('[data-testid="kt-ura-table"]', SERVER);

		// Clear it: the person is Not recorded again, and appears under that filter.
		await page.goBack();
		await page.waitForSelector('[data-testid="kt-home-table"]', SERVER);
		await page.fill('[data-testid="kt-home-search"]', world.user);
		await page.locator(`[data-testid="kt-home-edit-${world.user}"]`).click();
		await expect(page.locator("#kt-home-unit-title")).toHaveText("Change home unit");
		await page.locator('[data-testid="kt-home-unit-clear"]').click();
		await expect(page.locator('[data-testid="kt-home-unit-dialog"]')).toHaveCount(0, SERVER);
		await expect(page.locator(`[data-testid="kt-home-unit-${world.user}"]`)).toHaveText("Not recorded");
		await page.selectOption('[data-testid="kt-home-filter"]', "not-recorded");
		await expect(page.locator(`[data-testid="kt-home-row-${world.user}"]`)).toBeVisible(SERVER);

		await expect(page.locator(".modal.show .modal-title")).toHaveCount(0);
		expect(errors, `page errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
