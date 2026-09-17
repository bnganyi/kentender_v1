import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUDITOR,
	AUTHOR,
	HOD,
	OUTSIDER,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	gotoDpp,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.18 (PLN18-303) — the Departmental Plan screens' own
 * behaviour: real §5.1/§5.1.4/§12.2 commands and their interactive
 * re-render. Structural/copy fidelity against U02–U06 lives in
 * `design-fidelity/planning-fidelity.spec.ts` (U03/U03-notproceeding only
 * for this row — see that file's header for what is deferred and why).
 *
 * Replaces the v1.12 `planning-dpp.spec.ts` / `planning-dpp-review.spec.ts`
 * (deleted with this row).
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("PLN18-303 Departmental Plan screens", () => {
	test.afterAll(() => restoreSite());

	test("author completes Need funding, then marks it not proceeding and restores it", async ({ page }) => {
		const state = resetFixture<{ dpp_reference: string; need_entry_id: string }>("reset_dpp_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference, `/entry/${state.need_entry_id}`);
		await expectReady(page, "dpp-entry");

		await page.locator('[data-testid="dpp-f-budget-line"]').selectOption({ index: 0 });
		await page.locator('[data-testid="dpp-f-amount"]').fill("80000000");
		await page.locator('[data-testid="dpp-editor-save"]').click();
		await expectReady(page, "dpp");
		await expect(page.locator(`[data-testid="dpp-entry-${state.need_entry_id}"]`)).toContainText("Ready");

		// U03's own dialog — SetNeedPlanningDisposition, not bundled into save
		await page.locator(`[data-testid="dpp-entry-action-${state.need_entry_id}"]`).click();
		await expectReady(page, "dpp-entry");
		await page.locator('[data-testid="dpp-editor-not-proceed"]').click();
		await expect(page.locator('[data-testid="pln-not-proceed-dialog"]')).toBeVisible();
		await page.locator('[data-testid="pln-not-proceed-reason"]').fill("The department will pursue this requirement in a later annual planning cycle.");
		await page.locator('[data-testid="pln-not-proceed-confirm"]').click();
		await expectReady(page, "dpp");

		// U03-notproceeding — a distinct section, excluded from the main table
		await expect(page.locator('[data-testid="dpp-entries"] tbody tr')).toHaveCount(0);
		const section = page.locator('[data-testid="dpp-not-proceeding-entries"]');
		await expect(section).toContainText("Not proceeding this financial year");
		await expect(section).toContainText("Reason: The department will pursue this requirement in a later annual planning cycle.");

		await page.locator(`[data-testid="dpp-restore-${state.need_entry_id}"]`).click();
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-not-proceeding-entries"]')).toHaveCount(0);
		await expect(page.locator(`[data-testid="dpp-entry-${state.need_entry_id}"]`)).toContainText("Funding incomplete");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("author adds a direct requirement and later edits it", async ({ page }) => {
		const state = resetFixture<{ dpp_reference: string }>("reset_dpp_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference, "/add-direct");
		await expectReady(page, "dpp-entry");
		await expect(page.locator(".kt-page-title")).toHaveText("Add direct requirement");

		await page.locator('[data-testid="dpp-f-title"]').fill("Digital health platform security assessment");
		await page.locator('[data-testid="dpp-f-description"]').fill("Assess the security of the platform and report.");
		await page.locator('[data-testid="dpp-f-result"]').fill("A prioritised remediation plan exists.");
		await page.locator('[data-testid="dpp-f-quantity"]').fill("1");
		await page.locator('[data-testid="dpp-f-required-by"]').fill("2099-04-30");
		await page.locator('[data-testid="dpp-f-budget-line"]').selectOption({ index: 0 });
		await page.locator('[data-testid="dpp-f-amount"]').fill("20000000");
		await page.locator('[data-testid="dpp-editor-save"]').click();
		await expectReady(page, "dpp");
		const row = page.locator('[data-testid="dpp-entries"] tbody tr', { hasText: "Digital health platform security assessment" });
		await expect(row).toContainText("Ready");

		// the plan's other (Need-origin) entry is still unfunded, so the whole
		// plan is not yet ready — this row's own action stays Edit, not View
		await row.getByRole("button", { name: "Edit" }).click();
		await expectReady(page, "dpp-entry");
		await expect(page.locator(".kt-page-title")).toHaveText("Edit direct requirement");
		await page.locator('[data-testid="dpp-f-title"]').fill("Digital health platform security assessment (revised)");
		await page.locator('[data-testid="dpp-editor-save"]').click();
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-entries"]')).toContainText("(revised)");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("HoD certifies and submits a fully funded plan", async ({ page }) => {
		const state = resetFixture<{ dpp_reference: string }>("reset_dpp_fixture", { with_direct: true, funded: true });
		const errors = collectConsoleErrors(page);
		await login(page, HOD, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Ready to submit");

		const cert = page.locator('[data-testid="dpp-certification"]');
		await expect(cert).toContainText("Departmental certification");
		await expect(cert).toContainText("I confirm this certification");
		await expect(page.locator('[data-testid="dpp-submit"]')).toBeDisabled();
		await page.locator('[data-testid="dpp-certify"]').check();
		await page.locator('[data-testid="dpp-submit"]').click();
		// the HoD holds no validation task themselves (that is the Planner's own
		// task, FU-14) — submitting reloads this same record in place
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Awaiting validation");
		await expect(page.locator('[data-testid="dpp-certification"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("auditor reads the plan with no edit, not-proceed or submit controls", async ({ page }) => {
		const state = resetFixture<{ dpp_reference: string; need_entry_id: string }>("reset_dpp_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-add-direct"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-submit"]')).toHaveCount(0);
		await expect(page.locator(`[data-testid="dpp-entry-action-${state.need_entry_id}"]`)).toHaveCount(0);

		await gotoDpp(page, state.dpp_reference, `/entry/${state.need_entry_id}`);
		await expectReady(page, "dpp-entry");
		await expect(page.locator('[data-testid="dpp-editor-not-proceed"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-editor-save"]')).toHaveCount(0);
		// read-only for an Auditor: the same testid renders a plain value, never
		// the editable <select>
		await expect(page.locator('select[data-testid="dpp-f-budget-line"]')).toHaveCount(0);
	});

	test("an author from another department is masked, never sees the record", async ({ page }) => {
		const state = resetFixture<{ dpp_reference: string }>("reset_dpp_fixture");
		await login(page, OUTSIDER, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="pln-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-error"] h3')).toHaveText("This record isn't available to you");
		await expect(page.locator(".kt-page-title")).toHaveCount(0);
	});

	test("planner accepts a fully classified submission", async ({ page }) => {
		const state = resetFixture<{ task: string; need_entry_id: string; direct_entry_id: string }>("reset_review_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-planning/dpp-review/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "dpp-review");
		await expect(page.locator('[data-testid="dppv-accept"]')).toBeDisabled();
		// index 0 is the disabled "Select…" placeholder
		await page.locator(`[data-testid="dppv-type-${state.need_entry_id}"]`).selectOption({ index: 1 });
		await page.locator(`[data-testid="dppv-type-${state.direct_entry_id}"]`).selectOption({ index: 1 });
		await expect(page.locator('[data-testid="dppv-accept"]')).toBeEnabled();
		await page.locator('[data-testid="dppv-accept"]').click();
		await expectReady(page, "workspace");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("planner returns a submission with a structured issue", async ({ page }) => {
		const state = resetFixture<{ task: string }>("reset_review_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-planning/dpp-review/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "dpp-review");
		await page.locator('[data-testid="dppv-return"]').click();
		await expect(page.locator('[data-testid="dppv-return-dialog"]')).toBeVisible();
		await page.locator('[data-testid="dppv-issue-problem-0"]').fill("The indicative amount needs correction.");
		await page.locator('[data-testid="dppv-issue-correction-0"]').fill("Confirm and update the amount.");
		await page.locator('[data-testid="dppv-return-confirm"]').click();
		await expectReady(page, "workspace");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
