import { expect, test } from "@playwright/test";

import { CHARLES, EVIDENCE, as, awardWorld, closeSession, expectJourney, expectNextStep, expectScreen, restoreAwardWorld } from "./awdWorld";

/**
 * AWD-CHG-001 v0.4 slice 8 (boards D07, D07c, X03, V08, X04; tracker
 * AWD4-805): the Head answers a bidder's request (the draft survives a
 * reload; Send and close closes it only once sent); records an authoritative
 * order, which holds the award; and ends it only with evidence.
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("Award — debrief and holds", () => {
	test.afterAll(async () => {
		await closeSession();
		restoreAwardWorld();
	});

	test("respond to the bidder's request and close it once sent", async ({ browser }) => {
		const world = awardWorld("request");
		const page = await as(browser, CHARLES);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "request");
		await expectNextStep(page, "your_turn", "Respond to the bidder’s request.");
		await expectJourney(page, ["Done", "Done", "Done", "Current", "Not started"]);
		const root = page.locator('[data-testid="awd-root"]');
		await expect(root).toContainText("Please explain the recorded award result.");
		await root.locator('[data-testid="awd-field-reply"]').fill("The recorded result follows the signed evaluation report. Your tender was successful at KES 46,400,000.");
		await root.locator('[data-testid="awd-action-save-reply"]').click();
		await expect(root).toHaveAttribute("data-pending", "false");
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "request");
		await expect(root.locator('[data-testid="awd-field-reply"]')).toHaveValue(/Your tender was successful at KES 46,400,000\./);
		await page.screenshot({ path: `${EVIDENCE}/D07.png`, fullPage: true });
		await root.locator('[data-testid="awd-action-send-and-close"]').click();
		await expectScreen(page, "wait");
		await page.goto(`/app/award/${world.award}/requests/${world.requests[0]}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "request-closed");
		await expect(root.locator('[data-testid="awd-guidance"] [data-testid="kt-next-step-headline"]')).toHaveText("This request is closed.");
		await expect(root.locator('[data-testid="awd-def-response"]')).toHaveText("The recorded result follows the signed evaluation report. Your tender was successful at KES 46,400,000.");
		await expect(root.locator('[data-testid="awd-action-send-and-close"]')).toHaveCount(0);
		await page.screenshot({ path: `${EVIDENCE}/D07c.png`, fullPage: true });
	});

	test("an authoritative order holds the award until its release is evidenced", async ({ browser }) => {
		const world = awardWorld("order-hold");
		const page = await as(browser, CHARLES);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "hold");
		await expectNextStep(page, "your_turn_blocked", "This award is on hold.");
		await expectJourney(page, ["Done", "Done", "Done", "Blocked", "Not started"]);
		const root = page.locator('[data-testid="awd-root"]');
		await expect(root).toContainText("Review Board suspension notice received 20 Jun 2027, 11:00 EAT");
		await page.screenshot({ path: `${EVIDENCE}/V08.png`, fullPage: true });
		await root.locator('[data-testid="awd-guidance"] [data-fix^="record_outcome:"]').click();
		const dialog = root.locator('[data-testid="awd-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Record outcome");
		await expect(dialog).toContainText("Authoritative order");
		await expect(dialog.locator('[data-testid="awd-dialog-choice-reported-challenge-not-substantiated"]')).toHaveCount(0);
		await page.screenshot({ path: `${EVIDENCE}/X04.png`, fullPage: true });
		await dialog.locator("label.kt-radio", { hasText: "Restriction ended" }).click();
		await dialog.locator('[data-testid="awd-dialog-field-dlg_reason"]').fill("The Review Board released the suspension.");
		await dialog.locator('[data-testid="awd-dialog-field-dlg_evidence"]').fill("PPARB/2027/33 release");
		await dialog.locator('[data-testid="awd-dialog-save-outcome"]').click();
		await expectScreen(page, "wait");
		await expectJourney(page, ["Done", "Done", "Done", "Current", "Not started"]);
	});

	test("Record restriction from the opinion's outstanding issues", async ({ browser }) => {
		const world = awardWorld("received");
		const page = await as(browser, CHARLES);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "opinion");
		const root = page.locator('[data-testid="awd-root"]');
		await root.locator('[data-testid="awd-disclosure-outstanding-issues"] .kt-disclosure-head').click();
		await root.locator('[data-testid="awd-disclosure-action-record-restriction"]').click();
		const dialog = root.locator('[data-testid="awd-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Record restriction");
		await page.screenshot({ path: `${EVIDENCE}/X03.png`, fullPage: true });
		await dialog.locator("label.kt-radio", { hasText: "Reported challenge" }).click();
		await dialog.locator('[data-testid="awd-dialog-field-dlg_source"]').fill("Complaint letter from a bidder");
		await dialog.locator('[data-testid="awd-dialog-field-dlg_received_at"]').fill("2027-06-17 09:30:00");
		await dialog.locator('[data-testid="awd-dialog-field-dlg_reason"]').fill("A bidder reported a challenge.");
		await dialog.locator('[data-testid="awd-dialog-save-restriction"]').click();
		await expect(root.locator('[data-testid="awd-dialog"]')).toHaveCount(0, { timeout: 30_000 });
		await expectNextStep(page, "your_turn_blocked", "This award is on hold.");
	});
});
