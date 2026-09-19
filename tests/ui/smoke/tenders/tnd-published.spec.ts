import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, AUDITOR, HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7i — TPR-DES-09 Published Tender. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-09 Published Tender", () => {
	test.afterAll(() => restoreSite());

	test("HoPF: status panel, channels, addenda and inquiries, documents, the two actions", async ({ page }) => {
		const state = resetFixture("reset_published_fixture", { with_inquiry: true });
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Published — open");
		await expect(page.locator('[data-testid="tnd-published-facts"]')).toContainText("Published at");
		await expect(page.locator('[data-testid="tnd-effective-addenda"]')).toHaveText("1");
		await expect(page.locator('[data-testid="tnd-published-channels"] .kt-status')).toHaveText(["Confirmed", "Confirmed", "Confirmed", "Confirmed"]);
		await expect(page.locator('[data-testid="tnd-addenda-table"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="tnd-addenda-table"]')).toContainText("Delivery point clarified");
		await expect(page.locator('[data-testid="tnd-inquiries-table"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="tnd-inquiries-table"] .kt-status')).toHaveText("Awaiting response");
		await expect(page.locator('[data-testid="tnd-published-footer"] button')).toHaveText(["Recommend cancellation", "Prepare addendum"]);

		await page.locator('[data-testid="tnd-view-complete"]').click();
		await expect(page.locator('[data-testid="tnd-doc-frame"]')).toContainText(/Tender/i, { timeout: 30_000 });
		await page.locator('[data-testid="tnd-doc-close"]').click();
		await page.locator('[data-testid="tnd-published-channels"] .tnd-link-btn').first().click();
		await expect(page.locator('[data-testid="tnd-confirmation-view"]')).toContainText("Confirmed");
		await page.locator('[data-testid="tnd-cv-close"]').click();

		await page.locator('[data-testid="tnd-open-addendum"]').click();
		await expectReady(page, "addendum");
		await page.goBack();
		await expectReady(page, "published");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("AO: Cancel Tender only; officer: Prepare addendum only; auditor: no business action", async ({ page }) => {
		const state = resetFixture("reset_published_fixture");
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-published-footer"] button')).toHaveText(["Cancel Tender"]);
		await expect(page.locator('[data-testid="tnd-no-addenda"]')).toHaveText("No addenda have been issued.");

		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-published-footer"] button')).toHaveText(["Prepare addendum"]);

		await login(page, AUDITOR, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-no-action"]')).toHaveText("No business action available for this role.");
		await expect(page.locator('[data-testid="tnd-published-footer"] button')).toHaveCount(0);
	});

	test("submission ended: the badge, the ended deadline, no open-period action", async ({ page }) => {
		const state = resetFixture("reset_ended_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Submission period ended");
		await expect(page.locator('[data-testid="tnd-published-facts"]')).toContainText("(ended)");
		await expect(page.locator('[data-testid="tnd-prepare-addendum"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-cancel-tender"]')).toHaveCount(0);
	});
});
