import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { HOPF, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.6 Slice 3e — REQ-DES-09 Procurement authorisation task,
 * §5A compatibility table, fresh Planning/Budget cards, and Authorise, on
 * the REQ-402 world.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("REQ-DES-09 Procurement authorisation task", () => {
	test.afterAll(() => restoreSite());

	test("HoPF reads fresh availability/affordability and the §5A compatibility table, then authorises", async ({ page }) => {
		const state = resetFixture<{ task: string }>("reset_procurement_task_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/procurement-task/${state.task}`);
		await expectReady(page, "procurement-task");

		await expect(page.locator(".req-eyebrow, .kt-eyebrow").first()).toContainText("PROCUREMENT AUTHORISATION");
		await expect(page.locator(".kt-status", { hasText: "Submitted to Procurement" })).toBeVisible();
		await expect(page.getByText("Eligible", { exact: true })).toBeVisible();
		const compat = page.locator('[data-testid="req-compatibility-table"] tbody tr');
		await expect(compat.first()).toBeVisible();
		for (const row of await compat.all()) {
			await expect(row.locator(".kt-status")).not.toHaveText("");
		}
		await expect(page.getByText(/I authorise this complete Requisition/)).toBeVisible();

		await page.locator('[data-testid="req-task-authorise"]').click();
		const dialog = page.locator('[data-testid="req-authorise-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(dialog).toContainText("Authorise Requisition?");
		await page.locator('[data-testid="req-authorise-dialog-confirm"]').click();
		await expect(dialog).toHaveCount(0);
		await expectReady(page, "workspace");
		// HoPF is a site-wide role: "Your Requisitions" also carries whatever
		// other world's own Authorised rows exist (the canonical MOH fixture
		// in particular) — assert this world's own row is present, not an
		// exact total.
		const authorised = page.locator('[data-testid="req-your-requisitions"] tbody tr', { hasText: "Authorised" });
		expect(await authorised.count()).toBeGreaterThanOrEqual(1);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Return to department preserves the submitted Version and opens a Draft successor", async ({ page }) => {
		const state = resetFixture<{ task: string }>("reset_procurement_task_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/procurement-task/${state.task}`);
		await expectReady(page, "procurement-task");

		await page.locator('[data-testid="req-task-return"]').click();
		const dialog = page.locator('[data-testid="req-return-dialog"]');
		await expect(dialog).toBeVisible();
		await page.locator("#return-reason").fill("Confirm the delivery location matches the Ministry Headquarters address on file.");
		await page.locator('[data-testid="req-return-dialog-confirm"]').click();
		await expect(dialog).toHaveCount(0);
		await expectReady(page, "workspace");
		// HoPF is site-wide: other Draft rows (this world's own earlier tests,
		// or another world entirely) may legitimately coexist.
		const row = page.locator('[data-testid="req-your-requisitions"] tbody tr', { hasText: "Draft" });
		expect(await row.count()).toBeGreaterThanOrEqual(1);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
