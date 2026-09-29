import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { CHAIR, INDEPENDENT, MEMBER, PASSWORD, collectConsoleErrors, expectNextStep, expectScreen, gotoOpening, openingWorld, restoreBopWorld } from "./bopWorld";

/** BOP-CHG-001 v0.10 §10.4 — boards r1–r6 (slice 8.6). */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("BOP-DES-03 Opening record", () => {
	test.afterAll(() => restoreBopWorld());

	test("recorder: review, prepare the draft, finish; then sign for themselves and wait", async ({ page }) => {
		const world = openingWorld("ended");
		const errors = collectConsoleErrors(page);
		await login(page, CHAIR, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "record");
		await expectNextStep(page, "your_turn", "Prepare opening record");
		await expect(page.locator('[data-testid="bop-attendance"] thead th')).toHaveText(["Name", "Attended as", "Joined", "Left"]);
		await page.locator('[data-testid="bop-prepare-record"]').click();
		await expectNextStep(page, "your_turn", "Check the draft and finish the opening record");
		await expect(page.locator('[data-testid="bop-signing"] tbody tr td:nth-child(3)')).toHaveText(["Sign the page", "Initial the price", "Initial each page", "Sign with full name and designation"]);
		await page.locator('[data-testid="bop-finish-record"]').click();
		await expectScreen(page, "record");
		await expectNextStep(page, "your_turn", "Review and sign opening record");
		await expect(page.locator('[data-testid="bop-read-record"]')).toHaveAttribute("href", /get_record_pages/);
		await page.locator('[data-testid="bop-sign"]').click();
		await expectScreen(page, "record");
		await expectNextStep(page, "waiting", /^Waiting for .* to sign the opening record$/);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("r5: a new version asks for fresh signatures; the last signature completes the opening", async ({ page }) => {
		const world = openingWorld("changed");
		await login(page, MEMBER, PASSWORD);
		await gotoOpening(page, world.tender_reference);
		await expectScreen(page, "record");
		await expectNextStep(page, "your_turn", "The opening record changed. Review the latest version before signing");
		await expect(page.locator('[data-testid="bop-what-changed"]')).toContainText("Add the attendee’s repeat request");
		await expect(page.locator('[data-testid="bop-desc"] .kt-status')).toHaveText("Version 2");
		await page.locator('[data-testid="bop-sign"]').click();
		await expectScreen(page, "record");
		for (const user of [INDEPENDENT, CHAIR]) {
			await login(page, user, PASSWORD);
			await gotoOpening(page, world.tender_reference);
			await expectScreen(page, "record");
			await page.locator('[data-testid="bop-sign"]').click();
			await expect(page.locator('[data-testid="bop-root"]')).toHaveAttribute("data-pending", "false", { timeout: 30_000 });
		}
		await expectScreen(page, "completed");
		await expectNextStep(page, "done", /after the last signature\.$/);
	});
});
