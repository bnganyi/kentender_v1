import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { HOPF, OFFICER, OUTSIDER, PASSWORD, collectConsoleErrors, expectNoMessageDialog, expectReady, gotoTenderPreparation, resetFixture, restoreSite } from "./helpers";

/**
 * TPR-DES-02 — Start Tender (TPR-CHG-001 v0.6 §13.4), slice 5b: the dialog
 * over the workspace on /new/{handoff_id}; Prepare Tender creates one Draft
 * and routes to the editor; opening the route again shows the "already
 * linked" state with View Tender; a non-officer is not offered Prepare.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Tender Preparation — Start Tender", () => {
	test.afterAll(() => restoreSite());

	test("the officer prepares one Tender from the dialog and lands in the editor", async ({ page }) => {
		const fixture = resetFixture("reset_workspace_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, OFFICER, PASSWORD);
		await gotoTenderPreparation(page);
		await expectReady(page, "workspace");
		await page.locator('[data-testid="tpr-prepare-action-0"]').click();
		await expect(page).toHaveURL(new RegExp(`/tender-preparation/new/${fixture.handoff}$`));
		const dialog = page.locator('[data-testid="tpr-start-dialog"]');
		await expect(dialog.locator(".kt-dialog-title")).toHaveText("Prepare IT-equipment Tender");
		await expect(dialog.locator(".kt-label").allTextContents()).resolves.toEqual(["Requisition", "Requirement", "Package", "Method", "Template", "Official source"]);
		await expect(dialog).toContainText("IT Equipment — Open Tender · Version 1.1");
		await expect(dialog).toContainText("PPRA Standard Tender Document for Procurement of Goods");
		await expect(dialog).toContainText("This template release is fixed for this Tender. A later release will not change it.");
		await expect(dialog.locator("select")).toHaveCount(0); // no template/package/schema selector
		await page.locator('[data-testid="tpr-start-confirm"]').click();
		await expectReady(page, "editor");
		await expect(page).toHaveURL(/\/tender-preparation\/TPR-\d+$/);
		await expect(page.locator(".tpr-editor-header .kt-status")).toHaveText("Draft");
		await expectNoMessageDialog(page);
		// direct load of the start route again: already linked, View Tender offered
		await gotoTenderPreparation(page, `/new/${fixture.handoff}`);
		await expectReady(page, "start");
		await expect(page.locator('[data-testid="tpr-start-blocked"]')).toContainText("This Requisition is already linked to a Tender.");
		await page.locator('[data-testid="tpr-start-blocked"] a', { hasText: "View Tender" }).click();
		await expectReady(page, "editor");
		// browser back returns to the start route, forward returns to the editor
		await page.goBack({ waitUntil: "domcontentloaded" });
		await expectReady(page, "start");
		await page.goForward({ waitUntil: "domcontentloaded" });
		await expectReady(page, "editor");
		expect(errors).toEqual([]);
	});

	test("the head of procurement function is not offered Prepare Tender and an outsider is masked", async ({ page }) => {
		const fixture = resetFixture("reset_workspace_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoTenderPreparation(page, `/new/${fixture.handoff}`);
		await expectReady(page, "start");
		await expect(page.locator('[data-testid="tpr-start-confirm"]')).toBeDisabled();
		await page.context().clearCookies();
		await login(page, OUTSIDER, PASSWORD);
		await gotoTenderPreparation(page, `/new/${fixture.handoff}`);
		await expectReady(page, "start");
		await expect(page.locator('[data-testid="tpr-forbidden"]')).toBeVisible();
		await expect(page.locator('[data-testid="tpr-start-dialog"]')).toHaveCount(0);
	});
});
