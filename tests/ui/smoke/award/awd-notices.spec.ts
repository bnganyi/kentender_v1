import { expect, test } from "@playwright/test";

import { CHARLES, DANIEL, EVIDENCE, as, awardWorld, awdFixture, closeSession, collectConsoleErrors, expectJourney, expectNextStep, expectScreen,
	restoreAwardWorld } from "./awdWorld";

/**
 * AWD-CHG-001 v0.4 slice 5 (boards V05, V16; tracker AWD4-506): a notice the
 * address rejected is not "notified"; Correct contact retries the same notice
 * once the contact owner has corrected it; a service failure is the technical
 * operator's Retry operation, never a business decision.
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("Award — notices", () => {
	test.afterAll(async () => {
		await closeSession();
		restoreAwardWorld();
	});

	test("a rejected address, then the corrected contact", async ({ browser }) => {
		const world = awardWorld("notice-failed");
		const page = await as(browser, CHARLES);
		const errors = collectConsoleErrors(page);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "delivery-failure");
		await expectNextStep(page, "your_turn_blocked", "A required notice is not yet confirmed.");
		await expectJourney(page, ["Done", "Done", "Blocked", "Not started", "Not started"]);
		const root = page.locator('[data-testid="awd-root"]');
		await expect(root.locator("table")).toContainText("Delivery failed");
		await page.screenshot({ path: `${EVIDENCE}/V05.png`, fullPage: true });
		const fix = root.locator('[data-testid="awd-guidance"] [data-fix^="correct_contact:"]');
		await fix.click();
		await expect(root.locator('[data-testid="awd-error"]')).toContainText("The contact owner has not corrected the address yet.");
		awdFixture("simulate_contact_correction", { award: world.award });
		await fix.click();
		await expectScreen(page, "wait");
		await expectNextStep(page, "waiting", "The supplier must reply by the date in the notice.");
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("the technical operator restores notice delivery", async ({ browser }) => {
		const world = awardWorld("technical");
		const page = await as(browser, DANIEL);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "technical");
		const root = page.locator('[data-testid="awd-root"]');
		await expect(root.locator('[data-testid="awd-title"]')).toHaveText("Restore notice delivery");
		await expect(root).not.toContainText("KES");
		await expect(root).not.toContainText("Afya");
		await page.screenshot({ path: `${EVIDENCE}/V16.png`, fullPage: true });
		awdFixture("set_controls", { email_service_down: 0 });
		await root.locator('[data-testid="awd-action-retry-operation"]').click();
		await expect(root).toHaveAttribute("data-pending", "false", { timeout: 30_000 });
		await expect(root.locator('[data-testid="awd-fact-result"]')).toHaveText("Resolved");
	});
});
