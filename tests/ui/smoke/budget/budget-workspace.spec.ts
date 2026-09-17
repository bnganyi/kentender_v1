import { test, expect } from "@playwright/test";
import {
	ADMIN,
	APPROVER,
	AUDITOR,
	CANONICAL_FY,
	OFFICER,
	PendingFixture,
	SuccessorFixture,
	ConversionFixture,
	EmptyYearFixture,
	collectConsoleErrors,
	expectNoFrappeModal,
	expectScreen,
	gotoBudget,
	login,
	resetFixture,
	selectYear,
} from "./helpers";

/**
 * BUD-CHG-001 v1.9 — BUD-UI-01 workspace state matrix (§11.1, §11.1A,
 * §11.1B, §12.1; BUD19-AC-001/002/025/026) and the read-only journeys on
 * BUD-UI-03/05 (§11.4–§11.7A, §11.19; BUD19-AC-015/016/017).
 */
test.describe.configure({ mode: "serial" });

test("no record: the Officer may record an allocation, a reader may not", async ({ page }) => {
	const fx = resetFixture<EmptyYearFixture>("reset_no_budget_year");
	await login(page, OFFICER);
	await gotoBudget(page);
	await selectYear(page, fx.empty_fiscal_year);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	await expect(page.getByTestId("budget-no-baseline")).toContainText(`No procurement allocation has been recorded for FY ${fx.empty_fiscal_year}.`);
	await expect(page.getByTestId("budget-register-btn")).toHaveText("Record approved allocation");
	await expect(page.getByTestId("budget-position-cards")).toHaveCount(0);

	await login(page, AUDITOR);
	await gotoBudget(page);
	await selectYear(page, fx.empty_fiscal_year);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	await expect(page.getByTestId("budget-no-baseline")).toBeVisible();
	await expect(page.getByTestId("budget-register-btn")).toHaveCount(0);
});

test("initial draft and submission: next step per actor, never a current position", async ({ page }) => {
	const draft = resetFixture<PendingFixture>("reset_initial_draft");
	await login(page, OFFICER);
	await gotoBudget(page);
	await selectYear(page, draft.pending.fiscal_year);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	const card = page.getByTestId("budget-pending-card");
	await expect(card).toHaveAttribute("data-state", "initial_draft");
	await expect(card).toContainText("Allocation draft");
	await expect(page.getByTestId("budget-pending-action-btn")).toHaveText("Continue draft");
	await expect(page.getByTestId("budget-position-cards")).toHaveCount(0);
	await expect(page.getByTestId("budget-register-btn")).toHaveCount(0);
	await page.getByTestId("budget-pending-action-btn").click();
	await expectScreen(page, "editor");
	await expect(page).toHaveURL(new RegExp(`/budget-funding/${draft.pending.budget_code}/version/1/edit$`));

	const submitted = resetFixture<PendingFixture>("reset_initial_submitted");
	await login(page, APPROVER);
	await gotoBudget(page);
	await selectYear(page, submitted.pending.fiscal_year);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	await expect(page.getByTestId("budget-pending-card")).toContainText("Awaiting Budget Approver review");
	await expect(page.getByTestId("budget-pending-action-btn")).toHaveText("Review");
	await page.getByTestId("budget-pending-action-btn").click();
	await expectScreen(page, "review");
	await expect(page.getByRole("heading", { level: 1 })).toHaveText("Review registered allocation");

	await login(page, ADMIN);
	await gotoBudget(page);
	await selectYear(page, submitted.pending.fiscal_year);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	await expect(page.getByTestId("budget-pending-action-btn")).toHaveText("View version (read-only)");
	await page.getByTestId("budget-pending-action-btn").click();
	await expectScreen(page, "editor");
	await expect(page.getByTestId("bud-editor-readonly")).toBeVisible();
	await expect(page.getByTestId("bud-editor-save-btn")).toHaveCount(0);
	await expectNoFrappeModal(page);
});

