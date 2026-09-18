import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUDITOR,
	AUTHOR,
	OUTSIDER,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.18 (PLN18-305) — the Plan Item editor's (U09) own real
 * commands and their interactive re-render: saving Package details and the
 * baseline, declaring a Direct Procurement condition's evidence, dissolving
 * a mutable item back to its Plan, per-role access, and the RUN-CHG-001
 * stale-save race (ported verbatim from the deleted v1.12
 * `planning-plan-item-stale-save.spec.ts` — the regression it guards against
 * is unrelated to this row's own five-section restructuring). Structural/
 * copy fidelity against U09's own frames lives in
 * `design-fidelity/planning-fidelity.spec.ts` — this file does not re-assert
 * landmark order or exact prose.
 */

type PlanItemState = { plan_item_id: string; plan_reference: string };

// Sequential, but not serial: these run on one worker because the fixtures
// are one shared world, and each test rebuilds its own. Aborting the rest of
// the file because one test failed hides every other result behind it.
test.describe.configure({ timeout: 180_000 });

test.describe("PLN18-305 Plan Item editor", () => {
	test.afterAll(() => restoreSite());

	test("planner saves Package details and the baseline schedule recomputes", async ({ page }) => {
		const state = resetFixture<PlanItemState>("reset_plan_item_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");

		await page.locator('[data-testid="ppi-estimate-basis"]').fill("Market survey of the current supplier panel including delivery and installation costs.");
		await page.locator('[data-testid="ppi-basis-reference"]').fill("MS-2098-001");
		// The Planner sets the target invitation date; the departmental
		// deadline beside it is derived from the sources and is read-only.
		await page.locator('[data-testid="ppi-invitation"]').fill("2098-11-01");
		await page.locator('[data-testid="ppi-reservation"]').selectOption("Youth");
		await page.locator('[data-testid="ppi-save"]').click();
		await expect(page.locator('[data-testid="ppi-save"]')).toBeEnabled({ timeout: 10_000 });
		await expect(page.locator('[data-testid="ppi-error"]')).toHaveCount(0);

		const dates = page.locator('[data-testid="ppi-milestones"] tbody tr').first().locator("td").nth(1);
		await expect(dates).toHaveText("1 Nov 2098");
		await expect(page.locator('[data-testid="ppi-boundary"]')).toHaveCount(0);

		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await expect(page.locator('[data-testid="ppi-basis-reference"]')).toHaveValue("MS-2098-001");
		await expect(page.locator('[data-testid="ppi-reservation"]')).toHaveValue("Youth");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("planner declares a Direct Procurement condition's evidence and Conditions becomes Complete", async ({ page }) => {
		const state = resetFixture<PlanItemState>("reset_plan_item_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");

		await page.locator('[data-testid="ppi-method"]').selectOption("Direct Procurement");
		await page.locator('[data-testid="ppi-save"]').click();
		await expect(page.locator('[data-testid="ppi-save"]')).toBeEnabled({ timeout: 10_000 });
		await expect(page.locator('[data-testid="ppi-rule-evidence"]')).toContainText("Evidence required");

		await page.locator('[data-testid="ppi-evidence-CIRCUMSTANCES"]').fill("Sole supplier holds the exclusive distribution rights for this equipment.");
		await page.locator('[data-testid="ppi-authorisation-CIRCUMSTANCES"]').fill("AO/2098/DP/1");
		await page.locator('[data-testid="ppi-save"]').click();
		await expect(page.locator('[data-testid="ppi-save"]')).toBeEnabled({ timeout: 10_000 });
		await expect(page.locator('[data-testid="ppi-rule-evidence"]')).toContainText("Declared");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("planner dissolves a mutable item and returns to its Annual Plan", async ({ page }) => {
		const state = resetFixture<PlanItemState>("reset_plan_item_fixture");
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");

		await page.locator('[data-testid="ppi-remove"]').click();
		await expectReady(page, "plan");
		await expect(page).toHaveURL(new RegExp(`annual-procurement-plan/${state.plan_reference}`));
	});

	test("auditor reads with no editing, save or dissolve controls", async ({ page }) => {
		const state = resetFixture<PlanItemState>("reset_plan_item_fixture");
		await login(page, AUDITOR, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await expect(page.locator('[data-testid="ppi-save"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="ppi-remove"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="ppi-title"]')).toBeDisabled();
	});

	test("a departmental Author has no route to the Plan Item editor", async ({ page }) => {
		const state = resetFixture<PlanItemState>("reset_plan_item_fixture");
		await login(page, AUTHOR, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await expect(page.locator('[data-testid="pln-error"] h3')).toHaveText("This record isn't available to you");
	});

	test("an unrelated Author (Outsider) is masked the same way", async ({ page }) => {
		const state = resetFixture<PlanItemState>("reset_plan_item_fixture");
		await login(page, OUTSIDER, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${state.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await expect(page.locator('[data-testid="pln-error"] h3')).toHaveText("This record isn't available to you");
	});

	/**
	 * RUN-CHG-001 — ported verbatim from the deleted v1.12
	 * `planning-plan-item-stale-save.spec.ts`. Regression (latent, confirmed
	 * by the 2026-09-11 cross-module survey): `onSavePlanItem()` awaited
	 * `run()` and only afterwards, outside it, awaited `load({ quiet: true })`
	 * — the reload that refreshes `planItem.value.record_version`. `run()`'s
	 * `finally` cleared `pending` (and so re-enabled "Save draft") as soon as
	 * `savePlanItem` itself returned, before that reload had landed. A second
	 * Save fired in that window would have read the pre-save `record_version`
	 * and been refused as a stale write. The fix moves the reload to be the
	 * last thing awaited inside the function passed to `run()`. This test
	 * widens the reload window so the old behaviour cannot pass.
	 */
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
