import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { HOPF, OFFICER, PASSWORD, collectConsoleErrors, expectReady, gotoTenders, resetFixture, restoreSite } from "./helpers";

/** TPR-CHG-001 v0.12 (was v0.8) slice 7b — TPR-DES-02 Start Tender dialog. */

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
		await expect(dialog.locator(".dialog-title")).toContainText("Start this Tender?");
		await expect(dialog.locator(".kt-label")).toHaveText(["Purchase", "Requisition", "Quantity", "Approved value", "Method", "Latest delivery"]);
		await expect(dialog.locator('[data-testid="tnd-start-supported"]')).toContainText("Supported");
		await dialog.locator(".kt-disclosure-head").first().click();
		await expect(dialog.locator('[data-testid="tnd-start-checks"]')).toContainText("Method: Open Tender");
		// §10.3: the county-residents restriction is stated; the template details name the official source
		await expect(dialog.locator('[data-testid="tnd-start-checks"]')).toContainText("County-residents restriction:");
		await dialog.locator(".kt-disclosure-head").nth(1).click();
		await expect(dialog.locator('[data-testid="tnd-start-template"]')).toContainText("Official source:");
		await expect(dialog.locator('[data-testid="tnd-start-template"]')).not.toContainText("REQ-");
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

	test("a short window: the expanded dialog stays inside the viewport and its Start button can be reached", async ({ page }) => {
		const state = resetFixture("reset_start_fixture");
		await login(page, OFFICER, PASSWORD);
		await gotoTenders(page, `/new/${state.handoff}`);
		await expectReady(page, "start");
		await page.setViewportSize({ width: 1024, height: 560 }); // after the helper, which sets its own size
		const dialog = page.locator('[data-testid="tnd-start-dialog"] .dialog');
		await dialog.locator(".kt-disclosure-head").first().click();
		await dialog.locator(".kt-disclosure-head").nth(1).click();
		const box = await dialog.boundingBox();
		expect(box, "the dialog is drawn").not.toBeNull();
		expect(box!.y, "its top is not clipped above the window").toBeGreaterThanOrEqual(0);
		expect(box!.y + box!.height, "its bottom is not clipped below the window").toBeLessThanOrEqual(560);
		const start = page.locator('[data-testid="tnd-start-confirm"]');
		await start.scrollIntoViewIfNeeded();
		const button = await start.boundingBox();
		expect(button!.y + button!.height, "Start Tender is on screen once scrolled to").toBeLessThanOrEqual(560);
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
