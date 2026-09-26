import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectGuidance, expectReady, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.12 slice E — TPR-DES-10 Prepare and issue addendum (§10.11, §10.17). */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("TPR-DES-10 Prepare and issue addendum", () => {
	test.afterAll(() => restoreSite());

	test("officer prepares a non-material draft and submits it for issue; the HOPF then holds it", async ({ page }) => {
		const state = resetFixture("reset_published_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");
		await page.locator('[data-testid="tnd-prepare-addendum"]').click();
		await expectReady(page, "addendum");
		await expect(page).toHaveURL(/\/addenda\/TDA-\d+$/);
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Draft addendum");
		await expect(page.locator('[data-testid="tnd-addendum-scope"]')).toContainText("An addendum cannot expand the purchase");
		await expect(page.locator('[data-testid="tnd-addendum-channels"] tbody tr')).toHaveCount(4);
		await expectGuidance(page, "DES-10-DRAFT");

		await page.locator('[data-testid="tnd-ad-reference"]').selectOption("delivery_location");
		await expect(page.locator('[data-testid="tnd-ad-previous"]')).not.toHaveText("—");
		await page.locator('[data-testid="tnd-ad-revised"]').fill("Playwright — Requisitions Delivery Location, Loading Bay 3");
		await page.locator('[data-testid="tnd-ad-reason"]').fill("Loading bay reassigned after warehouse reorganisation.");
		await page.locator('[data-testid="tnd-ad-materiality"]').fill("Same site; no change to scope, quantity, value or evaluation basis.");
		// the late-amendment rule is the server's (it depends on the real clock here)
		await expect(page.locator('[data-testid="tnd-deadline-rule"] h2')).toHaveText(/Submission deadline must be extended|The submission deadline is unchanged/);
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
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Awaiting issue");
		await expect(page.locator('[data-testid="tnd-ad-submit"]')).toHaveCount(0);
		await expect(page.locator('[data-kt="next-step"]')).toHaveAttribute("data-kind", "waiting");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("HoPF issues after the comparison; channel confirmation follows; the officer cannot issue", async ({ page }) => {
		const state = resetFixture("reset_addendum_awaiting_issue_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await expect(page.locator('[data-testid="tnd-ad-issue"]')).toHaveCount(0);

		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await expectGuidance(page, "DES-10-ISSUE");
		await expect(page.locator('[data-testid="tnd-addendum-comparison"] tbody')).toContainText("Loading Bay 3");
		await expect(page.locator('[data-testid="tnd-addendum-form"]')).toHaveCount(0);
		await page.locator('[data-testid="tnd-ad-issue"]').click();
		await expect(page.locator('[data-testid="tnd-issue-dialog"]')).toContainText("The issue decision is immutable.");
		await page.locator('[data-testid="tnd-issue-dialog-confirm"]').click();
		await expectSettled(page);
		await expectGuidance(page, "DES-10-CHANNELS");
		await expect(page.locator('[data-testid="tnd-addendum-facts"]')).toContainText("Issue decided by");
		await expect(page.locator('[data-testid="tnd-ad-confirm-channel"]')).toHaveCount(4);
		await expect(page.locator('[data-testid="tnd-ad-issue"]')).toHaveCount(0);
		await page.locator('[data-testid="tnd-ad-confirm-channel"]').first().click();
		await expect(page.locator('[data-testid="tnd-channel-dialog"] .kt-dialog-title')).toHaveText("Confirm addendum publication — State Portal");
		await expect(page.locator('[data-testid="tnd-channel-dialog"]')).toContainText(/Confirm only after ADD-.+ was publicly available through this channel\./);
	});

	test("HoPF returns a submitted addendum; the copied draft goes back to its drafter", async ({ page }) => {
		const state = resetFixture("reset_addendum_awaiting_issue_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await page.locator('[data-testid="tnd-ad-return"]').click();
		await page.locator('[data-testid="tnd-addendum-return-dialog-reason"]').fill("State the loading bay number.");
		await page.locator('[data-testid="tnd-addendum-return-dialog-confirm"]').click();
		await expectReady(page, "published");
	});

	test("a material change is blocked; the AO considers cancellation and closes the review; the officer discards", async ({ page }) => {
		const state = resetFixture("reset_material_addendum_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await expectGuidance(page, "DES-10-MATERIAL");
		await expect(page.locator('[data-kt="next-step"]')).toContainText("Cancel the Tender and start a newly governed Tender if procurement must continue.");
		await expect(page.locator('[data-testid="tnd-addendum-form"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-addendum-comparison"] tbody')).toContainText("300 Each");
		await expect(page.locator('[data-testid="tnd-ad-submit"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-view-cancellation-requirements"]')).toBeVisible();
		await page.locator('[data-kt="next-step"] button').first().click();
		await page.locator('[data-testid="tnd-review-request-dialog-reason"]').fill("Additional deployment sites require 50 more laptops; please consider cancellation.");
		await page.locator('[data-testid="tnd-review-request-dialog-confirm"]').click();
		await expectSettled(page);
		await expectGuidance(page, "DES-10-REVIEW-REQUESTED");
		await expect(page.locator('[data-kt="next-step"] button')).toHaveCount(0);

		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await expect(page.locator('[data-kt="next-step"] [data-testid="kt-next-step-headline"]')).toContainText("Consider the request to cancel");
		await expect(page.locator('[data-testid="tnd-ad-cancel-tender"]')).toBeVisible();
		await page.locator('[data-testid="tnd-ad-close-review"]').click();
		await page.locator('[data-testid="tnd-review-close-dialog-reason"]').fill("The additional sites will be served by a separate procurement.");
		await page.locator('[data-testid="tnd-review-close-dialog-confirm"]').click();
		await expectSettled(page);

		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/addenda/${state.addendum}`);
		await expectReady(page, "addendum");
		await expectGuidance(page, "DES-10-REVIEW-CLOSED");
		await expect(page.locator('[data-testid="tnd-review-closed-reason"]')).toContainText("separate procurement");
		await page.locator('[data-kt="next-step"] button', { hasText: "Discard addendum draft" }).click();
		await page.locator('[data-testid="tnd-discard-dialog-confirm"]').click();
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-addenda-table"]')).toHaveCount(0);
	});
});
