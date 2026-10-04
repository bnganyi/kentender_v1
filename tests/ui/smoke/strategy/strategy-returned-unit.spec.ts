import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUTHOR,
	PASSWORD,
	collectConsoleErrors,
	expectScreen,
	gotoStrategy,
	resetFixture,
	type SuccessorFixture,
} from "./helpers";

/**
 * GitHub #18 — a plan returned for correction must let the Strategy Author
 * change an indicator's unit (for example Percentage to Count).
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("Strategy — returned plan, indicator unit", () => {
	let fixture: SuccessorFixture;

	test.beforeAll(() => {
		fixture = resetFixture<SuccessorFixture>("reset_returned_fixture");
	});

	test.afterAll(() => {
		resetFixture("reset_default");
	});

	test("the Author changes an indicator's unit on a returned plan and it is kept", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/plan/${fixture.plan_reference}/version/2/structure`);
		await expectScreen(page, "plan");

		const indicator = page.locator('[data-testid="str-tree-node"][data-node-type="Performance Indicator"]').first();
		await indicator.click();
		const unit = page.locator('[data-testid="str-indicator-unit"]');
		await expect(unit).toBeEnabled();
		await expect(unit).toHaveValue("Percentage");

		// The suggestions are always on show, whatever the field already holds
		// (a browser's own list only offers entries matching the current text,
		// so with "Percentage" in the box "Count" never appeared).
		const options = page.locator('[data-testid="str-unit-option"]');
		await expect(options.filter({ hasText: /^Count$/ })).toBeVisible();
		await expect(options.filter({ hasText: /^Percentage$/ })).toHaveAttribute("aria-pressed", "true");

		await options.filter({ hasText: /^Count$/ }).click();
		await expect(unit).toHaveValue("Count");
		await expect(options.filter({ hasText: /^Count$/ })).toHaveAttribute("aria-pressed", "true");
		await page.locator('[data-testid="str-node-save"]').click();
		await expect(page.locator('[data-testid="str-unsaved-indicator"]')).toHaveCount(0, { timeout: 30_000 });

		await page.reload();
		await expectScreen(page, "plan");
		await indicator.click();
		await expect(unit).toHaveValue("Count");

		// A unit nobody has used yet can still be typed.
		await unit.fill("Per 1,000 births");
		await page.locator('[data-testid="str-node-save"]').click();
		await expect(page.locator('[data-testid="str-unsaved-indicator"]')).toHaveCount(0, { timeout: 30_000 });
		await page.reload();
		await expectScreen(page, "plan");
		await indicator.click();
		await expect(unit).toHaveValue("Per 1,000 births");

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
