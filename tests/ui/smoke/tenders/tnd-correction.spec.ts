import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectGuidance, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.12 slice H — TPR-DES-13 Requisition correction (§10.14, §10.17). */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-13 Requisition correction", () => {
	test.afterAll(() => restoreSite());

	test("the HoPF requests a correction from the approval screen; the record stops and waits on the author", async ({ page }) => {
		const state = resetFixture("reset_awaiting_hopf_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "approval");
		await page.locator('[data-testid="tnd-request-correction"]').click();
		const dialog = page.locator('[data-testid="tnd-correction-dialog"]');
		await expect(dialog).toContainText("Request a requisition correction?");
		await dialog.locator('[data-testid="tnd-correction-dialog-reason"]').fill("The authorised battery-runtime requirement must be corrected before this Tender can continue.");
		await dialog.locator('[data-testid="tnd-correction-dialog-confirm"]').click();
		await expectReady(page, "correction");
		await expectGuidance(page, "DES-13-CORRECTION");
		await expect(page.locator('[data-testid="tnd-approve-package"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("correction requested: the facts, the current owner, page links only; no business action", async ({ page }) => {
		const state = resetFixture("reset_correction_requested_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "correction");
		await expectGuidance(page, "DES-13-CORRECTION");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Requisition correction requested");
		const facts = page.locator('[data-testid="tnd-correction-facts"]');
		await expect(facts).toContainText("Requested by");
		await expect(facts).toContainText("Stopped Version");
		await expect(facts).toContainText("Departmental Author");
		await expect(page.locator('[data-testid="tnd-view-requisition"]')).toBeVisible();
		await expect(page.locator('[data-testid="tnd-start-corrected"]')).toHaveCount(0);
		await page.locator('[data-testid="tnd-view-history"]').click();
		await expectReady(page, "history");
		await page.goBack();
		await expectReady(page, "correction");
	});

	test("corrected successor available: Your turn to start the corrected Version, which opens its Draft", async ({ page }) => {
		const state = resetFixture("reset_correction_requested_fixture", { successor: true });
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "correction");
		await expectGuidance(page, "DES-13-SUCCESSOR");
		await expect(page.locator('[data-testid="tnd-successor-facts"]')).toContainText("Basis of stopped Tender Version 1");
		await expect(page.locator('[data-testid="tnd-successor-consequence"]')).toHaveText("Starting creates a new Draft Version 2. Version 1 stays stopped and unchanged in history.");
		await page.locator('[data-testid="tnd-start-corrected"]').click();
		await expectReady(page, "details");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Draft Version 2");
		await expectGuidance(page, "DES-03");
	});
});
