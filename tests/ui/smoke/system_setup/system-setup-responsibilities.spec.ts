import { test, expect, Page } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";
import { resetResponsibilities, restoreSite, systemManager, type ResponsibilitiesWorld } from "./helpers";

/**
 * CFG-CHG-002 v0.14 D24 — the AUTH-owned tabs re-ported from
 * C05-Organisation-Structure / C06-Users-Responsibilities, in a real browser.
 * Structure is the fidelity gate's job; this proves the journeys AUTH v1.9
 * §13.5–13.8 describe: assign an Acting responsibility that has not started,
 * land on it by its own link, change it before it starts (one history event,
 * a line per changed field), revoke it; the unit link in Organisation
 * structure; the ambiguous-structure state; a failed read; the second setup
 * role; the narrow layout.
 *
 * Writes: responsibilities for one fixture user (reset_responsibilities),
 * removed with the user by restoreSite.
 */
const SERVER = { timeout: 20_000 };

function hash(page: Page): string {
	return decodeURIComponent(new URL(page.url()).hash);
}

async function open(page: Page, fragment: string, ready: string): Promise<string[]> {
	const errors = collectPageErrors(page);
	await page.goto(`/app/system-setup#${fragment}`, { waitUntil: "domcontentloaded" });
	await page.waitForSelector(ready, SERVER);
	return errors;
}

async function noFrappeMessage(page: Page): Promise<void> {
	await expect(page.locator(".modal.show .modal-title")).toHaveCount(0);
}

