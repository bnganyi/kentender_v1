import { expect, test } from "@playwright/test";

import { CHARLES, EVIDENCE, as, awardWorld, awdFixture, closeSession, expectJourney, expectNextStep, expectScreen, restoreAwardWorld } from "./awdWorld";

/**
 * AWD-CHG-001 v0.4 slice 7 (boards D05, D06, V10; tracker AWD4-706): the
 * waiting period runs on the trusted clock; at its end the system delivers the
 * package with no approval and the record reads "Contracting has received the
 * award."; a receiver outage waits with the technical owner named.
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("Award — wait and deliver", () => {
	test.afterAll(async () => {
		await closeSession();
		restoreAwardWorld();
	});

	test("the wait ends and Contracting receives the award", async ({ browser }) => {
		const world = awardWorld("accepted");
		const page = await as(browser, CHARLES);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "wait");
		await expectNextStep(page, "waiting", "The required waiting period is still running.");
		await expectJourney(page, ["Done", "Done", "Done", "Current", "Not started"]);
		const root = page.locator('[data-testid="awd-root"]');
		await expect(root).toContainText("Supplier accepted, 18 Jun 2027, 09:00 EAT");
		await expect(root).toContainText("All bidders have been notified");
		await expect(root.locator('[data-testid="awd-fact-earliest-permitted-date-and-time"]')).toHaveText("2 Jul 2027, 09:00 EAT");
		await page.screenshot({ path: `${EVIDENCE}/D05.png`, fullPage: true });
		awdFixture("set_instant", { instant: "2027-07-02 09:00:00" });
		awdFixture("refresh", { award: world.award });
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "delivered");
		await expectNextStep(page, "done", "Contracting has received the award.");
		await expectJourney(page, ["Done", "Done", "Done", "Done", "Done"]);
		await expect(root.locator('[data-testid="awd-fact-next"]')).toHaveText("Prepare contract");
		await expect(root.locator('[data-testid="awd-fact-contracting-owner"]')).toHaveText("Charles Mutiso");
		await page.screenshot({ path: `${EVIDENCE}/D06.png`, fullPage: true });
	});

	test("an unavailable receiver waits with its owner named", async ({ browser }) => {
		const world = awardWorld("receiver-down");
		const page = await as(browser, CHARLES);
		await page.goto(`/app/award/${world.award}`, { waitUntil: "domcontentloaded" });
		await expectScreen(page, "receiver-down");
		await expectNextStep(page, "waiting", "Contracting is unavailable. KenTender will check that the award can still proceed before sending it.");
		await expectJourney(page, ["Done", "Done", "Done", "Done", "Blocked"]);
		await expect(page.locator('[data-testid="awd-root"]')).toContainText("Technical operator Daniel Otieno is restoring delivery.");
		await page.screenshot({ path: `${EVIDENCE}/V10.png`, fullPage: true });
	});
});
