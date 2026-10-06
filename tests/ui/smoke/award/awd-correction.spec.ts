import { expect, test } from "@playwright/test";

import { AMINA, CHARLES, EVIDENCE, as, awardWorld, closeSession, expectJourney, expectNextStep, expectScreen, restoreAwardWorld } from "./awdWorld";

/**
 * AWD-CHG-001 v0.4 slice 9 (boards V09, X06, V17, V19; tracker AWD4-904): a
 * correction after the award holds it; the Head proposes a corrected
 * evaluation; the Accounting Officer authorises it; a numbered successor cycle
 * waits for Evaluation's corrected report — the original decision stays.
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("Award — post-decision correction", () => {
	test.afterAll(async () => {
		await closeSession();
		restoreAwardWorld();
	});

	test("review, propose, authorise, wait for the corrected report", async ({ browser }) => {
		const world = awardWorld("post-decision-correction");
		let page = await as(browser, CHARLES);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "correction-review");
		await expectNextStep(page, "your_turn", "Review the report correction before this award proceeds.");
		await expectJourney(page, ["Done", "Done", "Done", "Blocked", "Not started"]);
		let root = page.locator('[data-testid="awd-root"]');
		await page.screenshot({ path: `${EVIDENCE}/V09.png`, fullPage: true });
		await root.locator('[data-testid="awd-action-review-correction"]').click();
		const dialog = root.locator('[data-testid="awd-dialog"]');
		await expect(dialog.locator(".dialog-title")).toHaveText("Review correction");
		await expect(dialog.locator('input[type="radio"]:checked')).toHaveCount(0);
		await page.screenshot({ path: `${EVIDENCE}/X06.png`, fullPage: true });
		await dialog.locator("label.radio", { hasText: "Request corrected evaluation" }).click();
		await dialog.locator('[data-testid="awd-dialog-field-dlg_reason"]').fill("The reported calculation issue may affect the recommendation.");
		await dialog.locator('[data-testid="awd-dialog-field-dlg_evidence"]').fill("Correction notice PW-CN-1");
		await dialog.locator('[data-testid="awd-dialog-field-dlg_next_action"]').fill("Request a corrected evaluation report addressing the calculation issue.");
		await dialog.locator('[data-testid="awd-dialog-save-outcome"]').click();
		await expect(root.locator('[data-testid="awd-dialog"]')).toHaveCount(0, { timeout: 30_000 });

		page = await as(browser, AMINA);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "correction-proposal");
		await expectNextStep(page, "your_turn", "Decide the reported correction.");
		root = page.locator('[data-testid="awd-root"]');
		await expect(root.locator('[data-testid="awd-def-proposal"]')).toHaveText("Request a corrected evaluation report addressing the calculation issue.");
		await page.screenshot({ path: `${EVIDENCE}/V17.png`, fullPage: true });
		await root.locator('[data-testid="awd-action-request-corrected-evaluation"]').click();
		await expectScreen(page, "awaiting");

		page = await as(browser, CHARLES);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "awaiting");
		await expectNextStep(page, "waiting", "Evaluation is correcting the report.");
		await expectJourney(page, ["Blocked", "Not started", "Not started", "Not started", "Not started"]);
		await expect(page.locator('[data-testid="awd-fact-decision-cycle"]')).toHaveText("2");
		await page.screenshot({ path: `${EVIDENCE}/V19.png`, fullPage: true });
	});
});
