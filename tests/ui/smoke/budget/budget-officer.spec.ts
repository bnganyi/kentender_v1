import { test, expect } from "@playwright/test";
import {
	OFFICER,
	EmptyYearFixture,
	SuccessorFixture,
	TwoEmptyYearsFixture,
	attachDocument,
	collectConsoleErrors,
	confirmDecision,
	expectScreen,
	gotoBudget,
	login,
	resetFixture,
	selectYear,
} from "./helpers";

/**
 * BUD-CHG-001 v1.9 — the Budget Officer's journeys: Record approved
 * allocation (§11.2, §9.3; BUD19-AC-003/004), the lines editor and one Submit
 * for review (§11.3, §12.2; BUD19-AC-005/006/007/008), correcting a returned
 * update and the successor rules (§11.14–§11.15; BUD19-AC-009/010).
 */
test.describe.configure({ mode: "serial" });

test("record approved allocation, add lines and submit for review", async ({ page }) => {
	const fx = resetFixture<EmptyYearFixture>("reset_no_budget_year");
	const errors = collectConsoleErrors(page);
	await login(page, OFFICER);
	await gotoBudget(page);
	await selectYear(page, fx.empty_fiscal_year);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	await page.getByTestId("budget-register-btn").click();
	await expectScreen(page, "register");
	await expect(page.getByRole("heading", { level: 1 })).toHaveText("Record approved allocation");
	await expect(page.locator("text=Not assigned")).toHaveCount(0);
	await expect(page.getByTestId("bud-reg-currency")).toHaveValue("KES");

	// Missing fields stay unsaved with their actual errors — no Budget row, no dialog.
	await page.getByTestId("bud-reg-save-btn").click();
	await expect(page.locator(".kt-field-error").first()).toBeVisible();
	await expect(page.locator(".modal.show")).toHaveCount(0);

	await page.getByTestId("bud-reg-approval-ref").fill("MOH-FIN-BUD-PW-01 (Demo)");
	await page.getByTestId("bud-reg-approval-date").fill("2026-06-30");
	await page.getByTestId("bud-reg-approved-allocation").fill("160000000");
	await attachDocument(page, "bud-reg-upload-btn");
	await expect(page.getByTestId("bud-reg-document-name")).not.toHaveText("No file attached");
	await page.getByTestId("bud-reg-save-btn").click();
	await expectScreen(page, "editor");
	await expect(page).toHaveURL(/\/version\/1\/edit\/lines$/);
	await expect(page.getByTestId("bud-editor-status")).toHaveText("Draft");

	// Two lines; the running total reports the exact amount still to assign.
	await page.getByTestId("bud-editor-add-line-btn").click();
	const rows = page.locator('[data-testid="bud-editor-lines-table"] tbody tr');
	await rows.nth(0).getByLabel("Budget line").fill("Digital health infrastructure programme");
	await rows.nth(0).getByLabel("Amount").fill("100000000");
	await expect(page.getByTestId("bud-editor-reconcile")).toContainText("Amount still to assign: KES 60,000,000");
	await page.getByTestId("bud-editor-add-line-btn").click();
	await rows.nth(1).getByLabel("Budget line").fill("Digital health workforce development");
	await rows.nth(1).getByLabel("Amount").fill("60000000");
	await expect(page.getByTestId("bud-editor-reconcile")).toContainText("Budget lines match the approved allocation.");

	// UAT #22 — Submit asks first; Cancel saves and submits nothing.
	const submissions: string[] = [];
	page.on("request", (r) => { if (/submit_budget_version|save_budget_version_draft/.test(r.url())) submissions.push(r.url()); });
	await page.getByTestId("bud-editor-submit-btn").click();
	await confirmDecision(page, "Submit for review?", false);
	expect(submissions).toHaveLength(0);
	await expect(page.getByTestId("bud-editor-status")).toHaveText("Draft");

	// One Submit saves the pending lines and submits the exact version.
	await page.getByTestId("bud-editor-submit-btn").click();
	await confirmDecision(page, "Submit for review?");
	await expect(page.getByTestId("bud-editor-status")).toHaveText("Submitted for approval", { timeout: 30_000 });
	await expect(page.getByTestId("bud-editor-readonly")).toBeVisible();
	await expect(page.locator(".modal.show")).toHaveCount(0);
	expect(errors).toEqual([]);
});

