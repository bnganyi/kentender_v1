import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";
import { asEmpty, asFirstRun, resetWorld, restoreSite } from "./helpers";

/**
 * CFG-CHG-002 v0.14 §10.1 (tracker CFG14-401) — each fixture world puts the
 * page in the state its name promises, so the Phase 5 screen specs can rely
 * on them. This checks the worlds, not the screens' fidelity (that is the
 * fidelity gate's job): what must be reachable, and what must be absent.
 */
test.describe.serial("System setup — fixture worlds", () => {
	test.afterAll(() => restoreSite());

	test("CONFIG-FIRST: only Procuring entity is available and it asks to configure the site", async ({ page }) => {
		const errors = collectPageErrors(page);
		await loginAsAdministrator(page);
		await asFirstRun(page);
		await page.goto("/app/system-setup#fiscal-years", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-setup-pe-card"]')).toContainText("Configure this site", { timeout: 20_000 });
		// A link to a tab first run does not allow lands on the entity instead.
		await expect.poll(() => new URL(page.url()).hash).toBe("#procuring-entity");
		for (const tab of ["fiscal-years", "organisation-structure", "users-and-responsibilities", "procurement-settings"]) {
			await expect(page.locator(`[data-testid="kt-setup-tab-${tab}"]`)).toBeDisabled();
		}
		await expect(page.locator('[data-testid="kt-setup-pe-code"]')).toBeEditable();
		expect(errors, "console errors").toEqual([]);
	});

	test("CONFIG-EMPTY: empty lists render their own empty states, never an empty successful table", async ({ page }) => {
		await loginAsAdministrator(page);
		await asEmpty(page, { years: true, fundingSources: true, rules: true });
		await page.goto("/app/system-setup#fiscal-years", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-fy-empty"]')).toBeVisible({ timeout: 20_000 });
		await expect(page.locator('[data-testid^="kt-fy-row-"]')).toHaveCount(0);
		await page.goto("/app/system-setup#procurement-settings", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-procset-sources-empty"]')).toBeVisible({ timeout: 20_000 });
		// Each Procurement settings section is its own view.
		await page.click('[data-testid="kt-procset-link-procurement-rules"]');
		await expect(page.locator('[data-testid="kt-procset-rules-empty"]')).toBeVisible();
	});

	test("CONFIG: disposal plans are closed and the other two activities open for the upcoming year", async ({ page }) => {
		const world = resetWorld("reset_config");
		expect(world.disposal_plan_submission).toBeNull();
		await loginAsAdministrator(page);
		await page.goto(`/app/system-setup#fiscal-years/${world.fiscal_year_open}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-fy-activity-disposal_plan"]')).toContainText("Closed", { timeout: 20_000 });
		await expect(page.locator('[data-testid="kt-fy-activity-needs"]')).toContainText("Open");
		await expect(page.locator('[data-testid="kt-fy-activity-dpp"]')).toContainText("Open");
	});

	test("CONFIG-SWAP: departmental plans are open for the current year and closed for the upcoming one", async ({ page }) => {
		const world = resetWorld("reset_config_swap");
		expect(world.dpp_submission?.fiscal_year).toBe(world.fiscal_year_current);
		await loginAsAdministrator(page);
		await page.goto(`/app/system-setup#fiscal-years/${world.fiscal_year_current}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-fy-activity-dpp"]')).toContainText("Open", { timeout: 20_000 });
		await page.goto(`/app/system-setup#fiscal-years/${world.fiscal_year_open}`, { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-fy-activity-dpp"]')).toContainText("Closed", { timeout: 20_000 });
	});
});
