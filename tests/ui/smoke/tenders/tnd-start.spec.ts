import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.8 slice 7b — TPR-DES-02 Start Tender dialog. */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("TPR-DES-02 Start Tender dialog", () => {
	test.afterAll(() => restoreSite());

	test("supported requisition: facts, verdict, disclosures, Cancel, then Start creates the Draft", async ({ page }) => {
		const state = resetFixture("reset_start_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/new/${state.handoff}`);
		await expectReady(page, "start");
		const dialog = page.locator('[data-testid="tnd-start-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toContainText("Start this Tender?");
		await expect(dialog.locator(".kt-label")).toHaveText(["Purchase", "Requisition", "Quantity", "Approved value", "Method", "Latest delivery"]);
		await expect(dialog.locator('[data-testid="tnd-start-supported"]')).toContainText("Supported");
		await dialog.locator(".kt-disclosure-head").first().click();
		await expect(dialog.locator('[data-testid="tnd-start-checks"]')).toContainText("Method: Open Tender");
		await expect(dialog.locator("select, input[type=file]")).toHaveCount(0);

		await dialog.locator('[data-testid="tnd-start-cancel"]').click();
		await expectReady(page, "workspace");
		await page.goBack();
		await expectReady(page, "start");
		await page.locator('[data-testid="tnd-start-confirm"]').click();
		await expectReady(page, "details");
		await expect(page).toHaveURL(/\/tenders\/TND-MOH-2099-\d+\/details$/);
		await expect(page.locator('[data-testid="tnd-record-badge"]')).toHaveText("Draft Version 1");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("unsupported requisition: the critical notice, Start disabled, nothing created", async ({ page }) => {
		const state = resetFixture("reset_unsupported_start_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/new/${state.handoff}`);
		await expectReady(page, "start");
		await expect(page.locator('[data-testid="tnd-start-unsupported"]')).toContainText("not supported by the current IT-equipment Tender format");
		await expect(page.locator('[data-testid="tnd-start-confirm"]')).toBeDisabled();
		await expect(page.locator('[data-testid="tnd-start-supported"]')).toHaveCount(0);
	});

	test("a Head of Procurement Function can read the Start facts but cannot start", async ({ page }) => {
		const state = resetFixture("reset_start_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenders(page, `/new/${state.handoff}`);
		await expectReady(page, "start");
		await expect(page.locator('[data-testid="tnd-start-supported"]')).toBeVisible();
		await expect(page.locator('[data-testid="tnd-start-confirm"]')).toBeDisabled();
	});
});
