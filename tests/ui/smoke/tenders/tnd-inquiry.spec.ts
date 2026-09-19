import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, OFFICER, PASSWORD, collectConsoleErrors, expectReady, pick, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7j — TPR-DES-11 Respond to addendum inquiry. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-11 Respond to addendum inquiry", () => {
	test.afterAll(() => restoreSite());

	test("the officer answers without seeing the candidate; the auditor sees the identity", async ({ page }) => {
		const state = resetFixture("reset_inquiry_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/inquiries/${state.inquiry}`);
		await expectReady(page, "inquiry");
		await expect(page.locator('[data-testid="tnd-inq-candidate"]')).toHaveText("Verified supplier account");
		await expect(page.locator('[data-testid="tnd-inq-question"]')).toContainText("clarified delivery point");
		await expect(page.locator('[data-testid="tnd-inq-effect"]')).toHaveText("The response will be sent to the candidate and recorded.");
		await pick(page, "tnd-inq-affects-yes");
		await expect(page.locator('[data-testid="tnd-inq-effect"]')).toContainText("without identifying who asked");
		await pick(page, "tnd-inq-affects-no");
		await page.locator('[data-testid="tnd-inq-send"]').click();
		await expect(page.locator('[data-testid="tnd-inq-error"]')).toContainText("5–2,000 characters");
		await page.locator('[data-testid="tnd-inq-response"]').fill("The clarified delivery point applies to all lots under this Tender. No other delivery terms change.");
		await page.locator('[data-testid="tnd-inq-send"]').click();
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-inquiries-table"] .kt-status')).toHaveText("Answered");

		await login(page, AUDITOR, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/inquiries/${state.inquiry}`);
		await expectReady(page, "inquiry");
		await expect(page.locator('[data-testid="tnd-inq-candidate"]')).toContainText("SUP-PW-0001");
		await expect(page.locator('[data-testid="tnd-inq-response-text"]')).toContainText("applies to all lots");
		await expect(page.locator('[data-testid="tnd-inq-send"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a late inquiry is preserved and cannot be answered", async ({ page }) => {
		const state = resetFixture("reset_inquiry_fixture", { late: true });
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/inquiries/${state.inquiry}`);
		await expectReady(page, "inquiry");
		await expect(page.locator('[data-testid="tnd-inq-late"]')).toContainText("The inquiry deadline has passed.");
		await expect(page.locator('[data-testid="tnd-inq-send"]')).toHaveCount(0);
	});
});
