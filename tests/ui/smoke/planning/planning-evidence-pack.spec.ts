import fs from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

import { login, loginAsAdministrator } from "../../helpers/auth";
import {
	ACCOUNTING_OFFICER,
	AUTHOR,
	FINANCE,
	HOD,
	NOBODY,
	PASSWORD,
	PLANNER,
	STATUTORY,
	expectReady,
	gotoDpp,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.12 Phase 8 (PLN-804) — the evidence pack: one 1440×1024
 * screenshot per artboard, taken from the live screen on the D13 fixture
 * world in the state each artboard depicts. Not a gate; the fidelity spec is
 * the assertion, this is the record. Output: docs/mvp-1-r1/04_planning/evidence/v1_12/.
 */

const OUT = path.resolve(__dirname, "../../../../docs/mvp-1-r1/04_planning/evidence/v1_12");
type State = { dpp_reference: string; need_entry_id: string; task: string; plan_reference: string; plan_item_id: string; publication: string };

test.describe.configure({ mode: "serial", timeout: 180_000 });

async function shot(page: import("@playwright/test").Page, name: string): Promise<void> {
	fs.mkdirSync(OUT, { recursive: true });
	await page.setViewportSize({ width: 1440, height: 1024 });
	await page.screenshot({ path: path.join(OUT, `${name}.png`), fullPage: true });
}

test.describe("v1.12 evidence pack", () => {
	test.afterAll(() => restoreSite());

	test("DES-01 workspace, DES-16 forbidden", async ({ page }) => {
		resetFixture("reset_accepted_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-actionable"]')).toBeVisible();
		await shot(page, "PLN-DES-01-workspace");
		await login(page, NOBODY, PASSWORD);
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await expect(page.locator('[data-testid="pln-forbidden"]')).toBeVisible();
		await shot(page, "PLN-DES-16-forbidden");
	});

	test("DES-02, 03, 04, 05 departmental plan screens", async ({ page }) => {
		const draft = resetFixture<State>("reset_dpp_fixture", { with_direct: true });
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, draft.dpp_reference);
		await expectReady(page, "dpp");
		await shot(page, "PLN-DES-02-draft-dpp");
		await gotoDpp(page, draft.dpp_reference, `/entry/${draft.need_entry_id}`);
		await expectReady(page, "dpp-entry");
		await shot(page, "PLN-DES-03-need-funding");
		await gotoDpp(page, draft.dpp_reference, "/add-direct");
		await expectReady(page, "dpp-entry");
		await shot(page, "PLN-DES-04-direct-requirement");
		const ready = resetFixture<State>("reset_dpp_fixture", { with_direct: true, funded: true });
		await login(page, HOD, PASSWORD);
		await gotoDpp(page, ready.dpp_reference);
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-certification"]')).toBeVisible();
		await shot(page, "PLN-DES-05-hod-submission");
	});

	test("DES-06 validation task", async ({ page }) => {
		const state = resetFixture<State>("reset_review_fixture");
		await login(page, PLANNER, PASSWORD);
		await gotoPlanning(page, `/dpp-review/${state.task}`);
		await expectReady(page, "dpp-review");
		await shot(page, "PLN-DES-06-dpp-validation");
	});

	test("DES-07, 08 workbench and formation dialog", async ({ page }) => {
		const state = resetFixture<State>("reset_workbench_fixture");
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${state.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await shot(page, "PLN-DES-07-draft-annual-plan");
		await page.locator('[data-testid="pln-form-items"]').click();
		await expect(page.locator('[data-testid="pln-form-dialog"]')).toBeVisible();
		await shot(page, "PLN-DES-08-form-plan-items-dialog");
	});

	test("DES-09, 09A plan item editors", async ({ page }) => {
		const single = resetFixture<State>("reset_plan_item_fixture");
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-plan-item/${single.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await shot(page, "PLN-DES-09-plan-item-editor");
		const combined = resetFixture<State>("reset_combined_item_fixture");
		await page.goto(`/app/procurement-plan-item/${combined.plan_item_id}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan-item");
		await shot(page, "PLN-DES-09A-combined-plan-item-editor");
	});

	test("DES-10, 11, 12, 15 finance and governance", async ({ page }) => {
		const finance = resetFixture<State>("reset_finance_fixture");
		await login(page, FINANCE, PASSWORD);
		await gotoPlanning(page, `/finance/${finance.task}`);
		await expectReady(page, "finance");
		await shot(page, "PLN-DES-10-plan-funding-confirmation");
		const ao = resetFixture<State>("reset_governance_fixture");
		await login(page, ACCOUNTING_OFFICER, PASSWORD);
		await gotoPlanning(page, `/review/${ao.task}`);
		await expectReady(page, "governance");
		await shot(page, "PLN-DES-11-accounting-officer-adoption");
		await page.locator('[data-testid="pgt-return"]').click();
		await expect(page.locator('[data-testid="pgt-return-dialog"]')).toBeVisible();
		await shot(page, "PLN-DES-15-return-dialog-ao");
		const statutory = resetFixture<State>("reset_statutory_fixture");
		await login(page, STATUTORY, PASSWORD);
		await gotoPlanning(page, `/review/${statutory.task}`);
		await expectReady(page, "governance");
		await shot(page, "PLN-DES-12-statutory-approval");
		await page.locator('[data-testid="pgt-return"]').click();
		await expect(page.locator('[data-testid="pgt-return-dialog"]')).toBeVisible();
		await shot(page, "PLN-DES-15-return-dialog-statutory");
	});

	test("DES-14, 14A, 13 active plan, cascade dialog, publication result", async ({ page }) => {
		const active = resetFixture<State>("reset_active_fixture");
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/annual-procurement-plan/${active.plan_reference}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "plan");
		await page.locator(`[data-testid="pln-active-schedule-${active.plan_item_id}"]`).click();
		await expect(page.locator('[data-testid="pln-schedule-card"]')).toBeVisible();
		await shot(page, "PLN-DES-14-active-annual-plan");
		await page.locator('[data-testid="pln-shift-bid_opening"]').click();
		await expect(page.locator('[data-testid="pln-shift-row-delivery_completion"]')).toBeVisible();
		await shot(page, "PLN-DES-14A-shift-schedule-dialog");
		await gotoPlanning(page, `/publication/${active.publication}`);
		await expectReady(page, "publication");
		await shot(page, "PLN-DES-13-publication-result");
		const failed = resetFixture<State>("reset_publication_failed_fixture");
		await loginAsAdministrator(page);
		await gotoPlanning(page, `/publication/${failed.publication}`);
		await expectReady(page, "publication");
		await expect(page.locator('[data-testid="pub-retry"]')).toBeVisible();
		await shot(page, "PLN-DES-13-publication-failed-retry");
	});
});
