import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, OFFICER, PASSWORD, collectConsoleErrors, expectReady, pick, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7c — TPR-DES-03 Draft: Tender details. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-03 Tender details", () => {
	test.afterAll(() => restoreSite());

	test("inline field errors, a valid save, the meeting variants, the drawer, reload and back/forward", async ({ page }) => {
		const state = resetFixture("reset_draft_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/details`);
		await expectReady(page, "details");
		await expect(page.locator('[data-testid="tnd-step-status-details"]')).toHaveText("Needs attention");
		await expect(page.locator('[data-testid="tnd-context"]')).toContainText("Open Tender");
		// inherited facts are never inputs
		await expect(page.locator('[data-testid="tnd-context"] input')).toHaveCount(0);

		// a server-refused value renders inline, never in a Frappe dialog
		await page.locator('[data-testid="tnd-field-tender_security_amount"]').fill("0");
		await page.locator('[data-testid="tnd-save-draft"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-error-tender_security_amount"]')).toContainText("positive amount");
		await expect(page.locator(".modal.show")).toHaveCount(0);

		await page.locator('[data-testid="tnd-field-issue_date"]').fill("2027-05-15");
		await page.locator('[data-testid="tnd-field-clarification_deadline"]').fill("2027-05-27T17:00");
		await page.locator('[data-testid="tnd-field-submission_deadline"]').fill("2027-06-05T11:00");
		await page.locator('[data-testid="tnd-field-tender_security_amount"]').fill("500000");
		await pick(page, "tnd-meeting-yes");
		await expect(page.locator('[data-testid="tnd-field-meeting_datetime"]')).toBeVisible();
		await page.locator('[data-testid="tnd-field-meeting_datetime"]').fill("2027-05-22T10:00");
		await pick(page, "tnd-mode-online");
		await expect(page.locator('[data-testid="tnd-field-online_joining_information"]')).toBeVisible();
		await expect(page.locator('[data-testid="tnd-field-meeting_venue"]')).toHaveCount(0);
		await page.locator('[data-testid="tnd-field-online_joining_information"]').fill("Microsoft Teams — https://meet.example.test/tnd");
		await page.locator('[data-testid="tnd-save-draft"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-step-status-details"]')).toHaveText("Complete");

		await pick(page, "tnd-mode-physical");
		await expect(page.locator('[data-testid="tnd-field-meeting_venue"]')).toBeVisible();
		await page.locator('[data-testid="tnd-field-meeting_venue"]').selectOption({ index: 1 });
		await page.locator('[data-testid="tnd-save-draft"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-step-status-details"]')).toHaveText("Complete");

		await page.reload();
		await expectReady(page, "details");
		await expect(page.locator('[data-testid="tnd-field-tender_security_amount"]')).toHaveValue("500,000.00");
		await expect(page.locator('[data-testid="tnd-field-meeting_venue"]')).toBeVisible();

		await page.locator('[data-testid="tnd-open-drawer"]').click();
		const drawer = page.locator('[data-testid="tnd-drawer"]');
		await expect(drawer).toContainText("Authorised requisition");
		await expect(drawer.locator('[data-testid="tnd-drawer-context"]')).toContainText("Authorised value");
		await expect(drawer.locator('[data-testid="tnd-drawer-items"] tbody tr')).toHaveCount(1);
		await page.locator('[data-testid="tnd-drawer-close"]').click();
		await expect(drawer).toHaveCount(0);

		await page.locator('[data-testid="tnd-continue"]').click();
		await expectReady(page, "requirements");
		await page.goBack();
		await expectReady(page, "details");
		await page.goForward();
		await expectReady(page, "requirements");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("an auditor opens the same Draft as a record with no editable control", async ({ page }) => {
		const state = resetFixture("reset_draft_complete_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/details`);
		await expectReady(page, "record");
		await expect(page.locator('[data-testid="tnd-field-tender_title"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-save-draft"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-no-action"]')).toHaveText("No business action available for this role.");
	});
});
