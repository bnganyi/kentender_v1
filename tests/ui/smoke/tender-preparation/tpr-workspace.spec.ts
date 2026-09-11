import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, HOPF, NOBODY, OFFICER, OUTSIDER, PASSWORD, collectConsoleErrors, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-DES-01 — Tender Preparation workspace (TPR-CHG-001 v0.6 §13.3, §14),
 * slice 5a. Officer sees the eligible handoff and can prepare; auditor
 * reads with no Prepare action; HoPF sees the approval-task table; an
 * outsider and an unassigned user get the inline Forbidden state (§13.9,
 * KT-STD-001 §3A) with no table painted. No Procuring Entity control, no
 * template selector, no create-without-Requisition action anywhere.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Tender Preparation — workspace", () => {
	test.afterAll(() => restoreSite());

	test("the officer sees the eligible Requisition with Prepare Tender, and the section titles in order", async ({ page }) => {
		const fixture = resetFixture("reset_workspace_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		await expect(page.locator(".kt-page-title")).toHaveText("Tender Preparation");
		await expect(page.locator(".kt-page-lede")).toHaveText("Prepare Tenders from authorised Procurement Requisitions.");
		const titles = await page.locator('[data-testid="tpr-shell"] .kt-card-title').allTextContents();
		expect(titles).toEqual(["Ready to prepare", "My Tenders", "Approval tasks"]);
		const row = page.locator('[data-testid="tpr-ready-row"]').first();
		await expect(row).toContainText("Open Tender");
		await expect(row.getByRole("button", { name: "Prepare Tender" })).toBeVisible();
		await expect(page.locator('[data-testid="tpr-approval-tasks"]')).toContainText("Visible only to the Head of Procurement Function.");
		// absence assertions (§13.3, §20)
		await expect(page.locator("text=/Procuring Entity/i")).toHaveCount(0);
		await expect(page.locator("select, [data-testid*='pe-switcher']").filter({ hasText: /Ministry|Entity/ })).toHaveCount(0);
		await expect(page.locator("button", { hasText: /Create Tender|New Tender/ })).toHaveCount(0);
		await expect(page.locator("text=/STD Library|Template selector/i")).toHaveCount(0);
		// reload keeps the same screen
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectReady(page, "workspace");
		expect(fixture.handoff).toBeTruthy();
		expect(errors).toEqual([]);
	});

	test("an auditor reads the workspace without a Prepare action; the head sees the approval-task table", async ({ page }) => {
		resetFixture("reset_submitted_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tpr-tender-row"]')).toHaveCount(1);
		await expect(page.getByRole("button", { name: "Prepare Tender" })).toHaveCount(0);
		await page.context().clearCookies();
		await login(page, HOPF, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tpr-approval-task-row"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="tpr-approval-task-row"]').getByRole("button", { name: "Open approval task" })).toBeVisible();
	});

	test("an outsider and an unassigned user get the inline Forbidden state, never a modal or a table", async ({ page }) => {
		resetFixture("reset_workspace_fixture");
		for (const user of [OUTSIDER, NOBODY]) {
			await page.context().clearCookies();
			await login(page, user, PASSWORD);
			await gotoTenderPreparation(page);
			await expectReady(page, "workspace");
			const forbidden = page.locator('[data-testid="tpr-forbidden"]');
			await expect(forbidden).toContainText("You do not have access to Tender Preparation.");
			await expect(forbidden).toContainText("Procurement Officer, Head of Procurement Function or Auditor");
			await expect(page.locator('[data-testid="tpr-ready-to-prepare"]')).toHaveCount(0);
			await expect(page.locator(".modal-dialog")).toHaveCount(0);
		}
	});

	test("a forced 500 shows the load-error state with a support reference and Try again", async ({ page }) => {
		resetFixture("reset_workspace_fixture");
		await login(page, OFFICER, PASSWORD);
		let fail = true;
		await page.route("**/api/method/kentender_procurement.tender_preparation.api.get_tender_preparation_workspace", (route) => {
			if (fail) return route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exception: "Forced failure" }) });
			return route.continue();
		});
		await gotoTenderPreparation(page);
		await expect(page.locator('[data-testid="tpr-error"]')).toContainText("Tender Preparation could not be loaded.");
		await expect(page.locator('[data-testid="tpr-error"]')).toContainText("Support reference: TPR-ERR-");
		fail = false;
		await page.getByRole("button", { name: "Try again" }).click();
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="tpr-ready-row"]')).toHaveCount(1);
	});
});
