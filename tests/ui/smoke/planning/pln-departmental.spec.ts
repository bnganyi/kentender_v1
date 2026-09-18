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
	tickCheckbox,
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

// Sequential, but not serial: these run on one worker because the fixtures
// are one shared world, and each test rebuilds its own. Aborting the rest of
// the file because one test failed hides every other result behind it.
test.describe.configure({ timeout: 180_000 });

test.describe("PLN18-303 Departmental Plan screens", () => {
	test.afterAll(() => restoreSite());

	test("author completes Need funding, then marks it not proceeding and restores it", async ({ page }) => {
		const state = resetFixture<{ dpp_reference: string; need_entry_id: string }>("reset_dpp_fixture");
		const errors = collectConsoleErrors(page);
		const REASON = "The department will pursue this requirement in a later annual planning cycle.";
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");

		// §10.4 U03-FUNDING — funding opens beneath the requirement's own row;
		// the rest of the plan stays visible throughout.
		const row = page.locator('[data-testid="pln-dpp-row"]').first();
		await expect(row).toContainText("Funding details needed");
		await row.locator('[data-testid="pln-dpp-row-action"]').click();
		await expect(page.locator('[data-testid="dpp-funding-panel"]')).toBeVisible();
		await expect(page.locator('[data-testid="pln-dpp-table"]')).toBeVisible();

		await page.locator('[data-testid="dpp-funding-line"]').selectOption({ index: 1 });
		await page.locator('[data-testid="dpp-funding-amount"]').fill("80000000");
		await page.locator('[data-testid="dpp-funding-save"]').click();
		// The row refreshes in place; the panel closes because it was opened
		// against an entry whose state has now moved.
		await expect(page.locator('[data-testid="dpp-funding-panel"]')).toHaveCount(0, { timeout: 30_000 });
		await expect(page.locator('[data-testid="pln-dpp-row"]').first()).toContainText("Included");

		// U03-EXCLUDE — a governed reason, in its own dialog, never bundled
		// into the save.
		await page.locator('[data-testid="pln-dpp-row"]').first().locator('[data-testid="pln-dpp-row-action"]').click();
		await page.locator('[data-testid="dpp-funding-exclude"]').click();
		await expect(page.locator('[data-testid="pln-not-proceed-dialog"]')).toBeVisible();
		await page.locator('[data-testid="pln-not-proceed-reason"]').fill(REASON);
		await page.locator('[data-testid="pln-not-proceed-confirm"]').click();

		// U03-EXCLUDED-ROW — the reason is always visible beneath the row, and
		// the only action offered is the way back in.
		const excluded = page.locator('[data-testid="pln-dpp-exclusion-reason"]');
		await expect(excluded).toContainText(REASON, { timeout: 30_000 });
		await expect(page.locator('[data-testid="pln-dpp-row"]').first()).toContainText("Not included this year");
		await expect(page.locator('[data-testid="pln-dpp-row-action"]').first())
			.toHaveText("Include in this year's departmental plan");

		await page.locator('[data-testid="pln-dpp-row-action"]').first().click();
		await expect(page.locator('[data-testid="pln-dpp-exclusion-reason"]')).toHaveCount(0, { timeout: 30_000 });
		// Restoring brings it back without its funding: §10.4 U03-REINCLUDE
		// prefills no old operative amount.
		await expect(page.locator('[data-testid="pln-dpp-row"]').first()).toContainText("Funding details needed");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("author adds a direct requirement and later edits it", async ({ page }) => {
		const state = resetFixture<{ dpp_reference: string }>("reset_dpp_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference, "/add-direct");
		await expectReady(page, "dpp-entry");
		// §10.4 U04-DIRECT — the page is named for what the department is
		// doing, not for the internal origin of the record.
		await expect(page.locator('[data-testid="dpp-editor-title"]')).toHaveText("Add a requirement");

		await page.locator('[data-testid="dpp-f-title"]').fill("Digital health platform security assessment");
		await page.locator('[data-testid="dpp-f-description"]').fill("Assess the security of the platform and report.");
		await page.locator('[data-testid="dpp-f-result"]').fill("A prioritised remediation plan exists.");
		await page.locator('[data-testid="dpp-f-quantity"]').fill("1");
		await page.locator('[data-testid="dpp-f-unit"]').selectOption({ index: 1 });
		await page.locator('[data-testid="dpp-f-required-by"]').fill("2099-04-30");
		await page.locator('[data-testid="dpp-f-budget-line"]').selectOption({ index: 1 });
		await page.locator('[data-testid="dpp-f-amount"]').fill("20000000");
		await page.locator('[data-testid="dpp-editor-save"]').click();
		await expectReady(page, "dpp");
		const row = page.locator('[data-testid="pln-dpp-table"] tbody tr', { hasText: "Digital health platform security assessment" });
		// §10.3 — a requirement with a budget line and an amount is Included;
		// its action names what the department does next, which is read it back.
		await expect(row).toContainText("Included");

		// the plan's other (Need-origin) entry is still unfunded, so the whole
		// plan is not yet ready — this row stays openable, not read-only
		await row.getByRole("link", { name: "Review details" }).click();
		await expectReady(page, "dpp-entry");
		await expect(page.locator(".kt-page-title")).toHaveText("Edit direct requirement");
		await page.locator('[data-testid="dpp-f-title"]').fill("Digital health platform security assessment (revised)");
		await page.locator('[data-testid="dpp-editor-save"]').click();
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="pln-dpp-table"]')).toContainText("(revised)");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("HoD certifies and submits a fully funded plan", async ({ page }) => {
		const state = resetFixture<{ dpp_reference: string }>("reset_dpp_fixture", { with_direct: true, funded: true });
		const errors = collectConsoleErrors(page);
		await login(page, HOD, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		// The context row carries the department and year alongside the status.
		await expect(page.locator('[data-testid="pln-dpp-context"]')).toContainText("Ready to submit");

		const cert = page.locator('[data-testid="pln-dpp-certification"]');
		await expect(cert).toContainText("Certification");
		await expect(cert).toContainText("I confirm this certification");
		await expect(page.locator('[data-testid="pln-dpp-submit"]')).toBeDisabled();
		await tickCheckbox(page.locator('[data-testid="pln-dpp-certify"]'));
		await page.locator('[data-testid="pln-dpp-submit"]').click();
		// the HoD holds no validation task themselves (that is the Planner's own
		// task, FU-14) — submitting reloads this same record in place
		await expect(page.locator('[data-testid="pln-dpp-context"]')).toHaveText("Awaiting validation");
		await expect(page.locator('[data-testid="pln-dpp-certification"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("auditor reads the plan with no edit, not-proceed or submit controls", async ({ page }) => {
		const state = resetFixture<{ dpp_reference: string; need_entry_id: string }>("reset_dpp_fixture");
		await login(page, AUDITOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="pln-dpp-add"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="pln-dpp-submit"]')).toHaveCount(0);
		await expect(page.locator(`[data-testid="dpp-entry-action-${state.need_entry_id}"]`)).toHaveCount(0);

		await gotoDpp(page, state.dpp_reference, `/entry/${state.need_entry_id}`);
		await expectReady(page, "dpp-entry");
		await expect(page.locator('[data-testid="dpp-funding-exclude"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-editor-save"]')).toHaveCount(0);
		// Read-only for an Auditor: the field keeps its shape and its value —
		// a requirement's facts are what they came to read — but nothing on it
		// can be changed (§10.4 U04).
		await expect(page.locator('[data-testid="dpp-f-budget-line"]')).toBeDisabled();
		await expect(page.locator('[data-testid="dpp-f-title"]')).toBeDisabled();
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
		// §10.5 — the acceptance is absent until the evidence supports it,
		// never a disabled control with no explanation.
		await expect(page.locator('[data-testid="pln-review-accept"]')).toHaveCount(0);
		// index 0 is the "Select…" placeholder; each requirement is classified
		// on its own.
		await page.locator(`[data-testid="pln-review-type"][data-entry="${state.need_entry_id}"]`).selectOption({ index: 1 });
		await page.locator(`[data-testid="pln-review-type"][data-entry="${state.direct_entry_id}"]`).selectOption({ index: 1 });
		await expect(page.locator('[data-testid="pln-review-accept"]')).toBeEnabled();
		await page.locator('[data-testid="pln-review-accept"]').click();
		await expectReady(page, "workspace");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("planner returns a submission with a structured issue", async ({ page }) => {
		const state = resetFixture<{ task: string }>("reset_review_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, PLANNER, PASSWORD);
		await page.goto(`/app/procurement-planning/dpp-review/${state.task}`, { waitUntil: "domcontentloaded" });
		await expectReady(page, "dpp-review");
		await page.locator('[data-testid="pln-review-return"]').click();
		await expect(page.locator('[data-testid="dppv-return-dialog"]')).toBeVisible();
		await page.locator('[data-testid="dppv-issue-problem-0"]').fill("The indicative amount needs correction.");
		await page.locator('[data-testid="dppv-issue-correction-0"]').fill("Confirm and update the amount.");
		await page.locator('[data-testid="dppv-return-confirm"]').click();
		await expectReady(page, "workspace");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
