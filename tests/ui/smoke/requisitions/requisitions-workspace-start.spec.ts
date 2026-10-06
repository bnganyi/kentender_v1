import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, AUTHOR, HOD, NOBODY, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.11 slices 4a/4b — REQ-DES-01 workspace and REQ-DES-02 start
 * dialog, per role, on the Playwright world (FY 2099-2100). Every reference
 * comes from the fixture result; nothing is hardcoded.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

type World = { plan_item_id: string; requisition?: string; department_task?: string };

test.describe("REQ-DES-01 workspace and REQ-DES-02 start", () => {
	test.afterAll(() => restoreSite());

	test("author: Ready to start → dialog (direct load, reload, Escape, back) → Start opens the Draft", async ({ page }) => {
		const world = resetFixture<World>("reset_workspace_ready");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");

		await expect(page.getByTestId("req-your-work")).toHaveCount(0);
		const row = page.getByTestId("req-ready-row");
		await expect(row).toHaveCount(1);
		await expect(row).toContainText(world.plan_item_id);
		await expect(row).toContainText("250 Each");
		await expect(page.getByTestId("req-register-empty")).toHaveText("You have no requisitions yet.");

		await page.getByTestId("req-start").click();
		const dialog = page.getByTestId("req-start-dialog");
		await expect(dialog).toBeVisible();
		await expect(page).toHaveURL(new RegExp(`/procurement-requisitions/new/${world.plan_item_id}$`));
		await expect(dialog).toContainText("Start this requisition?");
		await expect(dialog).toContainText("Reserved for");
		await expect(dialog).not.toContainText("County requirement");
		await expect(dialog).toContainText("will submit this combined departmental request.");
		// the workspace stays underneath the dialog
		await expect(page.getByTestId("req-workspace")).toBeVisible();

		await page.reload();
		await expectReady(page, "start");
		await expect(dialog).toBeVisible();
		await page.keyboard.press("Escape");
		await expectReady(page, "workspace");
		await expect(dialog).toHaveCount(0);
		await page.goBack();
		await expectReady(page, "start");
		await expect(dialog).toBeVisible();

		await page.getByTestId("req-start-confirm").click();
		await expectReady(page, "record");
		await expect(page.getByTestId("req-editor")).toBeVisible();
		await expect(page.getByTestId("req-badge")).toHaveText("Draft");

		// back on the workspace the Draft leads Your work; the Ready row is gone
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		await expect(page.getByTestId("req-work-row")).toContainText("Complete request details");
		await expect(page.getByTestId("req-work-row").locator(".btn")).toHaveText("Continue");
		await expect(page.getByTestId("req-ready")).toHaveCount(0);
		await expect(page.getByTestId("req-register-row")).toHaveCount(1);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("filters narrow the register as typed and Clear filters restores it", async ({ page }) => {
		resetFixture("reset_draft");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		const rows = page.getByTestId("req-register-row");
		await expect(rows).toHaveCount(1);
		await page.getByTestId("req-filter-search").fill("no such requisition");
		await expect(page.getByTestId("req-register-no-match")).toBeVisible();
		await expect(page.getByTestId("req-filter-search")).toHaveValue("no such requisition");
		await page.getByTestId("req-clear-filters").click();
		await expect(rows).toHaveCount(1);
		await page.getByTestId("req-filter-status").selectOption("Authorised");
		await expect(page.getByTestId("req-register-no-match")).toBeVisible();
		await expect(page.getByTestId("req-filter-status")).toHaveValue("Authorised");
	});

	test("HoD: the assigned decision leads with Review and routes to the task", async ({ page }) => {
		const world = resetFixture<World>("reset_department_task");
		await login(page, HOD, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		const work = page.getByTestId("req-work-row");
		await expect(work).toContainText("Review departmental requisition");
		await expect(page.getByTestId("req-count-approvals")).toHaveText(/Approvals [1-9]/);
		await work.locator(".btn").click();
		await expect(page).toHaveURL(new RegExp(`/procurement-requisitions/department-task/${world.department_task}$`));
	});

	test("auditor: register only — no work, no Ready to start, no Start", async ({ page }) => {
		resetFixture("reset_draft");
		await login(page, AUDITOR, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		await expect(page.getByTestId("req-your-work")).toHaveCount(0);
		await expect(page.getByTestId("req-start")).toHaveCount(0);
		await expect(page.getByTestId("req-register")).toBeVisible();
	});

	test("no responsibility: the inline forbidden state and nothing else", async ({ page }) => {
		await login(page, NOBODY, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		await expect(page.getByTestId("req-state-forbidden")).toContainText("You do not have access to Procurement Requisitions.");
		await expect(page.getByTestId("req-register")).toHaveCount(0);
		await expect(page.getByTestId("req-start")).toHaveCount(0);
	});

	test("a failed load shows the load-failure state and Try again recovers", async ({ page }) => {
		resetFixture("reset_workspace_ready");
		await login(page, AUTHOR, PASSWORD);
		let fail = true;
		await page.route("**/api/method/kentender_procurement.procurement_requisitions.api.get_requisition_workspace**", (route) =>
			fail ? route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ exception: "boom" }) }) : route.continue()
		);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		await expect(page.getByTestId("req-state-error")).toContainText("Procurement Requisitions could not be loaded.");
		await expect(page.getByTestId("req-register")).toHaveCount(0);
		fail = false;
		await page.getByTestId("req-try-again").click();
		await expectReady(page, "workspace");
		await expect(page.getByTestId("req-ready-row")).toHaveCount(1);
	});

	test("narrow layout keeps Ready-to-start meaning as a labelled row card", async ({ page }) => {
		resetFixture("reset_workspace_ready");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page);
		await page.setViewportSize({ width: 390, height: 844 });
		await expectReady(page, "workspace");
		const card = page.locator(".req-row-card").first();
		await expect(card).toBeVisible();
		await expect(card).toContainText("Departments");
		await expect(card).toContainText("Still available");
		await expect(card).toContainText("Needed by");
		await expect(card.getByRole("button", { name: "Start requisition" })).toBeVisible();
		const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
		expect(overflow).toBeLessThanOrEqual(0);
	});
});
