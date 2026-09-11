import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { OFFICER, PASSWORD, collectConsoleErrors, expectNoMessageDialog, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-DES-04 — Review and readiness (TPR-CHG-001 v0.6 §10.1, §13.6), slice
 * 5e: the counts, the eight-row check table, the finding cards, both
 * server-rendered previews, and Submit for approval creating the Head of
 * Procurement Function task. A Draft with Blocking findings cannot submit.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

type Draft = { tender: string; tender_reference: string };

test.describe("Tender Preparation — review and readiness", () => {
	test.afterAll(() => restoreSite());

	test("a complete Draft is Ready with one Warning, previews render from the server, and Submit routes to the workspace", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_complete_draft_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await expect(page.locator('[data-testid="tpr-task-review"] .tpr-tag')).toContainText("Ready");
		await page.locator('[data-testid="tpr-task-review"]').click();
		await expect(page.locator(".kt-page-title", { hasText: "Review Tender" })).toBeVisible();
		await expect(page.locator(".kt-page-lede")).toHaveText("Resolve Blocking findings and review the complete Tender before submission.");
		await expect(page.locator('[data-testid="tpr-readiness-counts"] .kt-status').nth(0)).toHaveText("0 Blocking");
		await expect(page.locator('[data-testid="tpr-readiness-counts"] .kt-status').nth(1)).toHaveText("1 Warning");
		const rows = page.locator('[data-testid="tpr-readiness-summary"] tbody tr');
		await expect(rows).toHaveCount(8);
		await expect(rows.nth(0)).toContainText("Complete · digest verified");
		await expect(rows.nth(2)).toContainText("Complete · 1 item");
		await expect(rows.nth(6)).toContainText("Complete · generated");
		const warning = page.locator('[data-testid="tpr-finding"]');
		await expect(warning).toHaveCount(1);
		await expect(warning).toContainText("Warning");
		await expect(warning).toContainText("Confirm that manufacturer authorisation is proportionate for this item.");

		await page.locator('[data-testid="tpr-preview-invitation"]').click();
		const preview = page.locator('[data-testid="tpr-preview-dialog"]');
		await expect(preview.locator(".kt-dialog-title")).toHaveText("Invitation preview");
		await expect(preview.locator("iframe.tpr-preview-frame")).toBeVisible();
		await expect(preview).toContainText("digest");
		await preview.locator("button", { hasText: "Close" }).click();
		await expect(preview).toHaveCount(0);
		await page.locator('[data-testid="tpr-preview-tender"]').click();
		await expect(preview.locator(".kt-dialog-title")).toHaveText("Complete Tender preview");
		await expect(preview.locator("iframe.tpr-preview-frame")).toBeVisible();
		await preview.locator("button", { hasText: "Close" }).click();

		await expect(page.locator('[data-testid="tpr-submit"]')).toBeEnabled();
		await page.locator('[data-testid="tpr-submit"]').click();
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="tpr-tender-row"]', { hasText: fixture.tender_reference });
		await expect(row).toContainText("Submitted for approval");
		await expectNoMessageDialog(page);
		// the submitted Version is immutable for the officer
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await expect(page.locator(".tpr-editor-header .kt-status")).toHaveText("Submitted");
		await expect(page.locator("#tpr-tender-title")).toBeDisabled();
		await expect(page.locator('[data-testid="tpr-save-draft"]')).toBeDisabled();
		await page.locator('[data-testid="tpr-task-review"]').click();
		await expect(page.locator('[data-testid="tpr-submit"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a fresh Draft reports Blocking findings, cannot submit, and reload keeps the review screen's counts", async ({ page }) => {
		const fixture = resetFixture<Draft>("reset_draft_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}`);
		await expectReady(page, "editor");
		await expect(page.locator('[data-testid="tpr-task-review"] .tpr-tag')).toHaveText("Not run");
		await page.locator('[data-testid="tpr-task-review"]').click();
		await expect(page.locator('[data-testid="tpr-readiness-counts"] .kt-status').nth(0)).not.toHaveText("0 Blocking");
		await expect(page.locator('[data-testid="tpr-submit"]')).toBeDisabled();
		await expect(page.locator('[data-testid="tpr-readiness-summary"]')).toContainText("Blocking finding — see below");
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "editor");
		await expect(page.locator('[data-testid="tpr-task-review"] .tpr-tag')).toContainText("Blocking");
	});
});
