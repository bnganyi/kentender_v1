import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUTHOR, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.6 Slice 3c-i — REQ-DES-03/04 Editor Steps 1-2 (Request and
 * drawdown; Equipment items) plus §13.6A's baseline-proposal notice, on the
 * REQ-402 world.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("REQ-DES-03/04 Editor — Request/drawdown and Equipment items", () => {
	test.afterAll(() => restoreSite());

	test("author saves the summary on Step 1, continues to Step 2, adds an item and sees the baseline proposal", async ({ page }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");

		await expect(page.locator(".req-eyebrow")).toHaveText("PROCUREMENT REQUISITIONS");
		await expect(page.locator('[data-testid="req-step-1"]')).toBeVisible();
		await page.locator("#req-title").fill("Playwright laptop deployment programme");
		await page.locator("#req-location").selectOption({ label: "Playwright — Requisitions Delivery Location" });
		await page.locator("#req-date").fill("2099-12-31");

		await page.locator('[data-testid="req-step-2"]').click();
		await expect(page.locator('[data-testid="req-add-item"]')).toBeVisible();
		await expect(page.locator('[data-testid="req-items-table"] tbody tr')).toHaveCount(0);

		await page.locator('[data-testid="req-add-item"]').click();
		const dialog = page.locator('[data-testid="req-item-dialog"]');
		await expect(dialog).toBeVisible();
		await page.locator("#item-source").selectOption({ index: 1 });
		await page.locator("#item-category").selectOption("Laptop");
		await page.locator("#item-name").fill("Business laptops");
		await page.locator("#item-use").fill("Playwright fixture deployment testing");
		await page.locator("#item-location").selectOption({ label: "Playwright — Requisitions Delivery Location" });
		await page.locator("#item-date").fill("2099-12-31");
		await page.locator('[data-testid="req-item-dialog-confirm"]').click();
		await expect(dialog).toHaveCount(0);

		await expect(page.locator('[data-testid="req-items-table"] tbody tr')).toHaveCount(1);
		const banner = page.locator('[id^="req-baseline-banner-"], [data-testid^="req-baseline-banner-"]');
		await expect(banner).toContainText("baseline characteristic");
		await expect(banner).toContainText("proposed for Business laptops");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("direct load, reload and back/forward all resolve the same editor state", async ({ page }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_fixture");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "editor");
		await expect(page.locator('[data-testid="req-step-1"]')).toBeVisible();

		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		await page.goBack();
		await expectReady(page, "editor");
		await page.goForward();
		await expectReady(page, "workspace");
	});
});
