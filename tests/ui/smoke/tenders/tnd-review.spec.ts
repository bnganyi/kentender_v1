import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7e — TPR-DES-05 Review and submit. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-05 Review and submit", () => {
	test.afterAll(() => restoreSite());

	test("Needs attention: the Must fix with its route, Submit disabled with the reason", async ({ page }) => {
		const state = resetFixture("reset_needs_attention_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/review`);
		await expectReady(page, "review");
		await expect(page.locator('[data-testid="tnd-review-result-blocked"]')).toContainText("Needs attention.");
		await expect(page.locator('[data-testid="tnd-must-fix"]').first()).toContainText("inspection and acceptance location");
		await expect(page.locator('[data-testid="tnd-submit-for-approval"]')).toBeDisabled();
		await expect(page.locator('[data-testid="tnd-submit-blocked-text"]')).toHaveText("Fix the item above before submitting.");
		await page.locator('[data-testid="tnd-must-fix"] button').first().click();
		await expectReady(page, "requirements");
	});

	test("Ready to submit: facts, previews, sections, submit dialog, then the workspace shows the new status", async ({ page }) => {
		const state = resetFixture("reset_draft_complete_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/review`);
		await expectReady(page, "review");
		await expect(page.locator('[data-testid="tnd-review-result-ready"]')).toContainText("Ready to submit.");
		await expect(page.locator('[data-testid="tnd-review-notes"]')).toContainText("review note");
		await expect(page.locator('[data-testid="tnd-key-facts"] .kt-kpi-card')).toHaveCount(9);
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
		await page.locator('[data-testid="tnd-submit-dialog-confirm"]').click();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tnd-row-awaiting_approval"] .kt-status')).toHaveText("Awaiting procurement approval");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
