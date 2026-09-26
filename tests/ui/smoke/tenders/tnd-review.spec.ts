import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { OFFICER, PASSWORD, collectConsoleErrors, expectGuidance, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.12 slice A — TPR-DES-05 Review and submit (§10.6, §10.17). */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-05 Review and submit", () => {
	test.afterAll(() => restoreSite());

	test("Needs attention: Your turn, blocked names the item and its fix; Submit is unavailable", async ({ page }) => {
		const state = resetFixture("reset_needs_attention_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/review`);
		await expectReady(page, "review");
		await expectGuidance(page, "DES-05-NEEDS-ATTENTION");
		// the guidance replaces the result panel and the duplicate disabled-submit explanation
		await expect(page.locator('[data-testid="tnd-review-result-blocked"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-must-fix"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-submit-for-approval"]')).toHaveCount(0);
		// the review note stays separate and does not block
		await expect(page.locator('[data-testid="tnd-review-notes"]')).toContainText("review note");
		await page.locator('[data-kt="next-step"] button', { hasText: "Review contract terms" }).click();
		await expectReady(page, "requirements");
		await expect(page.locator("#tnd-inspection_location")).toBeFocused();
	});

	test("Ready to submit: facts, previews, sections, submit dialog, then the workspace shows the new status", async ({ page }) => {
		const state = resetFixture("reset_draft_complete_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/review`);
		await expectReady(page, "review");
		await expectGuidance(page, "DES-05");
		await expect(page.locator('[data-testid="tnd-review-result-ready"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-review-notes"]')).toContainText("review note");
		await expect(page.locator('[data-testid="tnd-key-facts"] .kt-label')).toHaveText(["Requisition", "Quantity", "Approved value", "Method", "Submission deadline", "Tender security", "Reservation", "Latest delivery"]);
		await expect(page.locator(".kt-disclosure-title")).toHaveText(["Tender details", "Requirements from the authorised requisition", "Supplier pricing schedule", "Supplier and evaluation requirements", "Contract terms", "Technical evidence"]);
		// no officer price input anywhere: the schedule is completed by the supplier
		await page.locator('[data-testid="tnd-section-pricing"] .kt-disclosure-head').click();
		await expect(page.locator('[data-testid="tnd-section-pricing"]')).toContainText("Completed by supplier");
		await expect(page.locator('[data-testid="tnd-section-pricing"] input')).toHaveCount(0);

		await page.locator('[data-testid="tnd-preview-invitation"]').click();
		const doc = page.locator('[data-testid="tnd-document-dialog"]');
		await expect(doc.locator('[data-testid="tnd-doc-frame"]')).toContainText(/Invitation|Tender/i, { timeout: 30_000 });
		await page.locator('[data-testid="tnd-doc-close"]').click();
		await expect(doc).toHaveCount(0);

		await page.locator('[data-testid="tnd-submit-for-approval"]').click();
		await expect(page.locator('[data-testid="tnd-submit-dialog"]')).toContainText("Submit this Tender for approval?");
		// the eligible HOPF is named in the confirmation (§10.6)
		await expect(page.locator('[data-testid="tnd-submit-dialog"]')).toContainText("can return it or approve the package for publication review.");
		await page.locator('[data-testid="tnd-submit-dialog-confirm"]').click();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tnd-row-awaiting_approval"] .kt-status')).toHaveText("Awaiting procurement approval");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
