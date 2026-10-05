import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, CHAIR, INDEPENDENT, PASSWORD, expectNextStep, expectScreen, gotoOpening, openingWorld, restoreBopWorld } from "./bopWorld";

/** BOP-CHG-001 v0.10 §10 branches 1, 2, 3, 5 — boards c10, c11–c11e, c12 (slice 8.4). */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BOP-DES-02 Open bids — pauses and cancellation", () => {
	test.afterAll(() => restoreBopWorld());

	test("c10: a member left; they rejoin and the opening continues", async ({ page }) => {
		const world = openingWorld("member-left");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "waiting", new RegExp(`^Waiting for ${world.independent_name} to rejoin`));
		await expect(page.locator('[data-testid="bop-desc"] .kt-status')).toHaveText("Paused");
		await expect(page.locator(`[data-testid="bop-notify-${INDEPENDENT}"]`)).toBeVisible();
		await login(page, INDEPENDENT, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await page.locator('[data-testid="bop-join"]').click();
		await expectScreen(page, "open-bids");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-desc"] .kt-status')).toHaveText("In session");
		await expectNextStep(page, "your_turn", "End the opening");
	});

	test("c11 → c11b: an unreadable bid; Retry waits for support, then opens the same bid", async ({ page }) => {
		let world = openingWorld("unreadable");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn_blocked", /^This bid could not be opened/);
		await expect(page.locator('[data-testid="bop-retry"]')).toBeDisabled();
		await expect(page.locator('[data-testid="bop-problem-status"]')).toHaveText("Being checked");
		world = openingWorld("resolved");
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Retry opening");
		await page.locator('[data-testid="bop-retry"]').click();
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Record what was read aloud");
	});

	test("c11c / c11e: support cannot fix it — the chair waits and the Accounting Officer decides", async ({ page }) => {
		const world = openingWorld("unresolved");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "waiting", /to resolve the paused opening$/);
		await expect(page.locator('[data-testid="bop-problem-status"]')).toHaveText("Not resolved");
		await login(page, AO, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Decide how to proceed with the paused opening");
		await expect(page.locator('[data-testid="bop-tender-decision"]')).toContainText("Cancellation after submissions close is not available in this version.");
	});

	test("c11d: a bid that does not match is checked, never skipped", async ({ page }) => {
		const world = openingWorld("mismatch");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn_blocked", /checks this bid against the submissions received at the deadline\.$/);
		await expect(page.locator('[data-testid="bop-bid-problem"] h2')).toHaveText("Bid being checked");
	});

	test("c12: ended by Tender cancellation — a partial record and nothing to sign", async ({ page }) => {
		const world = openingWorld("cancelled");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-desc"] .kt-status')).toHaveText("Ended — Tender cancelled");
		await expect(page.locator('[data-testid="bop-cancelled"]')).toContainText("There is no opening record to sign");
		await expect(page.locator("button.btn-primary")).toHaveCount(0);
	});
});
