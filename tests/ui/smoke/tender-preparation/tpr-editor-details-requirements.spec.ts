import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, OFFICER, OUTSIDER, PASSWORD, collectConsoleErrors, expectNoMessageDialog, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-DES-03 · Task 1 and Task 2 (TPR-CHG-001 v0.6 §8.1, §8.2, §13.5), slice
 * 5c: the editor shell, the read-only context, the finite officer controls
 * with inline field errors, the review-only Task 2 panels and the Request
 * upstream correction dialog. Every inherited value is text, never an
 * input; the auditor reads with every control disabled; an outsider is
 * masked inline.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

type Draft = { tender: string; tender_reference: string; handoff: string };

test.describe("Tender Preparation — editor Task 1 and Task 2", () => {
	test.afterAll(() => restoreSite());

	test("Task 1 shows the read-only context, saves the officer controls, re-renders the task status and keeps the values across reload", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_draft_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await expect(page.locator(".tpr-editor-header .tpr-cap")).toHaveText("Tender Preparation");
		await expect(page.locator(".tpr-editor-header .kt-status")).toHaveText("Draft");
		await expect(page.locator(".tpr-editor-ref")).toContainText(fixture.tender_reference);
		await expect(page.locator(".tpr-editor-ref")).toContainText("Version 1");
		await expect(page.locator(".tpr-task-nav .tpr-task-nav-item")).toHaveCount(6);
		await expect(page.locator('[data-testid="tpr-task-1"]')).toHaveClass(/is-active/);
		// read-only context: kt-label + value pairs, never inputs
		const context = page.locator(".tpr-section").first();
		await expect(context.locator(".kt-card-title")).toHaveText("Read-only context");
		await expect(context.locator("input, select, textarea")).toHaveCount(0);
		await expect(context.locator('[data-testid="tpr-internal-context"]')).toContainText("Internal only — never rendered to bidders");
		await expect(context.locator(".tpr-ro-val").filter({ hasText: fixture.tender_reference })).toHaveCount(1);
		// template-fixed values are disabled inputs, the officer controls are enabled
		await expect(page.locator("input.kt-input[disabled]")).toHaveCount(2);
		await expect(page.locator("#tpr-tender-title")).toBeEnabled();
		await expect(page.locator('[data-testid="tpr-task-1"] .tpr-tag')).toContainText("to complete");
		// absence: no Procuring Entity or Fiscal Year control, no template selector
		await expect(page.locator("text=/Procuring Entity/i")).toHaveCount(0);
		await expect(page.locator("label", { hasText: /Fiscal Year|Template version/ })).toHaveCount(0);

		await page.locator("#tpr-tender-title").fill("Supply and delivery of business laptops");
		await page.locator("#tpr-issue-date").fill("2100-05-15");
		await page.locator("#tpr-clarification").fill("2100-05-27T17:00");
		await page.locator("#tpr-submission").fill("2100-06-05T11:00");
		await page.locator("#tpr-validity").fill("120");
		await page.locator("#tpr-security").fill("500000");
		await page.locator('.tpr-seg[aria-label="Pre-tender meeting"] label', { hasText: "No" }).click();
		await page.locator('[data-testid="tpr-save-draft"]').click();
		await expect(page.locator('[data-testid="tpr-task-1"] .tpr-tag')).toHaveText("Complete");
		await expect(page.locator('[data-testid="tpr-editor-inline-error"]')).toHaveCount(0);
		await expectNoMessageDialog(page);

		// a range violation is an inline field error, never a Message dialog
		await page.locator("#tpr-validity").fill("0");
		await page.locator('[data-testid="tpr-save-draft"]').click();
		await expect(page.locator('[data-testid="tpr-editor-inline-error"]')).toHaveText("Correct the highlighted fields.");
		await expect(page.locator(".tpr-field-error").first()).toBeVisible();
		await expectNoMessageDialog(page);
		await page.locator("#tpr-validity").fill("120");
		await page.locator('[data-testid="tpr-save-draft"]').click();
		await expect(page.locator('[data-testid="tpr-editor-inline-error"]')).toHaveCount(0);

		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "editor");
		await expect(page.locator("#tpr-tender-title")).toHaveValue("Supply and delivery of business laptops");
		await expect(page.locator("#tpr-validity")).toHaveValue("120");
		await expect(page.locator('[data-testid="tpr-task-1"] .tpr-tag')).toHaveText("Complete");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Task 2 is review-only with the inherited panels and stable IDs; Continue walks from Task 1 to Task 2", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_draft_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="tpr-continue"]').click();
		await expect(page.locator('[data-testid="tpr-task-2"]')).toHaveClass(/is-active/);
		const main = page.locator(".tpr-task-main");
		await expect(main.locator("input, select, textarea, [contenteditable='true']")).toHaveCount(0);
		await expect(main.locator("input[type='file']")).toHaveCount(0);
		await expect(main.locator(".kt-card-title").first()).toHaveText("Goods and delivery");
		await expect(main.locator('[data-testid="tpr-goods"] tbody tr')).toHaveCount(1);
		await expect(main.locator('[data-testid="tpr-goods"] tbody tr').first().locator("td").first()).toContainText("RQI-");
		await expect(main.locator('[data-testid="tpr-technical"] tbody tr').first().locator("td").first()).toContainText("TECH-");
		await expect(main.locator('[data-testid="tpr-warranty"]')).toContainText("months minimum warranty");
		await expect(main.locator(".kt-card-title", { hasText: "Acceptance requirements" })).toHaveCount(1);
		await expect(main.locator(".kt-card-title", { hasText: "Supporting materials" })).toHaveCount(1);
		await expect(page.locator('[data-testid="tpr-task-2"] .tpr-tag')).toContainText("Complete · 1 item");
		await expect(page.locator('[data-testid="tpr-save-draft"]')).toBeDisabled();
	});

	test("Request upstream correction needs a reason, releases the Requisition and stops the Version", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_draft_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="tpr-task-2"]').click();
		await page.locator('[data-testid="tpr-upstream-trigger"]').click();
		const dialog = page.locator('[data-testid="tpr-upstream-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Request upstream correction");
		await expect(dialog).toContainText("Tender Preparation cannot edit an authorised requirement. This Tender Version will be preserved.");
		await dialog.locator("textarea").fill("short");
		await dialog.locator('[data-testid="tpr-upstream-dialog-confirm"]').click();
		await expect(dialog.locator(".tpr-field-error")).toHaveText("A reason of 10–1,000 characters is required.");
		await dialog.locator("button", { hasText: "Cancel" }).click();
		await expect(dialog).toHaveCount(0);
		await page.locator('[data-testid="tpr-upstream-trigger"]').click();
		await page.locator('[data-testid="tpr-upstream-dialog"] textarea').fill("The quantity on the second item no longer matches the department's confirmed need.");
		await page.locator('[data-testid="tpr-upstream-dialog-confirm"]').click();
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="tpr-tender-row"]', { hasText: fixture.tender_reference });
		await expect(row).toContainText("Upstream correction required");
		// the handoff is released: it is offered again under Ready to prepare
		await expect(page.locator('[data-testid="tpr-ready-row"]')).toHaveCount(1);
		await expectNoMessageDialog(page);
		// the stopped Version is preserved read-only
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await expect(page.locator(".tpr-editor-header .kt-status")).toHaveText("Upstream correction required");
		await expect(page.locator('[data-testid="tpr-save-draft"]')).toBeDisabled();
		await expect(page.locator("#tpr-tender-title")).toBeDisabled();
	});

	test("the auditor reads every task with disabled controls and no actions; an outsider is masked inline", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_draft_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await expect(page.locator("#tpr-tender-title")).toBeDisabled();
		await expect(page.locator('[data-testid="tpr-save-draft"]')).toBeDisabled();
		await page.locator('[data-testid="tpr-task-2"]').click();
		await expect(page.locator('[data-testid="tpr-upstream-trigger"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tpr-goods"] tbody tr')).toHaveCount(1);
		await page.context().clearCookies();
		await login(page, OUTSIDER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await expect(page.locator('[data-testid="tpr-editor-not-found"]')).toContainText("Tender not found.");
		await expect(page.locator(".tpr-task-nav")).toHaveCount(0);
		await expect(page.locator(".modal-dialog")).toHaveCount(0);
	});
});
