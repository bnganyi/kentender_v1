import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, HOD, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.6 Slice 3d — REQ-DES-08 Department approval task, plus the
 * shared Return-for-correction dialog, on the REQ-402 world.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("REQ-DES-08 Department approval task", () => {
	test.afterAll(() => restoreSite());

	test("HoD reads the read-only certification screen and submits to Procurement", async ({ page }) => {
		const state = resetFixture<{ task: string }>("reset_department_task_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOD, PASSWORD);
		await gotoRequisitions(page, `/department-task/${state.task}`);
		await expectReady(page, "department-task");

		await expect(page.locator(".req-eyebrow, .kt-eyebrow").first()).toContainText("DEPARTMENT APPROVAL");
		await expect(page.locator(".kt-status", { hasText: "Awaiting Department Approval" })).toBeVisible();
		await expect(page.locator('[data-testid="req-task-drawdown-table"]')).toBeVisible();
		await expect(page.locator('[data-testid="req-task-items-table"] tbody tr')).toHaveCount(1);
		await expect(page.locator('[data-testid="req-task-technical-table"] tbody tr')).toHaveCount(5);
		await expect(page.getByText(/I confirm that this Requisition/)).toBeVisible();

		await page.locator('[data-testid="req-task-submit"]').click();
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="req-your-requisitions"] tbody tr', { hasText: "Submitted to Procurement" });
		await expect(row).toHaveCount(1);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Return for correction preserves the reviewed Version and opens a Draft successor", async ({ page }) => {
		const state = resetFixture<{ task: string; requisition: string }>("reset_department_task_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, HOD, PASSWORD);
		await gotoRequisitions(page, `/department-task/${state.task}`);
		await expectReady(page, "department-task");

		await page.locator('[data-testid="req-task-return"]').click();
		const dialog = page.locator('[data-testid="req-return-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(dialog).toContainText("Return Requisition for correction?");
		await page.locator("#return-reason").fill("The delivery location does not match the Ministry Headquarters address on file.");
		await page.locator('[data-testid="req-return-dialog-confirm"]').click();
		await expect(dialog).toHaveCount(0);
		await expectReady(page, "workspace");
		const row = page.locator('[data-testid="req-your-requisitions"] tbody tr', { hasText: "Draft" });
		await expect(row).toHaveCount(1);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("an auditor — not a HoD for either contributing unit — gets a masked not-found on the task read, never the certification screen", async ({ page }) => {
		// `get_department_approval_task` gates on `require_hod_for_any(masked=True)`
		// only — a department task is the acting HoD's own decision record, not
		// a site-wide-readable artifact (unlike the Authorised/handoff read).
		const state = resetFixture<{ task: string }>("reset_department_task_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoRequisitions(page, `/department-task/${state.task}`);
		await expectReady(page, "department-task");
		await expect(page.locator('[data-testid="req-task-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="req-task-return"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="req-task-submit"]')).toHaveCount(0);
	});
});
