import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectGuidance, expectReady, expectSettled, gotoTenders, pick, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.12 slice F — TPR-DES-11 Respond to supplier clarification (§10.12, §10.17). */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-11 Respond to supplier clarification", () => {
	test.afterAll(() => restoreSite());

	test("an ordinary answer goes to every registered candidate without naming the asker", async ({ page }) => {
		const state = resetFixture("reset_clarification_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/clarifications/${state.clarification}`);
		await expectReady(page, "clarification");
		await expectGuidance(page, "DES-11");
		await expect(page.locator('[data-testid="tnd-clarification-candidate"]')).toHaveText("Registered Tender candidate");
		await expect(page.locator('[data-testid="tnd-clarification-question"]')).toContainText("different customers");
		await expect(page.locator('[data-testid="tnd-clar-audience"]')).toContainText("A general answer will not identify who asked.");
		await page.locator('[data-testid="tnd-clar-send"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-clar-error-response"]')).toContainText("5–2,000 characters");
		await expect(page.locator(".modal.show")).toHaveCount(0);
		await page.locator('[data-testid="tnd-clar-response"]').fill("Yes. The Tender requires two comparable contracts and does not require both contracts to be from the same customer.");
		await page.locator('[data-testid="tnd-clar-send"]').click();
		await expectReady(page, "published");
		await expect(page.locator('[data-testid="tnd-clarifications-table"] .kt-status')).toHaveText("Answered");
		await page.goBack();
		await expectReady(page, "clarification");
		await expect(page.locator('[data-testid="tnd-clar-recorded-response"]')).toContainText("same customer");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("an answer that would change the published Tender waits for an addendum", async ({ page }) => {
		const state = resetFixture("reset_clarification_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/clarifications/${state.clarification}`);
		await expectReady(page, "clarification");
		await page.locator('[data-testid="tnd-clar-response"]').fill("The delivery point will change to the 3rd Floor Procurement Stores.");
		await pick(page, "tnd-clar-changes-yes");
		await expectGuidance(page, "DES-11-PUBLISHED-CHANGE");
		await expect(page.locator('[data-kt="next-step"]')).toContainText("A clarification cannot change requirements, criteria, dates or supplier obligations on its own.");
		await expect(page.locator('[data-testid="tnd-clar-audience"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="tnd-clar-send"]')).toHaveCount(0);
		await page.locator('[data-kt="next-step"] button', { hasText: "Prepare addendum" }).click();
		await expectReady(page, "addendum");
		await page.goBack();
		await expectReady(page, "clarification");
		// the answer is kept, nothing was sent, and the required addendum is named
		await expect(page.locator('[data-testid="tnd-clar-response"]')).toHaveValue(/3rd Floor Procurement Stores/);
		await expect(page.locator('[data-testid="tnd-clar-required-addendum"]')).toContainText("ADD-");
		await expectGuidance(page, "DES-11-PUBLISHED-CHANGE");
	});

	test("a failed candidate notice: the protected recipient, Retry notice, the Tender stays open", async ({ page }) => {
		const state = resetFixture("reset_clarification_fixture", { failed: true });
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/clarifications/${state.clarification}`);
		await expectReady(page, "clarification");
		await expectGuidance(page, "DES-11-DELIVERY-FAILURE");
		const failed = page.locator('[data-testid="tnd-clar-notices"] tr[data-status="Failed"]');
		await expect(failed).toContainText("procurement@failed-delivery.example");
		await expect(failed.locator("td.is-num")).toHaveText("3");
		await page.locator('[data-kt="next-step"] button', { hasText: "Retry notice" }).click();
		await expectSettled(page);
		// the same notice (same recipient, same content) is retried: one more
		// attempt on it and no new notice. Its result is the transport's own —
		// this site has no outgoing email account, so the attempt fails again —
		// and a Sent result would never be shown as Delivered.
		const row = page.locator('[data-testid="tnd-clar-notices"] tbody tr').filter({ hasText: "failed-delivery" });
		await expect(row.locator("td.is-num")).toHaveText("4");
		await expect(page.locator('[data-testid="tnd-clar-notices"] tbody tr')).toHaveCount(2);
		await expect(row.locator(".kt-status")).not.toHaveText("Delivered");
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "published");

		await login(page, AUDITOR, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/clarifications/${state.clarification}`);
		await expectReady(page, "clarification");
		await expect(page.locator('[data-testid="tnd-clar-notices"]')).toContainText("procurement@failed-delivery.example");
		await expect(page.locator('[data-kt="next-step"] button')).toHaveCount(0);
	});
});