test("returned draft: Changes requested with the full reason", async ({ page }) => {
	const fx = resetFixture<PendingFixture>("reset_returned_draft");
	await login(page, OFFICER);
	await gotoBudget(page);
	await selectYear(page, fx.pending.fiscal_year);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	await expect(page.getByTestId("budget-pending-card")).toHaveAttribute("data-state", "returned_draft");
	await expect(page.getByTestId("budget-pending-return")).toContainText(fx.return_reason!);
	await expect(page.getByTestId("budget-pending-action-btn")).toHaveText("Correct and resubmit");
});

test("current allocation with an update awaiting review stays in use; reader journey through detail and line", async ({ page }) => {
	const fx = resetFixture<SuccessorFixture>("reset_successor_submitted");
	const errors = collectConsoleErrors(page);
	await login(page, AUDITOR);
	await gotoBudget(page);
	await selectYear(page, CANONICAL_FY);
	await gotoBudget(page);
	await expectScreen(page, "workspace");
	await expect(page.getByTestId("budget-pending-card")).toContainText("Allocation update awaiting Budget Approver review");
	await expect(page.getByTestId("budget-summary-card")).toContainText("Version 1");
	const cards = page.getByTestId("budget-position-cards");
	await expect(cards).toContainText("Registered allocation");
	await expect(cards).toContainText("Reserved for requisitions");
	await expect(cards).toContainText("Committed to contracts");
	await expect(cards).toContainText("Available to reserve");
	await expect(cards).toContainText("KES 80,000,000");
	await expect(page.getByTestId("budget-lines-preview")).toContainText("All departments");
	await expect(page.getByTestId("budget-lines-preview")).not.toContainText("Entity-wide");
	await expect(page.getByTestId("budget-update-btn")).toHaveCount(0);

	await page.getByTestId("budget-view-btn").click();
	await expectScreen(page, "detail");
	await expect(page.getByTestId("budget-detail-status")).toHaveText("Current");
	await expect(page.getByTestId("budget-detail-update-btn")).toHaveCount(0);
	await page.getByTestId("budget-detail-tab-lines").click();
	await expect(page).toHaveURL(/\/lines$/);
	await expect(page.getByTestId("budget-detail-lines-table")).toContainText("Registered allocation");
	await page.getByTestId("budget-detail-tab-activity").click();
	await expect(page.getByTestId("budget-detail-activity-table")).toContainText("Requisition funding reserved");
	await page.getByTestId("budget-detail-tab-history").click();
	await expect(page.getByTestId("budget-detail-history-table")).toContainText("Approved and activated");
	await page.goBack();
	await expect(page).toHaveURL(/\/activity$/);
	await page.goForward();
	await expect(page).toHaveURL(/\/history$/);
	await page.reload({ waitUntil: "domcontentloaded" });
	await expectScreen(page, "detail");
	await expect(page.getByTestId("budget-detail-history-table")).toBeVisible();

	await gotoBudget(page, `/line/${fx.dhi_code}`);
	await expectScreen(page, "line");
	await expect(page.getByTestId("bud-line-position-cards")).toContainText("KES 20,000,000");
	const row = page.getByTestId("bud-line-reservation").first();
	await expect(row).toContainText("REQ-MOH-2027-021-001");
	await expect(row).toContainText("Still reserved · originally KES 80,000,000");
	expect(errors).toEqual([]);
});

test("partial conversion and a reservation requiring review read without double counting", async ({ page }) => {
	const fx = resetFixture<ConversionFixture>("reset_requires_review");
	await login(page, AUDITOR);
	await gotoBudget(page, `/line/${fx.conversion.dhi_code}`);
	await expectScreen(page, "line");
	const cards = page.getByTestId("bud-line-position-cards");
	await expect(cards).toContainText("KES 100,000,000");
	await expect(cards).toContainText("KES 60,000,000");
	await expect(page.getByTestId("bud-line-explanation")).toContainText("KES 60,000,000 of the reservation is now committed to a contract. The remaining reservation is KES 20,000,000. No payment is recorded here.");
	const row = page.getByTestId("bud-line-reservation").first();
	await expect(row).toContainText("Requires review — funds remain reserved");
	await expect(row).toContainText("Originally reserved");
	await expect(row).toContainText("Converted into commitments");
	await expect(page.getByTestId("bud-line-requires-review")).toContainText("owning Requisition");
	await expect(page.getByRole("button", { name: /release|convert|adjust/i })).toHaveCount(0);
});
