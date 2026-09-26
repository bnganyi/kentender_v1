import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectGuidance, expectReady, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.12 slice G — TPR-DES-12 Cancel Tender (§10.13, §10.17). */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-12 Cancel Tender", () => {
	test.afterAll(() => restoreSite());

	test("the HoPF records a recommendation; it changes no status", async ({ page }) => {
		const state = resetFixture("reset_cancel_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		await expect(page.locator('[data-testid="tnd-cancel-warning"]')).toContainText("Cancellation is final for this Tender.");
		await expect(page.locator('[data-testid="tnd-cancel-open-dialog"]')).toHaveCount(0);
		await page.locator('[data-testid="tnd-cancel-reason"]').fill("Delivery timeline no longer meets user-department need following supplier market changes.");
		await page.locator('[data-testid="tnd-recommend"]').click();
		await page.locator('[data-testid="tnd-recommend-dialog-confirm"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-recommendation"] h2')).toHaveText("HOPF recommendation");
		await expect(page.locator('[data-testid="tnd-recommendation"]')).toContainText("Head of Procurement Function ·");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Published — open");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the AO decides with a ground and reason; the cancelled detail groups the obligations", async ({ page }) => {
		const state = resetFixture("reset_cancel_fixture", { recommended: true });
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		await expectGuidance(page, "DES-12-AO");
		await expect(page.locator('[data-testid="tnd-recommendation"]')).toContainText("HOPF recommendation");
		await expect(page.locator('[data-testid="tnd-consequences"] li')).toHaveCount(5);
		await page.locator('[data-testid="tnd-cancel-open-dialog"]').click();
		await expect(page.locator('[data-testid="tnd-cancel-error"]')).toContainText("20–2,000 characters");
		await page.locator('[data-testid="tnd-cancel-ground"]').selectOption("INADEQUATE_BUDGET");
		await page.locator('[data-testid="tnd-cancel-reason"]').fill("The confirmed budget available for this procurement is insufficient to proceed.");
		await page.locator('[data-testid="tnd-cancel-open-dialog"]').click();
		const dialog = page.locator('[data-testid="tnd-cancel-dialog"]');
		await expect(dialog).toContainText("Cancel this Tender?");
		await expect(dialog.locator("button")).toHaveText(["Keep Tender", "Cancel Tender"]);
		await dialog.locator('[data-testid="tnd-cancel-dialog-confirm"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Cancelled");
		await expect(page.locator('[data-testid="tnd-cancelled-facts"]')).toContainText("Inadequate budgetary provision");
		await expectGuidance(page, "DES-12-CANCELLED-READER");
		// the notice channels are one obligation; the PPRA report and candidate
		// notices appear when their rule is in force on the decision date
		await expect(page.locator('[data-testid="tnd-obligations"] tbody tr').first()).toContainText("Cancellation notices");
		await expect(page.locator('[data-testid="tnd-obligations"] button')).toHaveCount(0);
		await page.reload();
		await expectReady(page, "cancel");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Cancelled");
		await expect(page.locator('[data-testid="tnd-cancel-open-dialog"]')).toHaveCount(0);
	});

	test("the officer holds the compliance work and records the PPRA report", async ({ page }) => {
		const state = resetFixture("reset_cancelled_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "cancelled");
		await expectGuidance(page, "DES-12-CANCELLED-HOLDER");
		const rows = page.locator('[data-testid="tnd-obligations"] tbody tr');
		await expect(rows.first()).toContainText("Cancellation notices");
		await expect(rows.first()).toContainText("0 of 4 recorded");
		const ppra = page.locator('[data-testid="tnd-obligation-record_ppra_report_evidence"]');
		await ppra.locator('[data-testid="tnd-record-ppra-report-evidence"]').click();
		await page.locator('[data-testid="tnd-ob-reference"]').fill("PPRA/CANCEL/2027/033");
		await page.locator('[data-testid="tnd-ob-confirm"]').click();
		await expectSettled(page);
		await expect(ppra.locator(".kt-status")).toHaveText("Recorded");
		await expect(ppra.locator("button")).toHaveCount(0);
		// the cancellation notices stay with the officer, who can record them too
		await expect(page.locator('[data-testid="tnd-record-cancellation-notice-evidence"]')).toBeVisible();
	});

	test("the AO reads a cancellation-review request and closes it with a reason", async ({ page }) => {
		const state = resetFixture("reset_material_addendum_fixture", { review: "requested" });
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		await expectGuidance(page, "DES-12-REVIEW");
		await expect(page.locator('[data-testid="tnd-review-request"]')).toContainText("Procurement Officer");
		await expect(page.locator('[data-testid="tnd-review-proposal"] tbody')).toContainText("Each");
		await expect(page.locator('[data-testid="tnd-cancel-reason"]')).toHaveCount(0);
		await page.locator('[data-testid="tnd-close-review"]').click();
		await page.locator('[data-testid="tnd-review-close-dialog-reason"]').fill("The additional sites will be served by a separate procurement.");
		await page.locator('[data-testid="tnd-review-close-dialog-confirm"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-review-request"]')).toHaveCount(0);
		await expectGuidance(page, "DES-12-AO");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Published — open");
	});
});
