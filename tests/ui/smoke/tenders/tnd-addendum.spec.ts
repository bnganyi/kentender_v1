import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectReady, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7j — TPR-DES-10 Prepare and issue addendum. */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("TPR-DES-10 Prepare and issue addendum", () => {
	test.afterAll(() => restoreSite());

	test("officer prepares a draft, sees materiality and the deadline rule, submits for issue", async ({ page }) => {
		const state = resetFixture("reset_published_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");
		await page.locator('[data-testid="tnd-prepare-addendum"]').click();
		await expectReady(page, "addendum");
		await expect(page).toHaveURL(/\/addenda\/TDA-\d+$/);
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Draft addendum");
		await expect(page.locator('[data-testid="tnd-addendum-draft-notice"]')).toContainText("An addendum cannot expand the purchase");
		await expect(page.locator('[data-testid="tnd-addendum-channels"] tbody tr')).toHaveCount(4);

		// a material reference blocks the addendum — the notice, no form, no submit
		await page.locator('[data-testid="tnd-ad-reference"]').selectOption("authorised_value");
		await expect(page.locator('[data-testid="tnd-addendum-material"]')).toContainText("This change cannot be made by addendum.");
		await expect(page.locator('[data-testid="tnd-ad-submit"]')).toBeDisabled();

		await page.locator('[data-testid="tnd-ad-reference"]').selectOption("delivery_location");
		await expect(page.locator('[data-testid="tnd-ad-previous"]')).not.toHaveText("—");
		await page.locator('[data-testid="tnd-ad-revised"]').fill("Playwright — Requisitions Delivery Location, Loading Bay 3");
		await page.locator('[data-testid="tnd-ad-reason"]').fill("Loading bay reassigned after warehouse reorganisation.");
		await page.locator('[data-testid="tnd-ad-materiality"]').fill("Same site; no change to scope, quantity, value or evaluation basis.");
		// the late-amendment rule is the server's (it depends on the real clock
		// here); a deadline-extension class always asks for the revised deadline
		await expect(page.locator('[data-testid="tnd-deadline-rule"]')).toContainText(/Submission deadline must be extended\.|The current submission deadline is unchanged\./);
		await page.locator('[data-testid="tnd-ad-change-class"]').selectOption("Submission deadline extension");
		await page.locator('[data-testid="tnd-ad-deadline"]').fill("2027-06-12T11:00");
		await page.locator('[data-testid="tnd-ad-save"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-command-error"]')).toHaveCount(0);
		await page.reload();
		await expectReady(page, "addendum");
		await expect(page.locator('[data-testid="tnd-ad-revised"]')).toHaveValue("Playwright — Requisitions Delivery Location, Loading Bay 3");
		await page.locator('[data-testid="tnd-ad-submit"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Submitted for issue");
		await expect(page.locator('[data-testid="tnd-ad-submit"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("HoPF issues; issue is immutable and channel confirmation follows; the officer cannot issue", async ({ page }) => {
		const state = resetFixture("reset_addendum_awaiting_issue_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await expect(page.locator('[data-testid="tnd-ad-issue"]')).toHaveCount(0);

		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await expect(page.locator('[data-testid="tnd-addendum-ready"]')).toContainText("Ready to issue.");
		await expect(page.locator('[data-testid="tnd-addendum-form"] textarea')).toHaveCount(0);
		await page.locator('[data-testid="tnd-ad-issue"]').click();
		await expect(page.locator('[data-testid="tnd-issue-dialog"]')).toContainText("Issue is immutable.");
		await page.locator('[data-testid="tnd-issue-dialog-confirm"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-addendum-confirming"]')).toBeVisible();
		await expect(page.locator('[data-testid="tnd-ad-confirm-channel"]')).toHaveCount(4);
		await expect(page.locator('[data-testid="tnd-ad-issue"]')).toHaveCount(0);
	});

	test("HoPF returns a submitted addendum for correction with a reason", async ({ page }) => {
		const state = resetFixture("reset_addendum_awaiting_issue_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await page.locator('[data-testid="tnd-ad-return"]').click();
		await page.locator('[data-testid="tnd-addendum-return-dialog-reason"]').fill("State the loading bay number.");
		await page.locator('[data-testid="tnd-addendum-return-dialog-confirm"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-addendum-returned"]')).toContainText("State the loading bay number.");
	});
});