test("a returned update opens with the reason and resubmits the same draft", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_successor_returned");
	await login(page, OFFICER);
	await gotoBudget(page, `/${fx.budget_code}/version/${fx.v2_number}/edit`);
	await expectScreen(page, "editor");
	await expect(page.getByTestId("bud-editor-status")).toHaveText("Changes requested");
	await expect(page.getByTestId("bud-editor-returned")).toContainText(fx.return_reason!);
	await expect(page.getByRole("heading", { level: 1 })).toHaveText("Update registered allocation");
	await page.getByTestId("bud-editor-approval-ref").fill("MOH-FIN-BUD-2027-02 (Demo, corrected)");
	await page.getByTestId("bud-editor-submit-btn").click();
	await confirmDecision(page, "Submit for review?");
	await expect(page.getByTestId("bud-editor-status")).toHaveText("Submitted for approval", { timeout: 30_000 });
});

test("the Officer can see a version's own history from the editor, not only from Detail", async ({ page }) => {
	/**
	 * 2026-09-19 (owner report) — the Approver's review task has always had a
	 * History tab; the Officer working the same version in the editor had no
	 * equivalent, and for a version that has never been Active there is no
	 * Detail route to fall back to at all (get_budget_detail resolves an
	 * Active Version).
	 */
	const fx = resetFixture<SuccessorFixture>("reset_successor_returned");
	await login(page, OFFICER);
	await gotoBudget(page, `/${fx.budget_code}/version/${fx.v2_number}/edit`);
	await expectScreen(page, "editor");
	await page.getByTestId("bud-editor-tab-history").click();
	await expect(page).toHaveURL(new RegExp(`/version/${fx.v2_number}/edit/history$`));
	const table = page.getByTestId("bud-editor-history-table");
	await expect(table).toContainText("Budget version created");
	await expect(table).toContainText("Returned for correction");
});

test("successor lines: omission only where nothing is reserved; transfer totals; unsaved guard", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_omission");
	await login(page, OFFICER);
	await gotoBudget(page, `/${fx.budget_code}/version/${fx.v2_number}/edit/lines`);
	await expectScreen(page, "editor");
	const rows = page.locator('[data-testid="bud-editor-lines-table"] tbody tr');
	const dhi = rows.filter({ hasText: "Digital health infrastructure programme" });
	const hwd = rows.filter({ hasText: "Digital health workforce development" });
	await expect(dhi.getByTestId("bud-editor-omit-link")).toHaveCount(0);
	await expect(hwd.getByTestId("bud-editor-omit-link")).toHaveText("Omit from this update");
	await expect(dhi.locator("button:has-text('Remove')")).toHaveCount(0);
	await hwd.getByTestId("bud-editor-omit-link").click();
	await expect(page.getByTestId("bud-editor-omitted")).toContainText("Digital health workforce development");

	// Leaving the tab with unsaved line changes asks first.
	await page.getByTestId("bud-editor-tab-overview").click();
	await expect(page.getByTestId("bud-editor-unsaved-dialog")).toBeVisible();
	await page.getByRole("button", { name: "Stay here" }).click();
	await expect(page).toHaveURL(/\/edit\/lines$/);

	await page.getByTestId("bud-editor-save-btn").click();
	await expect(page.getByTestId("bud-editor-omitted")).toBeVisible();
	await page.reload({ waitUntil: "domcontentloaded" });
	await expectScreen(page, "editor");
	await expect(page.getByTestId("bud-editor-omitted")).toContainText("Digital health workforce development");
});

