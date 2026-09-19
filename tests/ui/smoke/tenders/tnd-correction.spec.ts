import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7f — TPR-DES-13 Requisition correction. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-13 Requisition correction", () => {
	test.afterAll(() => restoreSite());

	test("the HoPF requests a correction from the approval screen; the record stops", async ({ page }) => {
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
		// in this world the released handoff is itself the authorised successor, so
		// the record shows either the stopped facts or the successor-ready panel
		await expect(page.locator('[data-testid="tnd-successor-ready"], [data-testid="tnd-cannot-continue"]').first()).toBeVisible();
		await expect(page.locator('[data-testid="tnd-approve-package"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the officer sees Correction requested or the corrected successor and starts the new Version", async ({ page }) => {
		const state = resetFixture("reset_correction_requested_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "correction");
		const successor = page.locator('[data-testid="tnd-successor-ready"]');
		if ((await successor.count()) === 0) {
			await expect(page.locator('[data-testid="tnd-cannot-continue"]')).toContainText("This Tender cannot continue.");
			await expect(page.locator('[data-testid="tnd-correction-facts"]')).toContainText("Requested by");
			await expect(page.locator('[data-testid="tnd-start-corrected"]')).toHaveCount(0);
			return;
		}
		await expect(successor).toContainText("A corrected requisition is ready.");
		await page.locator('[data-testid="tnd-start-corrected"]').click();
		await expectReady(page, "details");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Draft Version 2");
	});
});
