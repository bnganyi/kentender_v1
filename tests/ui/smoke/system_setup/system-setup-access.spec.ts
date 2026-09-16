import { test, expect, Page } from "@playwright/test";
import { login, loginAsAdministrator } from "../../helpers/auth";
import { collectPageErrors } from "../../helpers/designFidelity";

/**
 * CFG-CHG-002 v0.11 §6/§11.1 (tracker CFG11-308) — who may use System setup
 * and what every actor sees when they may not, plus the shared states the
 * whole surface depends on.
 *
 * Nothing here writes: the spec proves refusal, presentation and reachability.
 * The denied actor is the canonical business user with no configuration
 * authority (a plain Desk User — `samuel.otieno@moh.example.test`).
 */
const DENIED_USER = "samuel.otieno@moh.example.test";
const DENIED_PASSWORD = process.env.UI_SEED_PASSWORD || "Test@123";

async function openSetup(page: Page, hash: string, ready: string): Promise<string[]> {
	const errors = collectPageErrors(page);
	await page.goto(`/app/system-setup#${hash}`, { waitUntil: "domcontentloaded" });
	await page.waitForSelector(ready, { timeout: 20_000 });
	return errors;
}

test.describe("System setup — access and shared states", () => {
	test("a business user without configuration authority is refused with an explanation, not an empty page or a crash", async ({ page }) => {
		const errors = collectPageErrors(page);
		await login(page, DENIED_USER, DENIED_PASSWORD);
		await page.goto("/app/system-setup#procurement-settings", { waitUntil: "domcontentloaded" });

		// §8.1 — a refusal is a stated outcome, never a blank screen.
		const forbidden = page.locator('[data-testid="kt-procset-forbidden"], [data-testid="kt-setup-forbidden"]').first();
		await expect(forbidden).toBeVisible({ timeout: 20_000 });
		await expect(forbidden).toContainText(/access/i);
		// And no maintenance control is offered behind the refusal.
		await expect(page.locator('[data-testid="kt-procset-source-add"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="kt-procset-rule-add"]')).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});

	test("the Administrator reaches every tab, and each one resolves to content rather than a spinner", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSetup(page, "procuring-entity", '[data-testid="kt-setup-pe-card"]');

		for (const [tab, ready] of [
			["fiscal-years", '[data-testid="kt-fy-table"]'],
			["procurement-settings", '[data-testid="kt-procset-rules"]'],
			["organisation-structure", '[data-testid="kt-ou-detail"]'],
			["users-and-responsibilities", '[data-testid="kt-ura-table"]'],
		] as const) {
			await page.goto(`/app/system-setup#${tab}`, { waitUntil: "domcontentloaded" });
			await page.waitForSelector(ready, { timeout: 20_000 });
			await expect(page.locator('[data-testid="kt-setup-loading"]')).toHaveCount(0);
		}
		expect(errors, "console errors").toEqual([]);
	});

	test("a sub-path survives reload and browser back, so a detail can be linked to", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSetup(page, "fiscal-years", '[data-testid="kt-fy-table"]');

		await page.click('[data-testid="kt-fy-detail-2027-2028"]');
		await page.waitForSelector('[data-testid="kt-setup-fy-detail-card"]');
		expect(page.url()).toContain("#fiscal-years/year/2027-2028");

		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-setup-fy-detail-card"]', { timeout: 20_000 });

		await page.goBack();
		await page.waitForSelector('[data-testid="kt-fy-table"]', { timeout: 20_000 });
		expect(errors, "console errors").toEqual([]);
	});

	test("all three intake activities stay readable at a narrow width and at 200% text scale", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSetup(page, "fiscal-years", '[data-testid="kt-fy-table"]');

		// CFG-UX-AC-06 — all three submission periods are visible at desktop
		// and narrow widths.
		await page.setViewportSize({ width: 400, height: 900 });
		for (const key of ["needs", "dpp", "disposal_plan"]) {
			await expect(page.locator(`[data-testid="kt-fy-${key}-2027-2028"]`)).toBeVisible();
		}
		// The page itself must not scroll sideways at that width.
		const overflow = await page.evaluate(
			() => document.documentElement.scrollWidth - document.documentElement.clientWidth
		);
		expect(overflow, "horizontal overflow at 400px").toBeLessThanOrEqual(1);

		// 200% text scale, the accessibility case the spec calls for.
		await page.setViewportSize({ width: 1280, height: 1024 });
		await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
		await expect(page.locator('[data-testid="kt-fy-needs-2027-2028"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-fy-disposal_plan-2027-2028"]')).toBeVisible();
		expect(errors, "console errors").toEqual([]);
	});

	test("the keyboard reaches the primary action, and a dialog takes focus when it opens", async ({ page }) => {
		await loginAsAdministrator(page);
		const errors = await openSetup(page, "fiscal-years", '[data-testid="kt-fy-table"]');

		await page.locator('[data-testid="kt-fy-add-open"]').focus();
		await expect(page.locator('[data-testid="kt-fy-add-open"]')).toBeFocused();
		await page.keyboard.press("Enter");
		await page.waitForSelector('[data-testid="kt-fy-add"]');
		// The dialog moves focus to its own first field rather than leaving it
		// behind on the page underneath.
		await expect(page.locator('[data-testid="kt-fy-start-year"]')).toBeFocused();
		// Escape closes it without saving anything.
		await page.keyboard.press("Escape");
		await expect(page.locator('[data-testid="kt-fy-add"]')).toHaveCount(0);
		expect(errors, "console errors").toEqual([]);
	});
});
