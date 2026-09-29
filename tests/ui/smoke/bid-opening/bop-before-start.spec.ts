import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, CHAIR, INDEPENDENT, MEMBER, PASSWORD, bopFixture, collectConsoleErrors, expectNextStep, expectScreen, gotoOpening, openingWorld, restoreBopWorld } from "./bopWorld";

/** BOP-CHG-001 v0.10 §10.3 before Start — boards c1–c3, c2b–c2d (slice 8.2). */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BOP-DES-02 Open bids — before Start", () => {
	test.afterAll(() => restoreBopWorld());

	test("chair: the missing member is named and notified; they join; the chair starts the opening", async ({ page }) => {
		const world = openingWorld("missing");
		const errors = collectConsoleErrors(page);
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "waiting", `Opening cannot start because ${world.independent_name} has not joined.`);
		await expect(page.locator('[data-testid="bop-desc"]')).toContainText("Submissions closed");
		await expect(page.locator('[data-testid="bop-committee-presence"] tbody tr')).toHaveCount(3);
		await expect(page.locator(`[data-user="${INDEPENDENT}"] .kt-status`)).toHaveText("Not joined");
		await page.locator(`[data-testid="bop-notify-${INDEPENDENT}"]`).click();
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-start"]')).toHaveCount(0);

		// the independent member joins from their own page
		await login(page, INDEPENDENT, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", `Join opening for ${world.tender_reference}`);
		await page.locator('[data-testid="bop-join"]').click();
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-join"]')).toHaveCount(0);

		// c3: ready; Start
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Ready to start");
		await page.locator('[data-testid="bop-start"]').click();
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Open the first bid");
		await expect(page.locator('[data-testid="bop-desc"] .kt-status')).toHaveText("In session");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("c1 before the deadline: sealed bids and no count; a member waits for the chair", async ({ page }) => {
		const world = openingWorld("joined");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "timed", /^Submissions close automatically at /);
		await expect(page.locator(".kt-region h2", { hasText: "Bids" })).toBeVisible();
		await expect(page.getByText("Nobody can see how many bids were received before then.")).toBeVisible();
		await login(page, MEMBER, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "timed", /^Submissions close automatically at /);
		await login(page, AUDITOR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-start"], [data-testid="bop-join"]')).toHaveCount(0);
	});

	test("c2b, c2d → c2c: access not ready; support could not be told, then Notify support tells them", async ({ page }) => {
		let world = openingWorld("access");
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "waiting", "Opening access is not ready yet.");
		await page.locator('[data-testid="bop-view-problem"]').click();
		world = openingWorld("notify-failed");
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn_blocked", "Bid opening isn’t available yet.");
		await expect(page.locator('[data-testid="bop-why-not-start"]')).toContainText("Not yet notified");
		// the notice fails again: the same incident, still not notified
		await page.locator('[data-testid="bop-guidance"] [data-kt="next-step"] button', { hasText: "Notify support" }).click();
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-why-not-start"]')).toContainText("Not yet notified");
		// then it gets through (board c2c)
		bopFixture("set_controls", { notify_outcome: "Deliver" });
		await page.locator('[data-testid="bop-guidance"] [data-kt="next-step"] button', { hasText: "Notify support" }).click();
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "waiting", "Bid opening isn’t available yet.");
		await expect(page.locator('[data-testid="bop-why-not-start"]')).toContainText("Support notified");
	});
});
