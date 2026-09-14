import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	APPROVER,
	AUTHOR,
	PASSWORD,
	RETURN_REASON,
	collectConsoleErrors,
	dateLabel,
	expectNoFrappeModal,
	expectScreen,
	gotoStrategy,
	resetFixture,
	type SuccessorFixture,
} from "./helpers";

/**
 * STR-CHG-001 v1.8 §16.2 (12) — the Strategy Approver journey on the §14.4
 * profiles: STR18-FX-IMMEDIATE (decision overview leads with what changed,
 * every tab, Return once with the §11.9 reason, the corrected resubmission
 * approved in one click, Version 1 becomes Previous version) and
 * STR18-FX-FUTURE (approval refused while the start date is in the future,
 * Return still available). Plus the submitting author's own denial.
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("STR-UI-04 — Strategy Approver", () => {
	let fixture: SuccessorFixture;

	test.beforeAll(() => {
		fixture = resetFixture<SuccessorFixture>("reset_submitted_fixture");
	});

	test.afterAll(() => {
		resetFixture("reset_default");
	});

	test("reviews the decision overview first, returns once and approves the corrected submission", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, APPROVER, PASSWORD);

		// Actions lists the task with the §11.1 columns; Review opens without deciding.
		await gotoStrategy(page, "/my-work");
		await expectScreen(page, "portfolio");
		await expect(page.locator('[data-testid="str-tab-my-work"]')).toHaveAttribute("aria-selected", "true");
		await expect(page.locator('[data-testid="str-new-plan"]')).toHaveCount(0);
		const item = page.locator('[data-testid="str-my-work-row"]');
		await expect(item).toHaveCount(1);
		await expect(item).toContainText("Plan changes");
		await expect(item).toContainText("Esther Muthoni");
		await expect(item).toContainText("Awaiting review");
		await expect(item.locator('[data-testid="str-my-work-action"]')).toHaveText("Review");
		await item.locator('[data-testid="str-my-work-action"]').click();

		// STR-DES-06 — what changed leads; the proposed plan follows; decision on every tab.
		await expectScreen(page, "approval");
		await expect(page).toHaveURL(new RegExp(`/strategy/approval/${fixture.v2_reference}$`));
		await expect(page.locator('[data-testid="str-approval-title"]')).toHaveText("Review plan changes");
		await expect(page.locator('[data-testid="str-approval-status"]')).toHaveText("Awaiting approval");
		await expect(page.locator('[data-testid="str-submitted-by"]')).toContainText("Submitted by Esther Muthoni");
		const changes = page.locator('[data-testid="str-what-changed"] [data-testid="str-changes-row"]');
		await expect(changes.filter({ hasText: "Target for FY 2027/28" })).toContainText("At least 80%");
		await expect(changes.filter({ hasText: "Target for FY 2027/28" })).toContainText("At least 85%");
		await expect(changes.filter({ hasText: "Version effective from" })).toContainText("1 Jul 2023");
		await expect(changes.filter({ hasText: "Version effective from" })).toContainText(dateLabel(fixture.effective_from!));
		await expect(page.locator('[data-testid="str-proposed-applies"]')).toContainText(dateLabel(fixture.effective_from!));
		await expect(page.locator('[data-testid="str-target-was"]')).toHaveText("was At least 80%");
		await expect(page.locator('[data-testid="str-readiness-failures"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-decision-footer"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-decision-consequence"]')).toContainText("Existing approved records keep their saved strategy details.");
		await expect(page.locator('[data-testid="str-approve"]')).toHaveText("Approve changes and use plan");
		await expect(page.locator('[data-testid="str-return"]')).toHaveText("Return for correction");

		// STR-DES-07 — the submitted structure, read-only, with facts on selection.
		await page.locator('[data-testid="str-atab-structure"]').click();
		await expect(page).toHaveURL(/\/structure$/);
		await expect(page.locator('[data-testid="str-tree-node"]')).toHaveCount(6);
		await expect(page.locator('[data-testid="str-add-child"]')).toHaveCount(0);
		await page.locator('[data-testid="str-tree-node"][data-node-type="Performance Indicator"]').click();
		await expect(page.locator('[data-testid="str-approval-node-facts"]')).toContainText("How it is measured");
		await expect(page.locator('[data-testid="str-decision-footer"]')).toBeVisible();

		// STR-DES-08 — complete comparison against the fixed baseline.
		await page.locator('[data-testid="str-atab-changes"]').click();
		await expect(page).toHaveURL(/\/changes$/);
		await expect(page.locator('[data-testid="str-approval-changes"] .kt-card-title')).toHaveText("Changes from Version 1");
		await expect(page.locator('[data-testid="str-approval-changes"] [data-testid="str-changes-row"]')).toHaveCount(2);

		// STR-DES-09 — submission and history for this version only, newest first.
		await page.locator('[data-testid="str-atab-history"]').click();
		await expect(page).toHaveURL(/\/history$/);
		const history = page.locator('[data-testid="str-history-row"]');
		await expect(history).toHaveCount(3);
		await expect(history.nth(0)).toContainText("Submitted for approval");
		await expect(history.nth(1)).toContainText("Draft saved");
		await expect(history.nth(2)).toContainText("Draft update created from Version 1");

		// Direct reload and back/forward keep the version and tab.
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-approval"]')).toHaveAttribute("data-tab", "history");
		await expect(page.locator('[data-testid="str-decision-footer"]')).toBeVisible();
		await page.goBack();
		await expect(page.locator('[data-testid="str-approval"]')).toHaveAttribute("data-tab", "changes");
		await page.goForward();
		await expect(page.locator('[data-testid="str-approval"]')).toHaveAttribute("data-tab", "history");

		// STR-DES-06-Return — one required field, 10–500 characters.
		await page.locator('[data-testid="str-return"]').click();
		const dialog = page.locator('[data-testid="str-return-dialog"]');
		await expect(dialog).toContainText("What needs to change?");
		await expect(dialog).toContainText("Correction required");
		await dialog.locator('[data-testid="str-confirm-reason"]').fill("short");
		await expect(dialog.locator('[data-testid="str-confirm-ok"]')).toBeDisabled();
		await dialog.locator('[data-testid="str-confirm-reason"]').fill(RETURN_REASON);
		await dialog.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page.locator('[data-testid="str-approval-status"]')).toHaveText("Changes requested", { timeout: 30_000 });
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-decision-footer"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-approval-settled"]')).toBeVisible();

		// The author sees Changes requested with the exact reason and resubmits.
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		await expect(page.locator('[data-testid="str-row-status"]')).toHaveText("Changes requested");
		await expect(page.locator('[data-testid="str-row-action"]')).toHaveText("Correct and resubmit");
		await page.locator('[data-testid="str-row-action"]').click();
		await expectScreen(page, "plan");
		await expect(page).toHaveURL(/\/version\/2\/structure$/);
		await expect(page.locator('[data-testid="str-return-reason"]')).toContainText(RETURN_REASON);
		// §5.1 — nothing is deleted after first submission.
		await page.locator('[data-testid="str-tree-node"][data-node-type="Performance Indicator"]').click();
		await expect(page.locator('[data-testid="str-target-delete"]')).toHaveCount(0);
		await page.locator('[data-testid="str-submit"]').click();
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Awaiting approval", { timeout: 30_000 });

		// One deliberate click approves the corrected submission.
		await login(page, APPROVER, PASSWORD);
		await gotoStrategy(page, `/approval/${fixture.v2_reference}/history`);
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-history-row"]').filter({ hasText: "Returned for correction" })).toContainText("Dr Alfred Ochieng");
		await expect(page.locator('[data-testid="str-history-reason"]')).toContainText(RETURN_REASON);
		await page.locator('[data-testid="str-approve"]').click();
		await expect(page.locator('[data-testid="str-approval-status"]')).toHaveText("Current", { timeout: 30_000 });
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-decision-footer"]')).toHaveCount(0);
		await expectNoFrappeModal(page);

		// STR-AC-014 / STR18-AC-016 — Version 2 Current, Version 1 Previous version, closed the day before.
		await page.locator('[data-testid="str-open-plan"]').click();
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-eyebrow"]')).toContainText("VERSION 2");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Current");
		await expect(page.locator('[data-testid="str-target-kpi"]')).toContainText("85%");
		const versions = page.locator('[data-testid="str-version-row"]');
		await expect(versions).toHaveCount(2);
		await expect(versions.nth(1)).toContainText("Previous version");
		await gotoStrategy(page, `/plan/${fixture.plan_reference}/version/1`);
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Previous version");
		await expect(page.locator('[data-testid="str-target-kpi"]')).toContainText("80%");
		await expect(page.locator('[data-testid="str-view-current"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-update-plan"]')).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("cannot approve a version that starts in the future, but may return it", async ({ page }) => {
		const future = resetFixture<SuccessorFixture>("reset_future_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, APPROVER, PASSWORD);
		await gotoStrategy(page, `/approval/${future.v2_reference}`);
		await expectScreen(page, "approval");
		const banner = page.locator('[data-testid="str-future-effective"]');
		await expect(banner).toContainText("This version cannot be approved yet. It starts on 1 Jul 2027.");
		await expect(banner).toContainText("It will not activate automatically.");
		await expect(page.locator('[data-testid="str-approve"]')).toBeDisabled();
		await expect(page.locator('[data-testid="str-return"]')).toBeEnabled();
		await page.locator('[data-testid="str-atab-changes"]').click();
		await expect(banner).toBeVisible();
		await expect(page.locator('[data-testid="str-approval-changes"] [data-testid="str-changes-row"]').filter({ hasText: "Version effective from" })).toContainText("1 Jul 2027");
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the submitting author is denied the approval task inline", async ({ page }) => {
		const state = resetFixture<SuccessorFixture>("reset_submitted_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/approval/${state.v2_reference}`);
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-forbidden"]')).toContainText("You do not have access to this Strategy approval page.");
		await expect(page.locator('[data-testid="str-forbidden"]')).toContainText("Strategy Approver");
		await expect(page.locator('[data-testid="str-decision-footer"]')).toHaveCount(0);
		await expectNoFrappeModal(page);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
