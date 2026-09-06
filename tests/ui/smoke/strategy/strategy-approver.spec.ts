import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	APPROVER,
	AUTHOR,
	PASSWORD,
	collectConsoleErrors,
	expectNoFrappeModal,
	expectScreen,
	gotoStrategy,
	resetFixture,
	type SuccessorFixture,
} from "./helpers";

/**
 * STR-CHG-001 v1.7 §16.2 (12) — the Strategy Approver journey on the §14.4
 * fixture (Version 2, Submitted for approval by Esther, target 80% → 85%):
 * Overview, Structure, Changes and History for the exact submitted version;
 * Return once with a reason; the corrected resubmission approved, which
 * activates Version 2 and supersedes Version 1 in one transaction.
 */

test.describe.configure({ mode: "serial", timeout: 300_000 });

test.describe("STR-UI-04 — Strategy Approver", () => {
	let fixture: SuccessorFixture;

	test.beforeAll(() => {
		fixture = resetFixture<SuccessorFixture>("reset_submitted_fixture");
	});

	// Leave the site exactly as the §14 seed defines it: the canonical plan at
	// Version 1 Active, no "Playwright —" plans (feedback: always remove test data).
	test.afterAll(() => {
		resetFixture("reset_default");
	});

	test("inspects every tab, returns once and approves the corrected submission", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, APPROVER, PASSWORD);

		// My work lists only what this actor may decide on (§12.1).
		await gotoStrategy(page, "/my-work");
		await expectScreen(page, "portfolio");
		await expect(page.locator('[data-testid="str-tab-my-work"]')).toHaveAttribute("aria-selected", "true");
		await expect(page.locator('[data-testid="str-new-plan"]')).toHaveCount(0);
		const item = page.locator('[data-testid="str-my-work-row"]');
		await expect(item).toHaveCount(1);
		await expect(item).toContainText("Version 2");
		await expect(item).toContainText("Submitted for approval");
		await item.locator('[data-testid="str-my-work-action"]').click();

		// STR-DES-06 Overview.
		await expectScreen(page, "approval");
		await expect(page).toHaveURL(new RegExp(`/strategy/approval/${fixture.v2_reference}$`));
		await expect(page.locator('[data-testid="str-approval-eyebrow"]')).toContainText("VERSION 2");
		await expect(page.locator('[data-testid="str-approval-status"]')).toHaveText("Submitted for approval");
		await expect(page.locator('[data-testid="str-submitted-by"]')).toHaveText("Esther Muthoni");
		await expect(page.locator('[data-testid="str-readiness-row"] .kt-status')).toHaveText(["Ready", "Ready", "Ready", "Ready"]);
		await expect(page.locator('[data-testid="str-decision-footer"]')).toBeVisible();

		// STR-DES-07 Structure — the submitted version, read-only.
		await page.locator('[data-testid="str-atab-structure"]').click();
		await expect(page).toHaveURL(/\/structure$/);
		await expect(page.locator('[data-testid="str-tree-node"]')).toHaveCount(6);
		await expect(page.locator('[data-testid="str-add-child"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-tree-node"][data-node-type="Performance Target"]')).toContainText("At least 85");

		// STR-DES-08 Changes — computed server-side against Version 1.
		await page.locator('[data-testid="str-atab-changes"]').click();
		await expect(page).toHaveURL(/\/changes$/);
		await expect(page.locator('[data-testid="str-approval-changes"] .kt-card-title')).toHaveText("Changes from Active Version 1");
		const change = page.locator('[data-testid="str-changes-row"]');
		await expect(change).toHaveCount(1);
		await expect(change).toContainText("At least 80");
		await expect(change).toContainText("At least 85");

		// STR-DES-09 History — this version only, newest first, named actors.
		await page.locator('[data-testid="str-atab-history"]').click();
		await expect(page).toHaveURL(/\/history$/);
		const history = page.locator('[data-testid="str-history-row"]');
		await expect(history.first()).toContainText("Submit for approval");
		await expect(history.first()).toContainText("Esther Muthoni");
		await expect(history.last()).toContainText("Successor Version Created");

		// Direct reload on a tab and back/forward keep the version and tab.
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-approval"]')).toHaveAttribute("data-tab", "history");
		await expect(history.first()).toBeVisible();
		await expect(page.locator('[data-testid="str-decision-footer"]')).toBeVisible();
		await page.goBack();
		await expect(page.locator('[data-testid="str-approval"]')).toHaveAttribute("data-tab", "changes");
		await page.goForward();
		await expect(page.locator('[data-testid="str-approval"]')).toHaveAttribute("data-tab", "history");

		// Return — the dialog holds only the reason; 10–500 characters, enforced.
		await page.locator('[data-testid="str-return"]').click();
		const reason = page.locator('[data-testid="str-confirm-reason"]');
		await reason.fill("short");
		await expect(page.locator('[data-testid="str-confirm-ok"]')).toBeDisabled();
		await reason.fill("Please add a baseline target for FY 2026/27 on the digital health indicator.");
		await page.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page.locator('[data-testid="str-approval-status"]')).toHaveText("Draft", { timeout: 30_000 });
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-decision-footer"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-approval-settled"]')).toBeVisible();

		// The author sees the returned Draft with the reason and resubmits.
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/plan/${fixture.plan_reference}`);
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Draft");
		await expect(page.locator('[data-testid="str-return-reason"]')).toContainText("baseline target for FY 2026/27");
		await page.locator('[data-testid="str-tab-structure"]').click();
		await page.locator('[data-testid="str-submit"]').click();
		await page.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Submitted for approval", { timeout: 30_000 });

		// The approver approves the corrected submission.
		await login(page, APPROVER, PASSWORD);
		await gotoStrategy(page, `/approval/${fixture.v2_reference}/history`);
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-history-row"]').filter({ hasText: "Return" })).toContainText("Dr Alfred Ochieng");
		await expect(page.locator('[data-testid="str-history-row"]').filter({ hasText: "Return" })).toContainText("baseline target");
		await page.locator('[data-testid="str-approve"]').click();
		await page.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page.locator('[data-testid="str-approval-status"]')).toHaveText("Active", { timeout: 30_000 });
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-decision-footer"]')).toHaveCount(0);
		await expectNoFrappeModal(page);

		// STR-AC-014 — Version 2 Active, Version 1 Superseded, in one transaction.
		await page.locator('[data-testid="str-open-plan"]').click();
		await expectScreen(page, "plan");
		await expect(page).toHaveURL(new RegExp(`/strategy/plan/${fixture.plan_reference}$`));
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Active");
		await expect(page.locator('[data-testid="str-active-version"]')).toHaveText("Version 2");
		await expect(page.locator('[data-testid="str-approved-by"]')).toHaveText("Dr Alfred Ochieng");
		const versions = page.locator('[data-testid="str-version-row"]');
		await expect(versions).toHaveCount(2);
		await expect(versions.nth(0)).toContainText("Active");
		await expect(versions.nth(1)).toContainText("Superseded");
		// Creating the next successor is an Author action; the Approver is offered none (§7).
		await expect(page.locator('[data-testid="str-create-successor"]')).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the submitting author is denied the approval task inline", async ({ page }) => {
		const state = resetFixture<SuccessorFixture>("reset_submitted_fixture");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/approval/${state.v2_reference}`);
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-forbidden"]')).toContainText("Strategy Approver");
		await expect(page.locator('[data-testid="str-decision-footer"]')).toHaveCount(0);
		await expectNoFrappeModal(page);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
