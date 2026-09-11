import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { HOPF, OFFICER, OUTSIDER, PASSWORD, collectConsoleErrors, expectNoMessageDialog, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-DES-05 — Tender approval (TPR-CHG-001 v0.6 §10.3, §13.7), slice 5f:
 * the Head of Procurement Function opens the task from the workspace, reads
 * the immutable submitted Version (internal-only context visible, never
 * editable), previews the renders, returns with a reason (creating the
 * officer's Draft successor) or approves (creating the publication handoff).
 * The officer reads the task without approval actions; an outsider is masked.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

type Submitted = { tender: string; tender_reference: string; task: string };

test.describe("Tender Preparation — approval task", () => {
	test.afterAll(() => restoreSite());

	test("the head opens the task from the workspace, previews, and returns it with a reason", async ({ page }) => {
		const fixture = resetFixture<Submitted>("reset_submitted_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		await page.locator('[data-testid="tpr-approval-task-row"]').getByRole("button", { name: "Open approval task" }).click();
		await expect(page).toHaveURL(new RegExp(`/tender-preparation/task/${fixture.task}$`));
		await expectReady(page, "task");
		await expect(page.locator(".tpr-cap").first()).toContainText(`${fixture.tender_reference} · Version 1`);
		await expect(page.locator(".kt-status").first()).toHaveText("Submitted for approval");
		await expect(page.locator('[data-testid="tpr-approval-internal-context"]')).toContainText("Internal only — never rendered to bidders");
		await expect(page.locator('[data-testid="tpr-approval-readiness"]')).toContainText("0 Blocking");
		await expect(page.locator('[data-testid="tpr-approval-readiness"]')).toContainText("1 Warning — manufacturer authorisation proportionality");
		await expect(page.locator('[data-testid="tpr-shell"] input, [data-testid="tpr-shell"] select, [data-testid="tpr-shell"] textarea')).toHaveCount(0);
		await page.locator('[data-testid="tpr-approval-preview-tender"]').click();
		const preview = page.locator('[data-testid="tpr-preview-dialog"]');
		await expect(preview.locator(".kt-dialog-title")).toHaveText("Complete Tender preview");
		await expect(preview.locator("iframe.tpr-preview-frame")).toBeVisible();
		await preview.locator("button", { hasText: "Close" }).click();

		await page.locator('[data-testid="tpr-return"]').click();
		const dialog = page.locator('[data-testid="tpr-return-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Return for correction");
		await expect(dialog.locator("label")).toHaveText("Correction required");
		await dialog.locator('[data-testid="tpr-return-dialog-confirm"]').click();
		await expect(dialog.locator(".tpr-field-error")).toHaveText("A reason of 10–1,000 characters is required.");
		await dialog.locator("textarea").fill("Confirm whether manufacturer authorisation is necessary and update the evidence requirement.");
		await dialog.locator('[data-testid="tpr-return-dialog-confirm"]').click();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tpr-approval-task-row"]')).toHaveCount(0);
		await expectNoMessageDialog(page);
		// the officer receives a Draft successor, Version 2
		await page.context().clearCookies();
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await expect(page.locator(".tpr-editor-ref")).toContainText("Version 2");
		await expect(page.locator(".tpr-editor-header .kt-status")).toHaveText("Draft");
		await expect(page.locator("#tpr-tender-title")).toBeEnabled();
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the head approves the task and lands on the approved Tender; the officer and an outsider get no approval actions", async ({ page }) => {
		const fixture = resetFixture<Submitted>("reset_submitted_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/task/${fixture.task}`);
		await expectReady(page, "task");
		await expect(page.locator('[data-testid="tpr-approve"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tpr-return"]')).toHaveCount(0);
		await page.context().clearCookies();
		await login(page, OUTSIDER, PASSWORD);
		await gotoTenderPreparation(page, `/task/${fixture.task}`);
		await expectReady(page, "task");
		await expect(page.locator('[data-testid="tpr-task-not-found"]')).toContainText("Tender not found.");
		await page.context().clearCookies();
		await login(page, HOPF, PASSWORD);
		await gotoTenderPreparation(page, `/task/${fixture.task}`);
		await expectReady(page, "task");
		await expect(page.locator('[data-testid="tpr-approve"]')).toBeEnabled();
		await page.locator('[data-testid="tpr-approve"]').click();
		await expect(page).toHaveURL(new RegExp(`/tender-preparation/${fixture.tender}/approved$`));
		await expectReady(page, "approved");
		await expect(page.locator(".kt-status.is-live").first()).toHaveText("Approved for publication");
		await expectNoMessageDialog(page);
		// back returns to the (now closed) task, forward to the approved view
		await page.goBack({ waitUntil: "domcontentloaded" });
		await expectReady(page, "task");
		await expect(page.locator('[data-testid="tpr-approve"]')).toHaveCount(0);
		await page.goForward({ waitUntil: "domcontentloaded" });
		await expectReady(page, "approved");
	});
});
