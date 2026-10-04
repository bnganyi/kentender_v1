import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUDITOR, AUTHOR, HOD, HOPF, PASSWORD, collectConsoleErrors, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.11 slices 4f–4i — REQ-DES-07 HoD review, REQ-DES-08/09
 * Procurement authorisation, REQ-DES-10 authorised record, REQ-DES-11
 * stopped work; each on its own reset, as the real actor.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

type World = { plan_item_id: string; requisition: string; department_task?: string; procurement_task?: string; handoff?: string; correction_request?: string };

test.describe("REQ-DES-07 … REQ-DES-11", () => {
	test.afterAll(() => restoreSite());

	test("HoD: return needs a reason; Submit to Procurement certifies and leaves a read-only task", async ({ page }) => {
		const world = resetFixture<World>("reset_department_task");
		const errors = collectConsoleErrors(page);
		await login(page, HOD, PASSWORD);
		await gotoRequisitions(page, `/department-task/${world.department_task}`);
		await expectReady(page, "department-task");
		await expect(page.getByTestId("req-badge")).toHaveText("Awaiting your approval");
		await expect(page.getByTestId("req-question")).toContainText("need and minimum requirements?");
		await expect(page.getByTestId("req-decision-chain")).toContainText("Awaiting your decision");

		await page.getByTestId("req-return").click();
		await page.getByTestId("req-return-dialog-confirm").click();
		await expect(page.getByTestId("req-return-dialog")).toContainText("Enter 20–1,000 characters.");
		await page.keyboard.press("Escape");

		await page.getByTestId("req-submit").click();
		await expectReady(page, "department-task");
		await expect(page.getByTestId("req-badge")).toHaveText("Submitted to Procurement");
		await expect(page.getByTestId("req-submit")).toHaveCount(0);
		await expect(page.getByTestId("req-return")).toHaveCount(0);
		await expect(page.getByTestId("req-other-actions")).toBeVisible();
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("the author cannot open the HoD decision", async ({ page }) => {
		const world = resetFixture<World>("reset_department_task");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/department-task/${world.department_task}`);
		await expectReady(page, "department-task");
		await expect(page.getByTestId("req-submit")).toHaveCount(0);
		await expect(page.getByTestId("req-question")).toHaveCount(0);
	});

	test("HOPF: the decision leads with its consequence; checks expand; confirm authorises once", async ({ page }) => {
		const world = resetFixture<World>("reset_procurement_task");
		const errors = collectConsoleErrors(page);
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/procurement-task/${world.procurement_task}`);
		await expectReady(page, "procurement-task");
		await expect(page.getByTestId("req-procurement-result")).toContainText("Ready to authorise");
		await expect(page.getByTestId("req-procurement-result")).toContainText("Authorising will reserve KES 50,000,000.00");
		await expect(page.getByTestId("req-funding")).toContainText("Available after authorisation");
		await expect(page.getByTestId("req-checks")).toHaveAttribute("data-open", "false");
		await page.getByTestId("req-checks-toggle").click();
		await expect(page.getByTestId("req-checks").locator("tbody tr")).toHaveCount(9);

		await page.getByTestId("req-authorise").click();
		const dialog = page.getByTestId("req-authorise-dialog");
		await expect(dialog).toContainText("Requisition value");
		await expect(dialog).toContainText("funding reservation");
		await page.getByTestId("req-authorise-confirm").click();
		await expectReady(page, "procurement-task");
		await expect(page.getByTestId("req-authorise")).toHaveCount(0);

		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-authorised")).toHaveAttribute("data-state", "Authorised");
		await expect(page.getByTestId("req-reservations").locator("tbody tr")).toHaveCount(2);
		await expect(page.getByTestId("req-revoke")).toBeVisible();
		await expect(page.getByTestId("req-continue-tender")).toHaveCount(0);
		expect(errors, errors.join(" | ")).toEqual([]);
	});

	test("HOPF: Change submitting department needs a reason; Return to department explains the copy", async ({ page }) => {
		const world = resetFixture<World>("reset_procurement_task");
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/procurement-task/${world.procurement_task}`);
		await expectReady(page, "procurement-task");
		await page.getByTestId("req-change-department").click();
		await expect(page.getByTestId("req-department-dialog")).toContainText("A copied Draft must be certified by the new submitting department");
		await page.keyboard.press("Escape");
		await page.getByTestId("req-return").click();
		await expect(page.getByTestId("req-return-dialog")).toContainText("a copied Draft will open for correction");
	});

	test("HOPF revokes an unconsumed authorisation; the record keeps its content and shows the reversal", async ({ page }) => {
		const world = resetFixture<World>("reset_authorised");
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await page.getByTestId("req-revoke").click();
		await page.getByTestId("req-revoke-dialog").locator("textarea").fill("The authorised warranty terms must be corrected before tendering.");
		await page.getByTestId("req-revoke-dialog-confirm").click();
		await expectReady(page, "record");
		await expect(page.getByTestId("req-authorised")).toHaveAttribute("data-state", "Revoked");
		await expect(page.getByTestId("req-badge")).toHaveText("Authorisation revoked");
		await expect(page.getByTestId("req-revoked")).toContainText("The authorised warranty terms must be corrected before tendering.");
		await expect(page.getByTestId("req-revoke")).toHaveCount(0);
	});

	test("consumed: Tender Preparation started replaces the status; revoke is absent", async ({ page }) => {
		const world = resetFixture<World>("reset_consumed");
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-consumed")).toContainText("Tender Preparation started");
		await expect(page.getByTestId("req-badge")).toHaveCount(0);
		await expect(page.getByTestId("req-revoke")).toHaveCount(0);
	});

	test("auditor: the authorised record offers navigation and Export only, and Export downloads the Version", async ({ page }) => {
		const world = resetFixture<World>("reset_authorised");
		await login(page, AUDITOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-revoke")).toHaveCount(0);
		await expect(page.getByTestId("req-continue-tender")).toHaveCount(0);
		const download = page.waitForEvent("download");
		await page.getByTestId("req-export").click();
		const file = await download;
		expect(file.suggestedFilename()).toMatch(/^REQ-.*\.json$/);
	});

	test("stopped: read-only page with the correction request and chain; no edit or decision", async ({ page }) => {
		const world = resetFixture<World>("reset_stopped");
		await login(page, HOD, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-stopped")).toHaveAttribute("data-status", "Open");
		await expect(page.getByTestId("req-badge")).toHaveText("Awaiting Planning correction");
		await expect(page.getByTestId("req-correction-request")).toContainText(world.correction_request || "");
		await expect(page.getByTestId("req-decision-chain")).toContainText("Planning correction requested · work stopped");
		await expect(page.getByTestId("req-start-new")).toHaveCount(0);
		await expect(page.getByTestId("req-editor")).toHaveCount(0);
	});

	test("closed without change: the outcome is shown and a fresh start is offered through its confirmation", async ({ page }) => {
		const world = resetFixture<World>("reset_stopped_closed");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${world.requisition}`);
		await expectReady(page, "record");
		await expect(page.getByTestId("req-badge")).toHaveText("Planning request closed without change");
		await page.getByTestId("req-start-new").click();
		await expect(page.getByTestId("req-fresh-start-dialog")).toContainText("Start a new requisition?");
	});
});
