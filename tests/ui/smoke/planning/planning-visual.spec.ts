import { test, expect } from "@playwright/test";

import { login } from "../../helpers/auth";
import { collectConsoleErrors, expectReady, gotoPlanning, resetFixture, restoreSite } from "./helpers";

/**
 * Visual references for the Procurement Planning screens, at the 1440 × 1024
 * the artboards are drawn at.
 *
 * The structural gate beside this one compares containers and nesting, and the
 * landmark gate compares copy. Neither sees spacing, rhythm or a rule that
 * stopped rendering — which is how "the page reads as unstructured" reached
 * the owner as a screenshot rather than as a failing test (24 Sep 2026).
 *
 * Settings are the Departmental Needs suite's, and for its reasons, which were
 * established by measurement:
 *
 * - `maxDiffPixels` is an **absolute** budget, not a ratio. A ratio scales with
 *   the shot, so a real but local change disappears into a full-screen
 *   denominator: measured there, `letter-spacing: 4px` on a page title moves
 *   901 pixels while a whole-card colour change moves 255,219. 300 sits below
 *   a one-heading change and above cross-machine antialiasing.
 * - `mask` covers the rail's signed-in identity and every `[data-volatile]`
 *   value — audit instants are fixture-build time and differ on every run.
 *
 * Deliberately few: a baseline per screen state is churn without coverage. One
 * shot per principal screen, in the state the board draws.
 */

const SHOT = { maxDiffPixels: 300, animations: "disabled" as const };

function chrome(page: import("@playwright/test").Page) {
	return { ...SHOT, mask: [page.locator(".kt-rail-mount"), page.locator("[data-volatile]")] };
}

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.use({ viewport: { width: 1440, height: 1024 } });

test.describe("Procurement Planning — visual references", () => {
	test.afterAll(() => restoreSite());

	test("U01 — the planning workspace", async ({ page }) => {
		resetFixture("reset_workspace_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, process.env.UI_PLN_PLANNER || "mercy.kilonzo@moh.example.test", process.env.UI_PLN_PASSWORD || "Test@123");
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page).toHaveScreenshot("pln-u01-workspace.png", chrome(page));
		expect(errors, "console errors").toEqual([]);
	});

	test("U07 — annual plan preparation", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_plan_item_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, process.env.UI_PLN_PLANNER || "mercy.kilonzo@moh.example.test", process.env.UI_PLN_PASSWORD || "Test@123");
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`);
		await expectReady(page, "plan");
		await expect(page).toHaveScreenshot("pln-u07-annual-plan.png", chrome(page));
		expect(errors, "console errors").toEqual([]);
	});
});
