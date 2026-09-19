import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AO, HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectReady, expectSettled, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7k — TPR-DES-12 Cancel Tender. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-12 Cancel Tender", () => {
	test.afterAll(() => restoreSite());

	test("the HoPF records a recommendation; it changes no status", async ({ page }) => {
		const state = resetFixture("reset_cancel_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		await expect(page.locator('[data-testid="tnd-cancel-warning"]')).toContainText("Cancellation is final for this Tender.");
		await expect(page.locator('[data-testid="tnd-cancel-open-dialog"]')).toHaveCount(0);
		await page.locator('[data-testid="tnd-cancel-reason"]').fill("Delivery timeline no longer meets user-department need following supplier market changes.");
		await page.locator('[data-testid="tnd-recommend"]').click();
		await page.locator('[data-testid="tnd-recommend-dialog-confirm"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-recommendation"]')).toContainText("Recommended by");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Published — open");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the AO cancels with a ground and reason; the cancelled detail lists the obligations", async ({ page }) => {
		const state = resetFixture("reset_cancel_fixture", { recommended: true });
		await login(page, AO, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}/cancel`);
		await expectReady(page, "cancel");
		await expect(page.locator('[data-testid="tnd-recommendation"]')).toContainText("Recommended by");
		await expect(page.locator('[data-testid="tnd-consequences"] li')).toHaveCount(5);
		await page.locator('[data-testid="tnd-cancel-open-dialog"]').click();
		await expect(page.locator('[data-testid="tnd-cancel-error"]')).toContainText("20–2,000 characters");
		await page.locator('[data-testid="tnd-cancel-ground"]').selectOption("INADEQUATE_BUDGET");
		await page.locator('[data-testid="tnd-cancel-reason"]').fill("The confirmed budget available for this procurement is insufficient to proceed.");
		await page.locator('[data-testid="tnd-cancel-open-dialog"]').click();
		const dialog = page.locator('[data-testid="tnd-cancel-dialog"]');
		await expect(dialog).toContainText("Cancel this Tender?");
		await expect(dialog.locator("button")).toHaveText(["Keep Tender", "Cancel Tender"]);
		await dialog.locator('[data-testid="tnd-cancel-dialog-confirm"]').click();
		await expectSettled(page);
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Cancelled");
		await expect(page.locator('[data-testid="tnd-cancelled-facts"]')).toContainText("Inadequate budgetary provision");
		// one obligation per original channel, plus the PPRA report and candidate
		// notice rows whose rule is in force on the decision date (a real-clock
		// browser decision falls outside the seeded 2027 rule window)
		expect(await page.locator('[data-testid="tnd-obligations"] tbody tr').count()).toBeGreaterThanOrEqual(4);
		await page.reload();
		await expectReady(page, "cancel");
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Cancelled");
		await expect(page.locator('[data-testid="tnd-cancel-open-dialog"]')).toHaveCount(0);
	});

	test("the officer records evidence for an obligation; recorded rows lose their action", async ({ page }) => {
		const state = resetFixture("reset_cancelled_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/${state.tender_reference}`);
		await expectReady(page, "cancelled");
		const rows = page.locator('[data-testid="tnd-obligations"] tbody tr');
		await expect(rows).toHaveCount(6);
		const ppra = page.locator('[data-testid="tnd-obligations"] tbody tr', { hasText: "PPRA" }).first();
		await ppra.locator('[data-testid="tnd-record-evidence"]').click();
		await page.locator('[data-testid="tnd-ob-reference"]').fill("PPRA/CANCEL/2027/033");
		await page.locator('[data-testid="tnd-ob-confirm"]').click();
		await expectSettled(page);
		await expect(ppra.locator(".kt-status")).toHaveText("Recorded");
		await expect(ppra.locator('[data-testid="tnd-record-evidence"]')).toHaveCount(0);
	});
});
