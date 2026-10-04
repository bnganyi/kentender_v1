import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { OFFICER, PASSWORD, collectConsoleErrors, expectGuidance, expectReady, pick, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.12 slice A — TPR-DES-04 Draft: Supplier and contract requirements (§10.5, §10.17). */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-04 Supplier and contract requirements", () => {
	test.afterAll(() => restoreSite());

	test("toggles, contract terms, evidence add/edit/remove and Review Tender", async ({ page }) => {
		const state = resetFixture("reset_draft_complete_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/requirements`);
		await expectReady(page, "requirements");
		await expectGuidance(page, "DES-04");
		await expect(page.locator('[data-testid="tnd-progress"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-warranty-fixed"]')).toHaveText("Yes — required by authorised requisition");
		// the reservation evidence the verified rule generates is read-only, with no rule identifier
		const reservation = page.locator('[data-testid="tnd-reservation-evidence"]');
		await expect(reservation).toHaveCount(1);
		await expect(reservation.locator("input")).toHaveCount(0);
		// the inherited warranty rule is never an input
		await expect(page.locator('[data-testid="tnd-toggle-warranty-yes"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-evidence-empty"]')).toHaveText("No additional evidence has been added.");

		await pick(page, "tnd-toggle-experience-no");
		await expect(page.locator('[data-testid="tnd-field-minimum_comparable_contracts"]')).toHaveCount(0);
		await pick(page, "tnd-toggle-experience-yes");
		await expect(page.locator('[data-testid="tnd-experience-group"]')).toContainText("Use only experience requirements that are necessary and proportionate for this purchase.");
		await page.locator('[data-testid="tnd-field-minimum_comparable_contracts"]').fill("3");
		await page.locator('[data-testid="tnd-save-draft"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-editor-error"]')).toHaveCount(0);

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
		await expect(page.locator('[data-testid="tnd-ev-confirm"]')).toHaveText("Save changes");
		await page.locator('[data-testid="tnd-ev-confirm"]').click();
		await expectSettled(page);
		await expect(rows.first()).toContainText("(KEBS)");

		await page.reload();
		await expectReady(page, "requirements");
		await expect(page.locator('[data-testid="tnd-evidence-table"] tbody tr')).toHaveCount(1);
		// removal is confirmed first, naming the evidence and the linked requirement
		await page.locator('[data-testid="tnd-evidence-remove"]').click();
		const confirm = page.locator('[data-testid="tnd-remove-evidence-dialog"]');
		await expect(confirm).toContainText("Remove this evidence?");
		await expect(confirm).toContainText("(KEBS)");
		await confirm.locator('[data-testid="tnd-remove-evidence-dialog-confirm"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-evidence-empty"]')).toBeVisible();

		await page.locator('[data-testid="tnd-disclosure-evaluation"]').click();
		await expect(page.locator(".kt-disclosure-body ol li")).toHaveCount(4);
		// the carried requirements open in place, never in a drawer
		await page.locator('[data-testid="tnd-disclosure-carried"]').click();
		await expect(page.locator('[data-testid="tnd-carried-summary"] > div')).toHaveCount(4);
		await page.locator('[data-testid="tnd-show-full-requirements"]').click();
		await expect(page.locator('[data-testid="tnd-requirement-tables"] table')).toHaveCount(4);
		await expect(page.locator('[data-testid="tnd-drawer"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-show-full-requirements"]')).toHaveText("Hide full requirements");
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
		await expectGuidance(page, "DES-13-RETURNED");
	});
});
