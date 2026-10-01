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
 * GitHub #27 — on Objectives and targets, each target card sits beside the
 * indicator it belongs to, not in one column that ignores which indicator
 * comes first.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("Strategy — Objectives and targets alignment", () => {
	let fixture: SuccessorFixture;

	test.beforeAll(() => {
		fixture = resetFixture<SuccessorFixture>("reset_two_indicator_fixture");
	});

	test.afterAll(() => {
		resetFixture("reset_default");
	});

	test("each target card is level with its own indicator", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/plan/${fixture.plan_reference}/version/2`);
		await expectScreen(page, "plan");

		const objective = page.locator('[data-testid="str-objective"]').first();
		await expect(objective).toBeVisible();
		const rows = objective.locator('[data-testid="str-objective-row"]');
		await expect(rows).toHaveCount(2);

		// One objective heading, one indicator and one target per row.
		await expect(objective.locator('[data-testid="str-objective-title"]')).toHaveCount(1);
		for (let i = 0; i < 2; i++) {
			await expect(rows.nth(i).locator('[data-testid="str-objective-indicator"]')).toHaveCount(1);
			await expect(rows.nth(i).locator('[data-testid="str-target-kpi"]')).toHaveCount(1);
		}
		await expect(rows.nth(0).locator('[data-testid="str-target-kpi"]')).toContainText("80%");
		await expect(rows.nth(1).locator('[data-testid="str-target-kpi"]')).toContainText("2");
		await expect(rows.nth(1).locator('[data-testid="str-objective-indicator"]')).toContainText("safeguarding");

		// Level on the page: the second card starts below the first indicator's
		// whole block and no higher than its own indicator.
		const box = async (locator: ReturnType<typeof page.locator>) => (await locator.boundingBox())!;
		const firstBlock = await box(rows.nth(0));
		const secondIndicator = await box(rows.nth(1).locator('[data-testid="str-objective-indicator"]'));
		const secondCard = await box(rows.nth(1).locator('[data-testid="str-target-kpi"]'));
		expect(secondCard.y).toBeGreaterThanOrEqual(firstBlock.y + firstBlock.height - 1);
		expect(secondCard.y).toBeLessThanOrEqual(secondIndicator.y + 1);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