test("stale save and a rejected submit are typed results, never a dialog", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_successor_draft");
	await login(page, OFFICER);
	await gotoBudget(page, `/${fx.budget_code}/version/${fx.v2_number}/edit`);
	await expectScreen(page, "editor");

	await page.route("**/api/method/kentender_budget.api.budget_api.save_budget_version_draft", (route) =>
		route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: { ok: false, code: "BUDGET_STALE_WRITE", errors: { expected_modified: "This budget has changed since you opened it. Refresh to see the current details." } } }) })
	);
	await page.getByTestId("bud-editor-approval-ref").fill("changed");
	await page.getByTestId("bud-editor-save-btn").click();
	await expect(page.getByTestId("bud-editor-stale")).toContainText("This budget has changed since you opened it.");
	await expect(page.locator(".modal.show")).toHaveCount(0);
	await page.unroute("**/api/method/kentender_budget.api.budget_api.save_budget_version_draft");

	await page.route("**/api/method/kentender_budget.api.budget_api.submit_budget_version", (route) =>
		route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: { ok: false, code: "BUDGET_NOT_READY", blockers: [{ code: "lines.total_mismatch", rule: "BUDGET_TOTAL_MISMATCH", message: "Amount still to assign: KES 10,000,000", detail: {} }] } }) })
	);
	await page.getByTestId("bud-editor-submit-btn").click();
	await confirmDecision(page, "Submit for review?");
	await expect(page.getByTestId("bud-editor-saved-not-submitted")).toContainText("Your changes were saved, but the allocation was not submitted.");
	await expect(page.getByTestId("bud-editor-blockers")).toContainText("Amount still to assign: KES 10,000,000");
	await expect(page.getByTestId("bud-editor-status")).toHaveText("Draft");
});

test("recording an allocation for a second year starts from a blank form", async ({ page }) => {
	/**
	 * GitHub #26 — after the first year's allocation was recorded, going back
	 * and choosing another year's Record approved allocation opened with the
	 * first one's reference, date, amount and document already filled in. The
	 * page stays open between screens, so the form must be cleared each time
	 * the screen is entered, and again when the year changes.
	 */
	const fx = resetFixture<TwoEmptyYearsFixture>("reset_two_empty_years");
	const errors = collectConsoleErrors(page);
	await login(page, OFFICER);
	await gotoBudget(page);
	await selectYear(page, fx.empty_fiscal_year);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	await page.getByTestId("budget-register-btn").click();
	await expectScreen(page, "register");
	await page.getByTestId("bud-reg-approval-ref").fill("MOH-FIN-BUD-FIRST-01 (Demo)");
	await page.getByTestId("bud-reg-approval-date").fill("2026-06-30");
	await page.getByTestId("bud-reg-approved-allocation").fill("160000000");
	await attachDocument(page, "bud-reg-upload-btn");
	await page.getByTestId("bud-reg-save-btn").click();
	await expectScreen(page, "editor");

	// Back to the workspace inside the open page (no reload), pick the other
	// year, and record again.
	await page.evaluate(() => (window as any).frappe.set_route("budget-funding"));
	await expectScreen(page, "workspace");
	await page.getByTestId("budget-fy-filter").selectOption(fx.second_empty_fiscal_year);
	await page.getByTestId("budget-register-btn").click();
	await expectScreen(page, "register");
	await expect(page.getByTestId("bud-reg-approval-ref")).toHaveValue("");
	await expect(page.getByTestId("bud-reg-approval-date")).toHaveValue("");
	await expect(page.getByTestId("bud-reg-approved-allocation")).toHaveValue("");
	await expect(page.getByTestId("bud-reg-document-name")).toHaveText("No file attached");

	// The second year's own details are what the editor then shows.
	await page.getByTestId("bud-reg-approval-ref").fill("MOH-FIN-BUD-SECOND-02 (Demo)");
	await page.getByTestId("bud-reg-approval-date").fill("2025-06-30");
	await page.getByTestId("bud-reg-approved-allocation").fill("90000000");
	await attachDocument(page, "bud-reg-upload-btn");
	await page.getByTestId("bud-reg-save-btn").click();
	await expectScreen(page, "editor");
	await page.getByTestId("bud-editor-tab-overview").click();
	await expect(page.getByTestId("bud-editor-approval-ref")).toHaveValue("MOH-FIN-BUD-SECOND-02 (Demo)");
	await expect(page.getByTestId("bud-editor-approved-allocation")).toHaveValue(/90[, ]?000[, ]?000/);
	expect(errors).toEqual([]);
});
