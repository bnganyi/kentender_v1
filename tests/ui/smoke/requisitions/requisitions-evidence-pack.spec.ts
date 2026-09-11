import { test } from "@playwright/test";

import { login } from "../../helpers/auth";
import { AUTHOR, HOD, HOPF, PASSWORD, expectReady, gotoRequisitions, resetFixture, restoreSite } from "./helpers";

/**
 * REQ-CHG-001 v1.6 Phase 5 (REQ-502) — one full-page screenshot per screen,
 * saved to docs/mvp-1-r1/06_requisitions/evidence/v1_6/ (Planning's own
 * precedent). Not a correctness check — every assertion this exercises is
 * already proven by the slice specs and the fidelity spec; this is a
 * capture pass only, kept as its own file so it never blocks the gate.
 */

const DIR = "docs/mvp-1-r1/06_requisitions/evidence/v1_6";

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Evidence capture", () => {
	test.afterAll(() => restoreSite());

	test("REQ-DES-01 Workspace", async ({ page }) => {
		resetFixture("reset_eligible_item_world");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page);
		await expectReady(page, "workspace");
		await page.screenshot({ path: `${DIR}/REQ-DES-01.png`, fullPage: true });
	});

	test("REQ-DES-02 Start Requisition", async ({ page }) => {
		const state = resetFixture<{ plan_item_id: string }>("reset_eligible_item_world");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/new/${state.plan_item_id}`);
		await expectReady(page, "start");
		await page.screenshot({ path: `${DIR}/REQ-DES-02.png`, fullPage: true });
	});

	test("REQ-DES-03/04 Editor steps 1-2", async ({ page }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_review_fixture");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await page.screenshot({ path: `${DIR}/REQ-DES-03.png`, fullPage: true });
		await page.locator('[data-testid="req-step-2"]').click();
		await page.screenshot({ path: `${DIR}/REQ-DES-04.png`, fullPage: true });
	});

	test("REQ-DES-05/06/07 Editor steps 3-5", async ({ page }) => {
		const state = resetFixture<{ requisition: string }>("reset_editor_review_fixture");
		await login(page, AUTHOR, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}`);
		await expectReady(page, "editor");
		await page.locator('[data-testid="req-step-3"]').click();
		await page.screenshot({ path: `${DIR}/REQ-DES-05.png`, fullPage: true });
		await page.locator('[data-testid="req-step-4"]').click();
		await page.screenshot({ path: `${DIR}/REQ-DES-06.png`, fullPage: true });
		await page.locator('[data-testid="req-step-5"]').click();
		await page.screenshot({ path: `${DIR}/REQ-DES-07.png`, fullPage: true });
	});

	test("REQ-DES-08 Department task", async ({ page }) => {
		const state = resetFixture<{ task: string }>("reset_department_task_fixture");
		await login(page, HOD, PASSWORD);
		await gotoRequisitions(page, `/department-task/${state.task}`);
		await expectReady(page, "department-task");
		await page.screenshot({ path: `${DIR}/REQ-DES-08.png`, fullPage: true });
	});

	test("REQ-DES-09 Procurement task", async ({ page }) => {
		const state = resetFixture<{ task: string }>("reset_procurement_task_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/procurement-task/${state.task}`);
		await expectReady(page, "procurement-task");
		await page.screenshot({ path: `${DIR}/REQ-DES-09.png`, fullPage: true });
	});

	test("REQ-DES-10 Authorised", async ({ page }) => {
		const state = resetFixture<{ requisition: string }>("reset_authorised_fixture");
		await login(page, HOPF, PASSWORD);
		await gotoRequisitions(page, `/${state.requisition}/authorised`);
		await expectReady(page, "authorised");
		await page.screenshot({ path: `${DIR}/REQ-DES-10.png`, fullPage: true });
	});
});
