import { execSync } from "node:child_process";
import path from "node:path";

import { test, expect } from "@playwright/test";
import {
	loginAsBudgetApprover,
	loginAsBudgetOfficerApprover,
	loginAsBudgetViewer,
} from "../../helpers/auth";

/**
 * BUD-CHG-001 v1.2 — BUD-UI-04 Approval task (/app/budget-funding/review/
 * {budget_version_id}), the single decide-and-activate screen that replaced
 * the old separate Reviewer/Activation task pair.
 *
 * Three dedicated, always-reset Playwright fixtures (see kentender_budget.
 * seeds.playwright_ui_fixtures) each hold their own Submitted-for-approval
 * initial-baseline version: BUD-PW-TASK-APPROVE (consumed by the Approve
 * test), BUD-PW-TASK-RETURN (consumed by the Return test), and
 * BUD-PW-TASK-SELFBLOCK (submitted by the dual Officer+Approver persona,
 * left untouched — used for both the self-approval-segregation check and
 * the Viewer direct-URL-denial check).
 */

const BENCH_ROOT = path.resolve(__dirname, "../../../../../..");
const SITE = process.env.UI_SITE || "kentender.midas.com";

function resetFixture(fn: string): void {
	execSync(`cd "${BENCH_ROOT}" && bench --site ${SITE} execute kentender_budget.seeds.playwright_ui_fixtures.${fn}`, {
		stdio: "pipe",
		timeout: 120_000,
	});
}

test.describe.configure({ mode: "serial" });

test.describe("Approval task (BUD-UI-04)", () => {
	test.beforeAll(() => {
		resetFixture("reset_approval_task_approve_fixture");
		resetFixture("reset_approval_task_return_fixture");
		resetFixture("reset_approval_task_selfblock_fixture");
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 1000 });
	});

	test("initial-baseline task screen renders all 4 tabs with a 3-check readiness set", async ({ page }) => {
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-PW-TASK-APPROVE-V1", { waitUntil: "domcontentloaded" });

		await expect(page.getByTestId("bud-task-header")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("bud-task-header")).toContainText("Submitted for approval");
		await expect(page.getByTestId("bud-task-readiness").locator('span:text("Ready")')).toHaveCount(3);

		await page.getByTestId("bud-task-tab-lines").click();
		await expect(page.getByTestId("bud-task-lines-table")).toContainText("Playwright approval-task test line");

		await page.getByTestId("bud-task-tab-changes").click();
		await expect(page.getByTestId("bud-task-changes-baseline")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("bud-task-changes-baseline")).toContainText("Initial baseline");

		await page.getByTestId("bud-task-tab-history").click();
		await expect(page.getByTestId("bud-task-history-table")).toContainText("Budget version created");
	});

	test("Approver approves a version, activating it", async ({ page }) => {
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-PW-TASK-APPROVE-V1", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("bud-task-approve-btn")).toBeVisible({ timeout: 30_000 });

		await page.getByTestId("bud-task-approve-btn").click();
		await expect(page.getByRole("heading", { name: "Approve this version?" })).toBeVisible({ timeout: 10_000 });
		await page.getByRole("dialog").getByRole("button", { name: "Approve" }).click();

		await expect(page.getByText("Approved and activated")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("bud-task-header")).toContainText("Active");
		await expect(page.getByTestId("bud-task-approve-btn")).toHaveCount(0);
		await expect(page.getByTestId("bud-task-return-btn")).toHaveCount(0);
	});

	test("Approver returns a version with a reason", async ({ page }) => {
		await loginAsBudgetApprover(page);
		await page.goto("/app/budget-funding/review/BUD-PW-TASK-RETURN-V1", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("bud-task-return-btn")).toBeVisible({ timeout: 30_000 });

		await page.getByTestId("bud-task-return-btn").click();
		const dialog = page.getByRole("dialog");
		await expect(dialog.getByRole("heading", { name: "Return this version?" })).toBeVisible({ timeout: 10_000 });
		const returnConfirm = dialog.getByRole("button", { name: "Return" });
		await expect(returnConfirm).toBeDisabled();
		await dialog.getByPlaceholder("Reason (10-500 characters)").fill(
			"Playwright test: authorised total needs revision before approval.",
		);
		await expect(returnConfirm).toBeEnabled();
		await returnConfirm.click();

		await expect(page.getByText("Returned")).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("bud-task-header")).toContainText("Draft");
		await expect(page.getByTestId("bud-task-approve-btn")).toHaveCount(0);
		await expect(page.getByTestId("bud-task-return-btn")).toHaveCount(0);
	});

	test("BUD-AC-008 self-approval segregation blocks Approve for the submitting dual-role persona", async ({
		page,
	}) => {
		await loginAsBudgetOfficerApprover(page);
		await page.goto("/app/budget-funding/review/BUD-PW-TASK-SELFBLOCK-V1", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("bud-task-header")).toBeVisible({ timeout: 30_000 });

		// This persona both submitted the version and holds Budget Approver —
		// Return is not restricted by self-submission, only Approve is.
		await expect(page.getByTestId("bud-task-return-btn")).toBeVisible();
		await expect(page.getByTestId("bud-task-approve-btn")).toHaveCount(0);
	});

	test("Budget Viewer is denied a Submitted version by direct id (§7 direct-URL gating)", async ({ page }) => {
		await loginAsBudgetViewer(page);
		await page.goto("/app/budget-funding/review/BUD-PW-TASK-SELFBLOCK-V1", { waitUntil: "domcontentloaded" });
		await expect(page.getByTestId("bud-task-forbidden")).toBeVisible({ timeout: 30_000 });
	});
});
