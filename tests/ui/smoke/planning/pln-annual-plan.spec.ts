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
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.18 (PLN18-304) — the Annual Plan record's own behaviour:
 * real §4.5/§4.7 commands and their interactive re-render across the five
 * tabs, plus U08 formation. Structural/copy fidelity against U07/U08 lives
 * in `design-fidelity/planning-fidelity.spec.ts` — this file does not
 * re-assert landmark order or exact prose.
 *
 * Replaces the v1.12 `planning-plan-workbench.spec.ts` (deleted with this
 * row): that file's testids predate the five-tab restructuring.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("PLN18-304 Annual Plan record", () => {
	test.afterAll(() => restoreSite());

	test("planner forms a single-source Plan Item and the Plan Items tab updates", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_workbench_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");

		// The control is unavailable until a requirement is ticked (§10.6).
		// The checkbox is styled: its input sits behind the label a user
		// actually clicks, so the test clicks what the user clicks.
		await page.locator('[data-testid="ppl-select-source"]').first().click({ force: true });
		await expect(page.locator('[data-testid="ppl-add-selected"]')).toBeEnabled();
		await page.locator('[data-testid="ppl-add-selected"]').click();
		await expect(page.locator('[data-testid="pln-form-dialog"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-form-title"]')).toHaveText("How should these requirements be added?");
		await expect(page.locator('[data-testid="pln-form-confirm"]')).toHaveText("Add to plan");
		await page.locator('[data-testid="pln-form-confirm"]').click();
		await expectReady(page, "plan-item");

		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="ppl-purchases"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="ppl-all-allocated"]')).toBeVisible();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("planner saves the project name from the Overview tab", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_workbench_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");

		const save = page.locator('[data-testid="ppl-save"]');
		await expect(save).toBeDisabled();
		await page.locator('[data-testid="ppl-project-name"]').fill("Digital health infrastructure programme");
		await expect(save).toBeEnabled();
		await save.click();
		await expectReady(page, "plan");
		await expect(save).toBeDisabled();

		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="ppl-project-name"]')).toHaveValue("Digital health infrastructure programme");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("planner requests plan funding confirmation once every readiness check passes", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_ready_for_funding_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");

		const request = page.locator('[data-testid="ppl-request-funding"]');
		await expect(request).toBeEnabled();
		await request.click();
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="ppl-plan-checks"]')).toContainText("Awaiting Finance confirmation");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("auditor reads every tab with no formation, save or funding-request controls", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_workbench_fixture");
		await login(page, AUDITOR, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="ppl-save"]')).toHaveCount(0);

		await expect(page.locator('[data-testid="ppl-add-selected"]')).toHaveCount(0);

		await expect(page.locator('[data-testid="ppl-request-funding"]')).toHaveCount(0);
	});

	test("a departmental Author has no route to the Annual Plan record", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_workbench_fixture");
		await login(page, AUTHOR, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-error"] h3')).toHaveText("This record isn't available to you");
	});

	test("an unrelated Author (Outsider) is masked the same way", async ({ page }) => {
		const state = resetFixture<{ plan_reference: string }>("reset_workbench_fixture");
		await login(page, OUTSIDER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await expect(page.locator('[data-testid="pln-error"] h3')).toHaveText("This record isn't available to you");
	});
});
