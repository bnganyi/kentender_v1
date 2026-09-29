import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { CHAIR, INDEPENDENT, MEMBER, PASSWORD, collectConsoleErrors, expectNextStep, expectScreen, gotoOpening, openingWorld, restoreBopWorld } from "./bopWorld";

/** BOP-CHG-001 v0.10 §10.3 in session — boards c4–c9, c13, c13b, c7, c8, c8b (slice 8.3). */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BOP-DES-02 Open bids — the ceremony", () => {
	test.afterAll(() => restoreBopWorld());

	test("chair: open the bid, record what was read aloud, a request, a comment for Evaluation, end", async ({ page }) => {
		const world = openingWorld("started");
		const errors = collectConsoleErrors(page);
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Open the first bid");
		await page.locator('[data-testid="bop-open-next"]').click();
		await expectScreen(page, "open-bids");

		// c6: the recorder's form; the bid's facts are read-only
		await expectNextStep(page, "your_turn", "Record what was read aloud");
		await expect(page.locator('[data-testid="bop-bid-facts"] .kt-label')).toHaveText(["Bid", "Tenderer", "Submitted total", "Tender security given", "Pages"]);
		await expect(page.getByText("Nothing recorded yet.")).toBeVisible();
		await page.locator('[data-testid="bop-readout-by"]').selectOption(MEMBER);
		await page.locator('[data-testid="bop-record-readout"]').click();
		await expectScreen(page, "open-bids");

		// c9: every bid read out
		await expectNextStep(page, "your_turn", "End the opening");
		await expect(page.locator('[data-testid="bop-register"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="bop-requests-none"]')).toBeVisible();

		// c7: a request made during the opening
		await page.locator('[data-testid="bop-open-request"]').click();
		await page.locator('[data-testid="bop-request-by"]').fill("David Ouma");
		await page.locator('[data-testid="bop-request-what"]').fill("Asked for the submitted total to be repeated");
		await page.locator('[data-testid="bop-request-response"]').fill("The member repeated the total.");
		await page.locator('[data-testid="bop-request-record"]').click();
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-requests"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="bop-requests"] .kt-status')).toHaveText("Answered during opening");

		// c13 → c13b
		await page.locator('[data-testid="bop-open-comment"]').click();
		await page.locator('[data-testid="bop-comment-text"]').fill("The security reference on the price page differs from the reference read aloud.");
		await page.locator('[data-testid="bop-comment-record"]').click();
		await expectScreen(page, "open-bids");
		await expect(page.locator('[data-testid="bop-requests"] thead th')).toHaveText(["Time", "Who", "What", "Response", "Outcome"]);
		await expect(page.locator('[data-testid="bop-requests"] .kt-status').last()).toHaveText("Recorded for Evaluation");

		// a reload keeps where the opening is
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "End the opening");

		await page.locator('[data-testid="bop-end"]').click();
		await expectScreen(page, "record");
		await expectNextStep(page, "your_turn", "Prepare opening record");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("c5: the reading member sees what to read aloud; the others wait", async ({ page }) => {
		const world = openingWorld("opened");
		await login(page, MEMBER, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "Read these details aloud");
		await expect(page.locator('[data-testid="bop-read-aloud-text"]')).not.toBeEmpty();
		await expect(page.locator('[data-testid="bop-view-bid-pages"]')).toHaveAttribute("href", /get_bid_pages/);
		await expect(page.locator('[data-testid="bop-record-readout"]')).toHaveCount(0);
	});

	test("c8 → c8b: a member records their own account; the recorder responds", async ({ page }) => {
		const world = openingWorld("answered");
		await login(page, INDEPENDENT, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await page.locator('[data-testid="bop-open-account"]').click();
		await expect(page.locator('[data-testid="bop-guidance"] [data-kt="next-step"]')).toHaveCount(0);
		await page.locator('[data-testid="bop-account-text"]').fill("I could not hear the security reference clearly.");
		await page.locator('[data-testid="bop-account-record"]').click();
		await expectScreen(page, "open-bids");

		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", `Record the response to ${world.independent_name}’s account`);
		await expect(page.locator('[data-testid="bop-respond-form"]')).toContainText("I could not hear the security reference clearly.");
		await page.locator('[data-testid="bop-respond-text"]').fill("The member repeated the security reference.");
		await page.locator('[data-testid="bop-respond-record"]').click();
		await expectScreen(page, "open-bids");
		await expectNextStep(page, "your_turn", "End the opening");
	});
});
