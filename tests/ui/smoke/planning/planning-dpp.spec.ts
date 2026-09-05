import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUTHOR,
	HOD,
	OU_NAME,
	PASSWORD,
	PLANNER,
	collectConsoleErrors,
	expectReady,
	gotoDpp,
	gotoPlanning,
	resetFixture,
	restoreSite,
} from "./helpers";

/**
 * PLN-CHG-001 v1.12 Phase 3 (Slice A) — PLN-UI-02..05: the departmental
 * plan with a genuine accepted Need projected into it, the Need funding
 * editor (PLN-DES-03) with its not-proceeding outcome, the direct-requirement
 * editor (PLN-DES-04), certification and submission — on the live Budget
 * contract, no mocking anywhere in this path.
 */

type DppState = { dpp_reference: string; need_entry_id: string; direct_entry_id: string };

test.describe.configure({ mode: "serial" });

test.describe("PLN-UI-02..05 Departmental Procurement Plan", () => {
	test.afterAll(() => restoreSite());

	test("author completes the Need's funding, adds a direct requirement and the plan re-renders Ready to submit", async ({ page }) => {
		const state = resetFixture<DppState>("reset_dpp_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);

		// from the workspace row, not by typing the route
		await gotoPlanning(page);
		await expectReady(page, "workspace");
		await page.locator('[data-testid="pln-departmental-plans"] tbody tr .kt-btn-ghost').click();
		await expectReady(page, "dpp");

		// PLN-DES-02: header + three-column strip + amber notice; no PE
		await expect(page.locator(".kt-page-title")).toHaveText(`${OU_NAME} departmental plan`);
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Draft");
		const strip = page.locator('[data-testid="dpp-context"]');
		await expect(strip.locator("label")).toHaveText(["Department", "Financial Year", "Submission window"]);
		await expect(strip).toContainText("FY 2098/99");
		await expect(strip).toContainText("Open until 31 May 2099, 23:59 EAT");
		await expect(page.locator('[data-testid="dpp-readiness"] .pln-notice-title')).toHaveText(
			"1 requirement needs funding details"
		);
		await expect(page.locator('[data-testid="dpp-certification"]')).toHaveCount(0);
		const needRow = page.locator(`[data-testid="dpp-entry-${state.need_entry_id}"]`);
		await expect(needRow).toContainText("National digital health infrastructure upgrade");
		await expect(needRow).toContainText("Accepted Need · NDS-");
		await expect(needRow).toContainText("Not selected");
		await expect(needRow.locator(".kt-status")).toHaveText("Funding incomplete");

		// PLN-DES-03 — Complete funding details
		await page.locator(`[data-testid="dpp-entry-action-${state.need_entry_id}"]`).click();
		await expectReady(page, "dpp-entry");
		await expect(page.locator(".kt-page-title")).toHaveText("Complete funding details");
		const facts = page.locator('[data-testid="dpp-need-facts"]');
		await expect(facts.locator("label")).toHaveText([
			"Title", "Description", "Expected operational result", "Quantity", "Unit", "Required by", "Accepted Need",
		]);
		await expect(facts.locator("input, textarea, select")).toHaveCount(0);
		const lineSelect = page.locator('[data-testid="dpp-f-budget-line"]');
		await expect(lineSelect.locator("option")).toHaveCount(2);
		await expect(lineSelect.locator("option").first()).toContainText("Digital health infrastructure programme");
		await lineSelect.selectOption({ index: 0 });
		await page.locator('[data-testid="dpp-f-amount"]').fill("80000000");
		await page.locator('[data-testid="dpp-editor-save"]').click();
		await expectReady(page, "dpp");
		await expect(needRow.locator(".kt-status")).toHaveText("Ready");
		await expect(needRow).toContainText("KES 80,000,000");
		await expect(page.locator('[data-testid="dpp-readiness"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Ready to submit");

		// PLN-DES-04 — Add direct requirement
		await page.locator('[data-testid="dpp-add-direct"]').click();
		await expectReady(page, "dpp-entry");
		await expect(page.locator(".kt-page-title")).toHaveText("Add direct requirement");
		await expect(page.locator('[data-testid="dpp-editor-context"] label')).toHaveText(["Department", "Financial Year"]);
		await expect(page.locator('[data-testid="dpp-unit-new"]')).toHaveCount(0);
		await page.locator('[data-testid="dpp-f-title"]').fill("Digital health platform security assessment");
		await page
			.locator('[data-testid="dpp-f-description"]')
			.fill("Assess the security of the national digital health platform and provide a prioritised remediation report.");
		await page
			.locator('[data-testid="dpp-f-result"]')
			.fill("The Ministry receives a prioritised and actionable security remediation plan.");
		await page.locator('[data-testid="dpp-f-quantity"]').fill("1");
		await page.locator('[data-testid="dpp-f-unit"]').selectOption({ label: "Each" });
		await page.locator('[data-testid="dpp-f-required-by"]').fill("2099-04-30");
		await page.locator('[data-testid="dpp-f-budget-line"]').selectOption({ index: 0 });
		await page.locator('[data-testid="dpp-f-amount"]').fill("20000000");
		await page.locator('[data-testid="dpp-editor-save"]').click();
		await expectReady(page, "dpp");

		const rows = page.locator('[data-testid="dpp-entries"] tbody tr');
		await expect(rows).toHaveCount(2);
		await expect(rows.nth(1)).toContainText("Direct requirement");
		await expect(rows.nth(1).locator(".kt-status")).toHaveText("Ready");
		await expect(page.locator('[data-testid="dpp-totals"]')).toHaveText("2 requirements · KES 100,000,000");
		// author still cannot submit — HoD only (§5.1)
		await expect(page.locator('[data-testid="dpp-certification"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-submit-header"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("author records a Need as not proceeding with a reason instead of funding (PLN-AC-092)", async ({ page }) => {
		const state = resetFixture<DppState>("reset_dpp_fixture");
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, state.dpp_reference, `/entry/${state.need_entry_id}`);
		await expectReady(page, "dpp-entry");
		await page.locator('[data-testid="dpp-f-not-proceeding"]').check();
		await expect(page.locator('[data-testid="dpp-f-budget-line"]')).toBeDisabled();
		await page
			.locator('[data-testid="dpp-f-not-proceeding-reason"]')
			.fill("The department will defer this requirement to the following financial year.");
		await page.locator('[data-testid="dpp-editor-save"]').click();
		await expectReady(page, "dpp");
		const row = page.locator(`[data-testid="dpp-entry-${state.need_entry_id}"]`);
		await expect(row.locator(".kt-status")).toHaveText("Not proceeding");
		await expect(row).toContainText("—");
		await expect(page.locator('[data-testid="dpp-readiness"]')).toHaveCount(0);
	});

	test("hod certifies and submits; the submitted plan locks and shows Awaiting validation", async ({ page }) => {
		const state = resetFixture<DppState>("reset_dpp_fixture", { with_direct: true, funded: true });
		await login(page, HOD, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");

		// PLN-DES-05: Submit in the header, certification card, no readiness notice
		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Ready to submit");
		await expect(page.locator('[data-testid="dpp-readiness"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-add-direct"]')).toHaveCount(0);
		const cert = page.locator('[data-testid="dpp-certification"]');
		await expect(cert).toBeVisible();
		await expect(cert).toContainText(
			`I certify that this Departmental Procurement Plan contains the current procurement requirements of ${OU_NAME} for FY 2098/99`
		);
		await expect(cert).toContainText("Procurement Budget Lines and indicative amounts are ready for Procurement validation");
		const submit = page.locator('[data-testid="dpp-submit"]');
		await expect(submit).toBeDisabled(); // §12.5 — checkbox first
		await expect(page.locator('[data-testid="dpp-submit-header"]')).toBeDisabled();
		await page.locator('[data-testid="dpp-certify"]').check();
		await expect(submit).toBeEnabled();
		await submit.click();

		await expect(page.locator('[data-testid="dpp-badge"]')).toHaveText("Awaiting validation", { timeout: 30_000 });
		// locked: no add button, no row actions, no certification card
		await expect(page.locator('[data-testid="dpp-add-direct"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-submit-header"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-certification"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-entries"] .kt-btn-ghost')).toHaveCount(0);
	});

	test("planner opens the record read-only with no edit affordances", async ({ page }) => {
		const state = resetFixture<DppState>("reset_dpp_fixture", { with_direct: true });
		await login(page, PLANNER, PASSWORD);
		await gotoDpp(page, state.dpp_reference);
		await expectReady(page, "dpp");
		await expect(page.locator('[data-testid="dpp-add-direct"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-certification"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-submit"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="dpp-entries"] tbody tr')).toHaveCount(2);
		await expect(page.locator('[data-testid="dpp-entries"] .kt-btn-ghost')).toHaveCount(0);
	});

	test("a direct URL to a nonexistent plan fails closed on the load-error component", async ({ page }) => {
		await login(page, AUTHOR, PASSWORD);
		await gotoDpp(page, "DPP-NOPE-0000-000");
		await expectReady(page, "dpp");
		const card = page.locator('[data-testid="pln-error"]');
		await expect(card.locator("h3")).toHaveText("Procurement Planning could not be loaded");
		await expect(card.locator("button")).toHaveText("Try again");
		await expect(card).toContainText("Support reference: PLN-ERR-");
	});
});
