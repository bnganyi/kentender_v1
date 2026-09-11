import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { PASSWORD, PLANNER, collectConsoleErrors, expectReady, resetFixture, restoreSite } from "./helpers";

/**
 * RUN-CHG-001 — Procurement Planning's Plan Item editor
 * (docs/mvp-1-r1/00_common/KenTender_RUN-CHG-001_Shared_Command_Runner_v1.0.md).
 *
 * Regression (latent, confirmed by the 2026-09-11 cross-module survey):
 * `onSavePlanItem()` awaited `run()` and only afterwards, outside it, awaited
 * `load({ quiet: true })` — the reload that refreshes `planItem.value
 * .record_version`. `run()`'s `finally` cleared `pending` (and so re-enabled
 * "Save draft") as soon as `savePlanItem` itself returned, before that
 * reload had landed. A second Save fired in that window would have read the
 * pre-save `record_version` and been refused as a stale write. The fix moves
 * the reload to be the last thing awaited inside the function passed to
 * `run()`. This test widens the reload window so the old behaviour cannot
 * pass.
 */
type PlanItemState = { plan_item_id: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Procurement Planning — Plan Item stale-save race", () => {
	test.afterAll(() => restoreSite());

	test("a second Save right after the first is not refused as a stale write", async ({ page }) => {
		const state = resetFixture<PlanItemState>("reset_plan_item_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.setViewportSize({ width: 1440, height: 1024 });
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");

		// The reload that repopulates record_version now lands 1.5s after the
		// save it follows.
		await page.route("**/api/method/kentender_procurement.procurement_planning.api.get_plan_item", async (route) => {
			const response = await route.fetch();
			await new Promise((resolve) => setTimeout(resolve, 1500));
			await route.fulfill({ response });
		});

		const titleField = page.locator('[data-testid="ppi-title"]');
		const save = page.locator('[data-testid="ppi-save"]');
		const pageTitle = page.locator(".kt-page-title");

		// The value must genuinely differ from whatever the shared dev site
		// currently holds, or the server sees no change for an unrelated,
		// correct reason — use a fresh stamp each run.
		const stamp = Date.now();
		await titleField.fill(`Digital health infrastructure package ${stamp}`);
		await save.click();

		// Old behaviour: `pending` (and so the Save button) would already have
		// cleared well inside the 1.5s reload delay.
		await expect(save).toBeDisabled();
		await page.waitForTimeout(800);
		await expect(save).toBeDisabled();
		await expect(pageTitle).toHaveText(`Digital health infrastructure package ${stamp}`, { timeout: 10_000 });
		await expect(save).toBeEnabled({ timeout: 10_000 });
		await expect(page.locator('[data-testid="ppi-error"]')).toHaveCount(0);

		// A second, genuinely different edit right after the first save's
		// reload has landed must be accepted, not refused as a stale write —
		// and the first edit must not have been silently reverted.
		await titleField.fill(`Digital health infrastructure package ${stamp} v2`);
		await save.click();
		await expect(save).toBeDisabled({ timeout: 10_000 });
		await expect(pageTitle).toHaveText(`Digital health infrastructure package ${stamp} v2`, { timeout: 10_000 });
		await expect(save).toBeEnabled({ timeout: 10_000 });
		await expect(page.locator('[data-testid="ppi-error"]')).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
