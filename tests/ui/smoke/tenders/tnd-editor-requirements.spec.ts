import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { OFFICER, PASSWORD, collectConsoleErrors, expectReady, pick, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7d — TPR-DES-04 Draft: Supplier and contract requirements. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-04 Supplier and contract requirements", () => {
	test.afterAll(() => restoreSite());

	test("toggles, contract terms, evidence add/edit/remove and Review Tender", async ({ page }) => {
		const state = resetFixture("reset_draft_complete_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/requirements`);
		await expectReady(page, "requirements");
		await expect(page.locator('[data-testid="tnd-step-status-requirements"]')).toHaveText("Complete");
		await expect(page.locator('[data-testid="tnd-warranty-fixed"]')).toHaveText("Yes — required by authorised requisition");
		// the inherited warranty rule is never an input
		await expect(page.locator('[data-testid="tnd-toggle-warranty-yes"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-evidence-empty"]')).toHaveText("No additional evidence has been added.");

		await pick(page, "tnd-toggle-experience-no");
		await expect(page.locator('[data-testid="tnd-field-minimum_comparable_contracts"]')).toHaveCount(0);
		await pick(page, "tnd-toggle-experience-yes");
		await page.locator('[data-testid="tnd-field-minimum_comparable_contracts"]').fill("3");
		await page.locator('[data-testid="tnd-save-draft"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-step-status-requirements"]')).toHaveText("Complete");

		await page.locator('[data-testid="tnd-add-evidence"]').click();
		const dialog = page.locator('[data-testid="tnd-evidence-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Add supplier evidence");
		await dialog.locator('[data-testid="tnd-ev-confirm"]').click();
		await expect(dialog.locator(".tnd-field-error").first()).toBeVisible();
		await dialog.locator('[data-testid="tnd-ev-label"]').fill("Electrical compatibility certificate");
		await dialog.locator('[data-testid="tnd-ev-proves"]').selectOption({ index: 1 });
		await dialog.locator('[data-testid="tnd-ev-confirm"]').click();
		await expectSettled(page);
		await expect(dialog).toHaveCount(0);
		const rows = page.locator('[data-testid="tnd-evidence-table"] tbody tr');
		await expect(rows).toHaveCount(1);
		await expect(rows.first()).toContainText("Electrical compatibility certificate");
		await expect(rows.first()).toContainText("Certificate");

		await rows.first().locator('[data-testid="tnd-evidence-edit"]').click();
		await expect(page.locator('[data-testid="tnd-evidence-dialog"] .kt-dialog-title')).toHaveText("Edit supplier evidence");
		await page.locator('[data-testid="tnd-ev-label"]').fill("Electrical compatibility certificate (KEBS)");
		await page.locator('[data-testid="tnd-ev-confirm"]').click();
		await expectSettled(page);
		await expect(rows.first()).toContainText("(KEBS)");

		await page.reload();
		await expectReady(page, "requirements");
		await expect(page.locator('[data-testid="tnd-evidence-table"] tbody tr')).toHaveCount(1);
		await page.locator('[data-testid="tnd-evidence-remove"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-evidence-empty"]')).toBeVisible();

		await page.locator(".kt-disclosure-head").first().click();
		await expect(page.locator(".kt-disclosure-body ol li")).toHaveCount(4);
		await page.locator('[data-testid="tnd-continue"]').click();
		await expectReady(page, "review");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the Returned state carries the reviewer's comment above the task", async ({ page }) => {
		const state = resetFixture("reset_returned_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/requirements`);
		await expectReady(page, "requirements");
		await expect(page.locator('[data-testid="tnd-returned-notice"]')).toContainText("Returned for correction");
		await expect(page.locator('[data-testid="tnd-returned-notice"]')).toContainText("Confirm whether manufacturer authorisation is necessary");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Draft Version 2");
	});
});
