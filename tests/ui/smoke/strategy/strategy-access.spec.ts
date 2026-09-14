import { expect, test } from "@playwright/test";

import { login, loginAsAdministrator } from "../../helpers/auth";
import {
	AUDITOR,
	NOBODY,
	PASSWORD,
	PLAN_TITLE,
	collectConsoleErrors,
	expectNoFrappeModal,
	expectScreen,
	gotoStrategy,
	resetFixture,
	type DefaultFixture,
	type SuccessorFixture,
} from "./helpers";

/**
 * STR-CHG-001 v1.8 §16.2 (12), §11.10, STR-AC-004/021/026/035–037,
 * STR18-AC-019/020 and KT-STD-001 v1.5 §3A — a read-only user opens the
 * Current plan and sees no workflow action; an actor with no Strategy
 * assignment sees the exact Forbidden copy on every route with no data
 * disclosure and no modal; a technical reader (§3A.6) reads every status
 * and the exact task read-only with an empty Actions queue.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Strategy access states", () => {
	let fixture: DefaultFixture;

	test.beforeAll(() => {
		fixture = resetFixture("reset_default");
	});

	test.afterAll(() => {
		resetFixture("reset_default");
	});

	test("auditor reads the Current plan and cannot open an approval task", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUDITOR, PASSWORD);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="str-new-plan"]')).toHaveCount(0);
		await page.locator('[data-testid="str-row-action"]').click();
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-title-heading"]')).toContainText(PLAN_TITLE);
		await expect(page.locator('[data-testid="str-objective-definition"]')).toContainText("expressed as a percentage.");
		await expect(page.locator('[data-testid="str-update-plan"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-submit"]')).toHaveCount(0);
		await page.locator('[data-testid="str-tab-structure"]').click();
		await expect(page.locator('[data-testid="str-tree-node"]')).toHaveCount(6);
		await expect(page.locator('[data-testid="str-add-child"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-add-pillar"]')).toHaveCount(0);

		// STR-AC-021 — read access is not approval-task access.
		await gotoStrategy(page, `/approval/${fixture.version_reference}`);
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-forbidden"]')).toContainText("Decision access requires Strategy Approver responsibility.");
		await expectNoFrappeModal(page);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("an actor with no Strategy assignment lands on the inline Forbidden state everywhere", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, NOBODY, PASSWORD);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		const forbidden = page.locator('[data-testid="str-forbidden"]');
		await expect(forbidden).toContainText("You do not have access to Strategy Alignment.");
		await expect(forbidden).toContainText("This area needs Strategy Author, Strategy Approver or Auditor responsibility, or Administrator/System Manager technical access.");
		await expect(forbidden).toContainText("Ask your KenTender administrator to check your access in System setup.");
		// §3A.1 — no header, filter, content or count is painted alongside the refusal.
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-tab-plans"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-search"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-new-plan"]')).toHaveCount(0);
		await expectNoFrappeModal(page);
		// §3A.3 — the module stays in navigation and its own route was pushed.
		await expect(page).toHaveURL(/\/strategy$/);
		await expect(page.locator("a", { hasText: "Strategy Alignment" }).first()).toBeVisible();

		await gotoStrategy(page, `/plan/${fixture.plan_reference}`);
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-forbidden"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-plan-title-heading"]')).toHaveCount(0);
		await expectNoFrappeModal(page);

		await gotoStrategy(page, `/approval/${fixture.version_reference}`);
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-forbidden"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-decision-footer"]')).toHaveCount(0);
		await expectNoFrappeModal(page);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("administrator reads every status and the exact task read-only, with an empty Actions queue", async ({ page }) => {
		const submitted = resetFixture<SuccessorFixture>("reset_submitted_fixture");
		const errors = collectConsoleErrors(page);
		await loginAsAdministrator(page);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="str-new-plan"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-row-action"]')).toHaveText("View");
		await page.locator('[data-testid="str-tab-my-work"]').click();
		await expect(page.locator('[data-testid="str-my-work-empty"]')).toContainText("Nothing needs your action right now.");

		// The submitted Draft update is readable, with no mutation control.
		await gotoStrategy(page, `/plan/${submitted.plan_reference}/version/2/structure`);
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Awaiting approval");
		await expect(page.locator('[data-testid="str-tree-node"]')).toHaveCount(6);
		await expect(page.locator('[data-testid="str-add-child"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-submit"]')).toHaveCount(0);

		// KT-STD-001 §3A.6 — the exact task resolves read-only; no decision.
		await gotoStrategy(page, `/approval/${submitted.v2_reference}`);
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-forbidden"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-approval-title"]')).toHaveText("Review plan changes");
		await expect(page.locator('[data-testid="str-what-changed"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-decision-footer"]')).toHaveCount(0);
		await expectNoFrappeModal(page);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
