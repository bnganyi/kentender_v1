import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUDITOR,
	AUTHOR,
	NOBODY,
	OUTSIDER,
	PASSWORD,
	collectConsoleErrors,
	expectReady,
	gotoRequisitions,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * REQ-CHG-001 v1.6 Slice 3a — REQ-DES-01 workspace, per role, in a real
 * browser on the REQ-402 world (own Fiscal Year 2099-2100).
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("REQ-DES-01 Procurement Requisitions workspace", () => {
	test.afterAll(() => restoreSite());

	test("author is offered Prepare Requisition, clicks it and reaches the Start screen", async ({ page }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_eligible_item_world");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");

		await expect(page.locator(".kt-page-title")).toHaveText("Procurement Requisitions");
		const ready = page.locator('[data-testid="req-ready-to-prepare"]');
		await expect(ready).toBeVisible();
		const rows = page.locator('[data-testid="req-ready-row"]');
		await expect(rows).toHaveCount(1);
		await expect(page.locator('[data-testid="req-your-requisitions"] tbody tr')).toHaveCount(0);

		await page.locator('[data-testid="req-prepare-action-0"]').click();
		await expectReady(page, "start");
		await expect(page).toHaveURL(new RegExp(`/procurement-requisitions/new/${state.plan_item_id}$`));
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("auditor reads the register but is offered no work at all", async ({ page }) => {
		resetFixture("reset_department_task_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUDITOR, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");

		// A site-wide Auditor reads every Requisition on the site (not scoped
		// to this world's own Fiscal Year), so other worlds' own rows (the
		// canonical MOH fixture in particular) may legitimately also be
		// present — scope the assertion to this world's own row by status.
		await expect(page.locator('[data-testid="req-ready-to-prepare"]')).toHaveCount(0);
		const awaiting = page.locator('[data-testid="req-your-requisitions"] tbody tr', { hasText: "Awaiting Department Approval" });
		expect(await awaiting.count()).toBeGreaterThanOrEqual(1);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("a stale Frappe Role without a responsibility assignment gets the Forbidden panel and nothing else", async ({ page }) => {
		await login(page, NOBODY, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");

		const card = page.locator('[data-testid="req-forbidden"]');
		await expect(card).toContainText("You do not have access to Procurement Requisitions.");
		await expect(card).toContainText(
			"This area needs one of these responsibilities: Departmental Author, Head of User Department, Head of Procurement Function or Auditor. Ask your KenTender administrator to assign one in System setup."
		);
		await expect(page.locator('[data-testid="req-ready-to-prepare"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="req-your-requisitions"]')).toHaveCount(0);
	});

	test("an author from another department sees no eligible item and no prepare action", async ({ page }) => {
		resetFixture("reset_eligible_item_world");
		const errors = collectConsoleErrors(page);
		await login(page, OUTSIDER, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");

		await expect(page.locator('[data-testid="req-ready-to-prepare"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="req-your-requisitions"] tbody tr')).toHaveCount(0);
		await expect(page.locator('[data-testid="req-forbidden"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
