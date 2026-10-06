import { expect, test } from "@playwright/test";

import { AMINA, CHARLES, EVIDENCE, as, awardWorld, closeSession, collectConsoleErrors, expectJourney, expectNextStep, expectScreen, openAwardsFromMenu,
	restoreAwardWorld } from "./awdWorld";

/**
 * AWD-CHG-001 v0.4 slice 4 (boards D03, X08, X09, V01, V04; tracker AWD4-404):
 * the Accounting Officer decides from the task in the menu — Award and notify
 * bidders in one action; Return for correction back to the Head; Record no
 * award with a named next action. One fixture entity per test: tender 033
 * at "signed".
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("Award — the Accounting Officer's decision", () => {
	test.afterAll(async () => {
		await closeSession();
		restoreAwardWorld();
	});

	test("Award and notify bidders in one action", async ({ browser }) => {
		const world = awardWorld("signed");
		const page = await as(browser, AMINA);
		const errors = collectConsoleErrors(page);
		await openAwardsFromMenu(page);
		const root = page.locator('[data-testid="awd-root"]');
		const row = root.locator("tr", { hasText: world.award });
		await expect(row).toContainText("Decide award");
		await row.getByRole("button", { name: "Open award" }).click();
		await expectScreen(page, "decision");
		await expectNextStep(page, "your_turn", "Decide the award.");
		await expectJourney(page, ["Done", "Current", "Not started", "Not started", "Not started"]);
		await expect(root).toContainText("Signed by Charles Mutiso, 17 Jun 2027, 09:10 EAT");
		await expect(root.locator('[data-testid="awd-def-notice-preview"]')).toHaveText("Successful bidder notice — Afya Digital Supplies Limited");
		await root.locator('[data-testid="awd-field-decision_reason"]').fill("I accept the recommendation in the signed evaluation report and professional opinion.");
		await page.screenshot({ path: `${EVIDENCE}/D03.png`, fullPage: true });
		await root.locator('[data-testid="awd-action-award-and-notify-bidders"]').click();
		await expectScreen(page, "wait");
		await expectJourney(page, ["Done", "Done", "Done", "Current", "Not started"]);
		await expect(root.locator('[data-testid="awd-action-award-and-notify-bidders"]')).toHaveCount(0);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("Return for correction reaches the Head as one task", async ({ browser }) => {
		const world = awardWorld("signed");
		let page = await as(browser, AMINA);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "decision");
		const root = page.locator('[data-testid="awd-root"]');
		await root.locator('[data-testid="awd-action-return-for-correction"]').click();
		const dialog = root.locator('[data-testid="awd-dialog"]');
		await expect(dialog.locator(".dialog-title")).toHaveText("Return for correction");
		await page.screenshot({ path: `${EVIDENCE}/X08.png`, fullPage: true });
		await dialog.locator('[data-testid="awd-dialog-field-dlg_reason"]').fill("Explain the unresolved funding concern before recommending an award.");
		await dialog.locator('[data-testid="awd-dialog-return-for-correction"]').click();
		await expectScreen(page, "opinion-read");
		page = await as(browser, CHARLES);
		await openAwardsFromMenu(page);
		const row = page.locator('[data-testid="awd-root"] tr', { hasText: world.award });
		await expect(row).toContainText("Resolve returned decision");
		await row.getByRole("button", { name: "Open award" }).click();
		await expectScreen(page, "returned");
		await expectNextStep(page, "your_turn", "Resolve the Accounting Officer’s comments.");
		await expect(page.locator('[data-testid="awd-def-comment"]')).toHaveText("Explain the unresolved funding concern before recommending an award.");
		await page.screenshot({ path: `${EVIDENCE}/V01.png`, fullPage: true });
	});

	test("Record no award needs a named next action", async ({ browser }) => {
		const world = awardWorld("signed");
		let page = await as(browser, AMINA);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "decision");
		const root = page.locator('[data-testid="awd-root"]');
		await root.locator('[data-testid="awd-action-record-no-award"]').click();
		const dialog = root.locator('[data-testid="awd-dialog"]');
		await dialog.locator('[data-testid="awd-dialog-field-dlg_reason"]').fill("The funding position cannot support an award.");
		await dialog.locator('[data-testid="awd-dialog-record-no-award"]').click();
		await expect(dialog.locator('[data-testid="awd-dialog-error-dlg_next_action"]')).toHaveText("Name the next action.");
		await expect(dialog.locator('[data-testid="awd-dialog-field-dlg_reason"]')).toHaveValue("The funding position cannot support an award.");
		await page.screenshot({ path: `${EVIDENCE}/X09.png`, fullPage: true });
		await dialog.locator('[data-testid="awd-dialog-field-dlg_next_action"]').fill("Resolve the funding position");
		await dialog.locator('[data-testid="awd-dialog-record-no-award"]').click();
		await expectScreen(page, "no-award");
		page = await as(browser, CHARLES);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "no-award");
		await expectNextStep(page, "your_turn", "No award was made.");
		await expect(page.locator('[data-testid="awd-chip"]')).toHaveText("Closed");
		await expectJourney(page, ["Done", "Done", "Not started", "Not started", "Not started"]);
		await page.screenshot({ path: `${EVIDENCE}/V04.png`, fullPage: true });
	});
});
