import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { BOTH, HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7f — TPR-DES-06 HOPF approval. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-06 HOPF approval", () => {
	test.afterAll(() => restoreSite());

	test("return dialog validates inline, then returns; the officer sees the returned Draft", async ({ page }) => {
		const state = resetFixture("reset_awaiting_hopf_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "approval");
		await expect(page.locator('[data-testid="tnd-ready-to-approve"]')).toContainText("It does not publish the Tender.");
		await expect(page.locator('[data-testid="tnd-submitted-row"]')).toContainText("Version 1");
		await expect(page.locator('[data-testid="tnd-field-tender_title"]')).toHaveCount(0);

		await page.locator('[data-testid="tnd-return-for-correction"]').click();
		const dialog = page.locator('[data-testid="tnd-return-dialog"]');
		await dialog.locator('[data-testid="tnd-return-dialog-confirm"]').click();
		await expect(dialog.locator('[data-testid="tnd-return-dialog-field-error"]')).toBeVisible();
		await expect(page.locator(".modal.show")).toHaveCount(0);
		await dialog.locator('[data-testid="tnd-return-dialog-reason"]').fill("Increase past supply experience evidence detail — confirm the criterion is proportionate to purchase value.");
		await dialog.locator('[data-testid="tnd-return-dialog-select"]').selectOption("Supplier and contract requirements");
		await dialog.locator('[data-testid="tnd-return-dialog-confirm"]').click();
		await expectReady(page, "workspace");

		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page);
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="tnd-row-returned"]');
		await expect(row.locator(".kt-status")).toContainText("Returned to you");
		await row.locator('[data-testid="tnd-action-correct"]').click();
		await expectReady(page, "requirements");
		await expect(page.locator('[data-testid="tnd-returned-notice"]')).toContainText("Increase past supply experience evidence detail");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("approve dialog, then the AO decision row appears; the officer's record shows no decision control", async ({ page }) => {
		const state = resetFixture("reset_awaiting_hopf_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "approval");
		await page.locator('[data-testid="tnd-approve-package"]').click();
		await expect(page.locator('[data-testid="tnd-approve-dialog"]')).toContainText("The Accounting Officer must separately authorise publication.");
		await page.locator('[data-testid="tnd-approve-dialog-confirm"]').click();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tnd-row-approved"] .kt-status')).toContainText("Approved — awaiting publication authorisation");

		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "record");
		await expect(page.locator('[data-testid="tnd-approve-package"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-authorise-publication"]')).toHaveCount(0);
	});

	test("segregation: the actor who submitted cannot approve and sees no decision control", async ({ page }) => {
		const state = resetFixture("reset_segregation_fixture", { stage: "hopf" });
		await login(page, BOTH, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "approval");
		await expect(page.locator('[data-testid="tnd-segregation"]')).toContainText("Another Head of Procurement Function must decide it.");
		await expect(page.locator('[data-testid="tnd-approve-package"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-return-for-correction"]')).toHaveCount(0);
	});
});
