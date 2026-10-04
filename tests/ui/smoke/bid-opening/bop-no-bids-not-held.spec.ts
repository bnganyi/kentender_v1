import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, CHAIR, PASSWORD, expectNextStep, expectScreen, gotoOpening, openingWorld, restoreBopWorld } from "./bopWorld";

/** BOP-CHG-001 v0.10 §10 empty outcome and branch 4 — boards z1, n1, n2 (slice 8.5). */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BOP-DES-02 Open bids — no bids and not held", () => {
	test.afterAll(() => restoreBopWorld());

	test("z1: no bids — one action ends the opening, and the record still needs signing", async ({ page }) => {
		const world = openingWorld("empty-started");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "No bids to open");
		await expect(page.locator('[data-testid="bop-open-next"]')).toHaveCount(0);
		await page.locator('[data-testid="bop-end-no-bids"]').click();
		await expectScreen(page, "record");
		await expectNextStep(page, "your_turn", "Prepare opening record");
		await expect(page.locator('[data-testid="bop-register"] tbody tr')).toHaveCount(0);
	});

	test("n1 → n2: the Accounting Officer records that the opening did not take place", async ({ page }) => {
		const world = openingWorld("not-held-due");
		await login(page, AO, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "The opening has not started; record what happened");
		await expect(page.locator('[data-testid="bop-desc"] .kt-status')).toHaveText("Not started");
		await expect(page.locator('[data-testid="bop-record-not-held"]')).toBeDisabled();
		await page.locator('[data-testid="bop-not-held-reason"]').fill("The public attendance service was unavailable; opening did not start");
		await page.locator('[data-testid="bop-record-not-held"]').click();
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Decide what happens next");
		await expect(page.locator('[data-testid="bop-not-held"]')).toContainText("The public attendance service was unavailable; opening did not start");
		await expect(page.locator('[data-testid="bop-desc"] .kt-status')).toHaveText("Did not take place");
	});
});