test.describe.serial("System setup — Users and responsibilities, Organisation structure", () => {
	let world: ResponsibilitiesWorld;
	test.beforeAll(() => {
		world = resetResponsibilities();
	});
	test.afterAll(() => restoreSite());

	test("assign an Acting responsibility, open it by its link, change it before it starts, then revoke it", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await open(page, "users-and-responsibilities", '[data-testid="kt-ura-table"]');

		const trigger = page.locator('[data-testid="kt-ura-assign-open"]');
		await trigger.click();
		const dialog = page.locator('[data-testid="kt-ura-assign"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Assign responsibility");
		await expect(page.locator("#kt-assign-user")).toBeFocused();
		await page.fill("#kt-assign-user", "Playwright Grantee");
		await dialog.locator(".kt-matches button", { hasText: world.user }).click();
		await expect(page.locator('[data-testid="kt-ura-user-picked"]')).toHaveValue(`${world.full_name} · ${world.user}`);
		await page.selectOption('[data-testid="kt-ura-role"]', "Departmental Author");
		await page.click('[data-testid="kt-ura-ou-toggle"]');
		await page.click(`[data-testid="kt-ura-ou-option-${world.unit}"]`);
		await dialog.locator("label.kt-seg-opt", { hasText: "Acting" }).click();
		await expect(page.locator('[data-testid="kt-ura-appointment-acting"]')).toBeChecked();
		// The primary stays off, saying why, until the server says the form is whole.
		await expect(page.locator('[data-testid="kt-ura-assign-confirm"]')).toBeDisabled();
		await expect(page.locator('[data-testid="kt-ura-blocked"]')).toBeVisible();
		await page.fill('[data-testid="kt-ura-from"]', "2026-12-01");
		await page.fill('[data-testid="kt-ura-to"]', "2026-12-31");
		await page.fill('[data-testid="kt-ura-authority"]', "PW/ACT/2026/001");
		await expect(page.locator('[data-testid="kt-ura-summary"]')).toContainText(`${world.full_name} will be Departmental Author for ${world.unit_name}`, SERVER);
		await expect(page.locator('[data-testid="kt-ura-assign-confirm"]')).toBeEnabled(SERVER);
		await page.click('[data-testid="kt-ura-assign-confirm"]');

		// Lands on the new responsibility, by its own link.
		await page.waitForSelector('[data-testid="kt-ura-detail"]', SERVER);
		expect(hash(page)).toMatch(/^#users-and-responsibilities\/[^/]+$/);
		const link = hash(page);
		await expect(page.locator('[data-testid="kt-ura-detail-status"]')).toHaveText("Scheduled");
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-ura-detail-status"]')).toHaveText("Scheduled", SERVER);
		expect(hash(page)).toBe(link);

		// Change it before it starts: one history event, a line per field.
		await page.click('[data-testid="kt-ura-open-edit"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Edit scheduled assignment");
		await expect(page.locator('[data-testid="kt-ura-edit-notice"]')).toContainText("Clear Effective from to bring it into force now.");
		await page.fill('[data-testid="kt-ura-to"]', "2027-01-31");
		await expect(page.locator('[data-testid="kt-ura-assign-confirm"]')).toBeEnabled(SERVER);
		await page.click('[data-testid="kt-ura-assign-confirm"]');
		await expect(dialog).toHaveCount(0, SERVER);
		const changed = page.locator('[data-testid="kt-ura-history"] tbody tr', { hasText: "Scheduled assignment changed" });
		await expect(changed).toHaveCount(1, SERVER);
		await expect(changed.locator(".kt-ura-change")).toHaveCount(1);
		await expect(changed.locator(".kt-ura-change")).toContainText("Effective to:");
		await expect(changed.locator(".kt-ura-change")).toContainText("31 Jan 2027");
		await expect(page.locator('[data-testid="kt-ura-open-edit"]')).toBeFocused();

		// Revoke: a reason is required; afterwards nothing can be done to it.
		await page.click('[data-testid="kt-ura-open-revoke"]');
		await expect(page.locator('[data-testid="kt-ura-revoke-confirm"]')).toBeDisabled();
		await page.fill('[data-testid="kt-ura-revoke-reason"]', "Playwright journey: the acting period was cancelled.");
		await page.click('[data-testid="kt-ura-revoke-confirm"]');
		await expect(page.locator('[data-testid="kt-ura-detail-status"]')).toHaveText("Revoked", SERVER);
		await expect(page.locator('[data-testid="kt-ura-open-edit"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-ura-open-revoke"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-ura-history"]')).toContainText("Responsibility revoked");

		// Edit and revoke change the record, not the link: one Back returns.
		await page.goBack();
		await page.waitForSelector('[data-testid="kt-ura-table"]', SERVER);
		await noFrappeMessage(page);
		expect(errors, "console errors").toEqual([]);
	});

	test("a unit opens by its own link, and reload and Back follow it", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await open(page, "organisation-structure", '[data-testid="kt-ou-detail"]');
		await page.locator(".kt-org-tree-host .tree-link", { hasText: "Human Resources" }).click();
		await expect(page.locator('[data-testid="kt-ou-detail"] h3')).toHaveText("Human Resources Management and Development", SERVER);
		const link = hash(page);
		expect(link).toMatch(/^#organisation-structure\/[^/]+$/);
		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-ou-detail"] h3')).toHaveText("Human Resources Management and Development", SERVER);
		await page.goBack();
		await expect(page.locator('[data-testid="kt-ou-detail"] h3')).toHaveText("Ministry of Health", SERVER);
		expect(errors, "console errors").toEqual([]);
	});

	test("an ambiguous structure lists the conflicts and offers no repair", async ({ page }) => {
		await loginAsAdministrator(page);
		await page.route("**/api/method/kentender_core.api.organisation_structure_api.get_organisation_structure", (route) =>
			route.fulfill({ json: { message: { state: "ambiguous", tree: [], conflicts: ["More than one top-level organisation unit: Ministry of Health (PE-MOH), Stray (OU-X)."] } } })
		);
		await open(page, "organisation-structure", '[data-testid="kt-org-ambiguous"]');
		await expect(page.locator('[data-testid="kt-org-ambiguous"]')).toContainText("The organisation structure cannot be repaired automatically.");
		await expect(page.locator('[data-testid="kt-org-conflicts"] li')).toHaveText(["More than one top-level organisation unit: Ministry of Health (PE-MOH), Stray (OU-X)."]);
		await expect(page.locator('[data-testid="kt-org-repair"]')).toHaveCount(0);
	});

	test("a failed register read shows the error state, and Try again recovers", async ({ page }) => {
		await loginAsAdministrator(page);
		const url = "**/api/method/kentender_core.api.responsibility_api.list_user_responsibilities";
		await page.route(url, (route) => route.fulfill({ status: 500, json: { exc_type: "Exception" } }));
		await page.goto("/app/system-setup#users-and-responsibilities", { waitUntil: "domcontentloaded" });
		await expect(page.locator('[data-testid="kt-ura-error"]')).toContainText("Responsibilities could not be loaded", SERVER);
		await expect(page.locator('[data-testid="kt-ura-table"]')).toHaveCount(0);
		await noFrappeMessage(page);
		await page.unroute(url);
		await page.click('[data-testid="kt-ura-retry"]');
		await page.waitForSelector('[data-testid="kt-ura-table"]', SERVER);
	});

	test("a System Manager reaches the register and may assign", async ({ page }) => {
		const manager = systemManager();
		await login(page, manager.user, manager.password);
		const errors = await open(page, "users-and-responsibilities", '[data-testid="kt-ura-table"]');
		await expect(page.locator('[data-testid="kt-ura-assign-open"]')).toBeVisible();
		expect(errors, "console errors").toEqual([]);
	});

	test("at 400px the detail stays inside the page", async ({ page }) => {
		await page.setViewportSize({ width: 400, height: 900 });
		await loginAsAdministrator(page);
		await open(page, "users-and-responsibilities", '[data-testid="kt-ura-table"]');
		await page.locator('[data-testid^="kt-ura-view-"]').first().click();
		await page.waitForSelector('[data-testid="kt-ura-detail"]', SERVER);
		const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
		expect(overflow).toBeLessThanOrEqual(1);
	});
});
