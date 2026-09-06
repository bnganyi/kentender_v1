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
} from "./helpers";

/**
 * STR-CHG-001 v1.7 §16.2 (12), STR-AC-004/021/026/035–037 and KT-STD-001
 * §3A — a read-only user opens an Active plan and sees no workflow action;
 * an actor with no Strategy assignment sees the Forbidden state on every
 * route with no data disclosure and no permission modal; Administrator has
 * technical read and no business action.
 */

test.describe.configure({ mode: "serial", timeout: 180_000 });

test.describe("Strategy access states", () => {
	let fixture: DefaultFixture;

	test.beforeAll(() => {
		fixture = resetFixture("reset_default");
	});

	test("auditor opens the Active plan read-only and cannot open an approval task", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUDITOR, PASSWORD);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="str-new-plan"]')).toHaveCount(0);
		await page.locator('[data-testid="str-row-action"]').click();
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-title-heading"]')).toContainText(PLAN_TITLE);
		await expect(page.locator('[data-testid="str-create-successor"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-submit"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-identity-edit"]')).toHaveCount(0);
		await page.locator('[data-testid="str-tab-structure"]').click();
		await expect(page.locator('[data-testid="str-tree-node"]')).toHaveCount(6);
		await expect(page.locator('[data-testid="str-add-child"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-add-pillar"]')).toHaveCount(0);

		// STR-AC-021 — read access is not approval-task access.
		await gotoStrategy(page, `/approval/${fixture.version_reference}`);
		await expectScreen(page, "approval");
		await expect(page.locator('[data-testid="str-forbidden"]')).toContainText("Strategy Approver");
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
		await expect(forbidden).toContainText("Strategy Author, Strategy Approver or Auditor");
		await expect(forbidden).toContainText("Ask your KenTender administrator to assign one in System setup.");
		// §3A.1 / STR-AC-026 — no header, filter, content or count is painted alongside the refusal.
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

	test("administrator reads everything and is offered no business action", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await loginAsAdministrator(page);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="str-new-plan"]')).toHaveCount(0);
		await page.locator('[data-testid="str-row-action"]').click();
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-create-successor"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-submit"]')).toHaveCount(0);
		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
