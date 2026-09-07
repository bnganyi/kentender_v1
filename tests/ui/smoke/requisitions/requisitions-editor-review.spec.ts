import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUTHOR, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.6 Slice 3c-ii — REQ-DES-05/06/07 Editor Steps 3-5
 * (Technical and support; Services and acceptance; Review and submit), on
 * the REQ-402 world's already-complete fixture package.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("REQ-DES-05/06/07 Editor — Technical, services/acceptance, review", () => {
	test.afterAll(() => restoreSite());

	test("Step 3 shows the confirmed technical rows and the saved warranty panel", async ({ page }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_review_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");

		await page.locator('[data-testid="req-step-3"]').click();
		const rows = page.locator('[data-testid="req-technical-table"] tbody tr');
		await expect(rows).toHaveCount(5);
		await expect(rows.first().locator(".kt-status")).toHaveText("Confirmed");
		await expect(page.locator("#tech-warranty")).toHaveValue("24");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Step 4 shows the one acceptance row and no related-services table (No)", async ({ page }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_review_fixture");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="req-step-4"]').click();

		await expect(page.locator('[data-testid="req-services-table"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="req-acceptance-table"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="req-materials-table"]')).toHaveCount(0);
	});

	test("Step 5 renders the result banner and sends the Draft for department approval", async ({ page }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_review_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="req-step-5"]').click();

		const banner = page.locator('[data-testid="req-review-result"]');
		await expect(banner).toBeVisible();
		await expect(page.getByText("Equipment", { exact: true })).toBeVisible();

		await page.locator('[data-testid="req-send-for-approval"]').click();
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="req-your-requisitions"] tbody tr', { hasText: "Awaiting Department Approval" });
		await expect(row).toHaveCount(1);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
