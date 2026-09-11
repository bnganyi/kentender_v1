import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectNoMessageDialog, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-DES-06 — Approved Tender (TPR-CHG-001 v0.6 §10.4, §13.8), slice 5g:
 * the approved Version 2 with its digests, the Ready publication handoff,
 * both renders and the structured mappings; Reopen before publication (Head
 * of Procurement Function, unconsumed only) creates the Draft successor; a
 * consumed handoff removes the action; the officer and auditor read only.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

type Approved = { tender: string; tender_reference: string; publication_handoff: string };

test.describe("Tender Preparation — approved Tender", () => {
	test.afterAll(() => restoreSite());

	test("the head reaches the approved view from the workspace and reopens it before publication", async ({ page }) => {
		const fixture = resetFixture<Approved>("reset_approved_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="tpr-tender-row"]', { hasText: fixture.tender_reference });
		await expect(row).toContainText("Approved for publication");
		await row.locator("a", { hasText: fixture.tender_reference }).click();
		await expect(page).toHaveURL(new RegExp(`/tender-preparation/${fixture.tender}/approved$`));
		await expectReady(page, "approved");
		await expect(page.locator(".tpr-cap").first()).toContainText(`${fixture.tender_reference} · Version 2`);
		await expect(page.locator(".kt-label").allTextContents()).resolves.toEqual(["Approved by", "Requisition digest", "Template digest", "Package digest", "Publication handoff", "Publication consumption"]);
		await expect(page.locator(".tpr-ro-val", { hasText: "Ready · not yet consumed" })).toHaveCount(1);
		await expect(page.locator('[data-testid="tpr-consumption-status"]')).toHaveText("Awaiting downstream acknowledgment");
		await expect(page.locator(".tpr-tag", { hasText: "Invitation.pdf — digest verified" })).toHaveAttribute("href", /\/private\/files\//);
		await expect(page.locator(".tpr-tag", { hasText: "Issued Tender.pdf — digest verified" })).toHaveAttribute("href", /\/private\/files\//);
		await expect(page.locator(".tpr-tag.is-accent")).toHaveText(["Supplier-response schema · complete", "Evaluation contract · complete", "Contract-obligation projection · complete"]);
		await expect(page.locator('[data-testid="tpr-shell"] input, [data-testid="tpr-shell"] select, [data-testid="tpr-shell"] textarea')).toHaveCount(0);

		await page.locator('[data-testid="tpr-reopen"]').click();
		const dialog = page.locator('[data-testid="tpr-reopen-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Reopen before publication");
		await expect(dialog.locator("label")).toHaveText("Reason for reopening");
		await dialog.locator("textarea").fill("The submission deadline must move after the public holiday announcement.");
		await dialog.locator('[data-testid="tpr-reopen-dialog-confirm"]').click();
		await expect(page).toHaveURL(new RegExp(`/tender-preparation/${fixture.tender}$`));
		await expectReady(page, "editor");
		await expect(page.locator(".tpr-editor-ref")).toContainText("Version 3");
		await expect(page.locator(".tpr-editor-header .kt-status")).toHaveText("Draft");
		await expectNoMessageDialog(page);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a consumed publication handoff removes Reopen; the officer and auditor read without it", async ({ page }) => {
		const fixture = resetFixture<Approved>("reset_consumed_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenderPreparation(page, `/${fixture.tender}/approved`);
		await expectReady(page, "approved");
		await expect(page.locator('[data-testid="tpr-consumption-status"]')).toContainText("Consumed");
		await expect(page.locator('[data-testid="tpr-reopen"]')).toHaveCount(0);
		for (const user of [OFFICER, AUDITOR]) {
			await page.context().clearCookies();
			await login(page, user, PASSWORD);
			await gotoTenderPreparation(page, `/${fixture.tender}/approved`);
			await expectReady(page, "approved");
			await expect(page.locator(".kt-status.is-live").first()).toHaveText("Approved for publication");
			await expect(page.locator('[data-testid="tpr-reopen"]')).toHaveCount(0);
		}
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "approved");
		await expect(page.locator(".tpr-cap").first()).toContainText("Version 2");
	});
});
