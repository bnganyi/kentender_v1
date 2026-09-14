import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUTHOR,
	NEW_PLAN_TITLE,
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
 * STR-CHG-001 v1.8 §16.2 (12) — the Strategy Author journey in a real
 * browser on the v1.8 compositions: Strategic plans → Update plan → one
 * pending change set (inline target edit, Add objective directly under a
 * Programme, Move up) → the unsaved-changes guard → Submit for approval
 * (save then submit) → Awaiting approval; plus the Create strategic plan
 * path (STR-AC-003, STR18-AC-003/004) with inline refusals and the §10
 * routes under reload and back/forward.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("STR-UI-01..03 — Strategy Author", () => {
	let fixture: DefaultFixture;

	test.beforeAll(() => {
		fixture = resetFixture("reset_default");
	});

	test.afterAll(() => {
		resetFixture("reset_default");
	});

	test("updates the current plan through one pending change set and submits it", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");

		// STR-DES-01 — name first, plain plan type, Current badge, View.
		await expect(page.locator("h1")).toHaveText("Strategic plans");
		await expect(page.locator('[data-testid="str-tab-my-work"]')).toContainText("Actions");
		const row = page.locator('[data-testid="str-plan-row"]');
		await expect(row).toHaveCount(1);
		await expect(row).toContainText(PLAN_TITLE);
		await expect(row).toContainText("Main strategic plan");
		await expect(row.locator('[data-testid="str-row-status"]')).toHaveText("Current");
		await expect(row.locator('[data-testid="str-row-action"]')).toHaveText("View");
		await expect(page.locator('[data-testid="str-new-plan"]')).toHaveText("Create strategic plan");

		// STR-DES-03 — the current plan's meaning leads.
		await row.locator('[data-testid="str-row-action"]').click();
		await expectScreen(page, "plan");
		await expect(page).toHaveURL(new RegExp(`/strategy/plan/${fixture.plan_reference}$`));
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Current");
		await expect(page.locator('[data-testid="str-objective-title"]')).toHaveText("Strengthen interoperable national digital health services");
		await expect(page.locator('[data-testid="str-objective-definition"]')).toContainText("expressed as a percentage.");
		await expect(page.locator('[data-testid="str-target-kpi"]')).toContainText("80%");
		await expect(page.locator('[data-testid="str-history-row"]').first()).toContainText("Approved and activated Version 1");
		await expect(page.locator('[data-testid="str-update-plan"]')).toHaveText("Update plan");

		// Update plan — a Draft update from the exact Current version.
		await page.locator('[data-testid="str-update-plan"]').click();
		await page.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page).toHaveURL(/\/version\/2\/structure$/, { timeout: 30_000 });
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-title-heading"]')).toHaveText("Edit plan");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Draft update");
		await expect(page.locator('[data-testid="str-editor-notice"]')).toContainText("The current plan remains in use");
		await expect(page.locator('[data-testid="str-save-changes"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-save-draft"]')).toHaveCount(0);

		// STR-DES-05 — inline target editor: 80% → 85%, pending until Save changes.
		await page.locator('[data-testid="str-tree-node"][data-node-type="Performance Target"]').first().click();
		await expect(page.locator('[data-testid="str-selected-type"]')).toHaveText("Indicator");
		await expect(page.locator('[data-testid="str-target-editor"]')).toBeVisible();
		await page.locator('[data-testid="str-target-value"]').fill("85");
		await page.locator('[data-testid="str-target-confirm"]').click();
		await expect(page.locator('[data-testid="str-target-result"]')).toHaveText("At least 85%");
		await expect(page.locator('[data-testid="str-structure-editor"]')).toHaveAttribute("data-dirty", "true");
		await page.locator('[data-testid="str-save-changes"]').click();
		await expect(page.locator('[data-testid="str-structure-editor"]')).toHaveAttribute("data-dirty", "false", { timeout: 30_000 });
		await expect(page.locator('[data-testid="str-target-result"]')).toHaveText("At least 85%");

		// STR-DES-04 — Add objective directly under the Programme, then Move up.
		await page.locator('[data-node-type="Programme"] [data-child-type="Strategic Objective"]').first().click();
		await expect(page.locator('[data-testid="str-selected-type"]')).toHaveText("Objective");
		await page.locator('[data-testid="str-node-title"]').fill("Expand telemedicine coverage in underserved counties");
		await expect(page.locator('[data-testid="str-move-down"]')).toBeDisabled();
		await page.locator('[data-testid="str-move-up"]').click();
		await expect(page.locator('[data-testid="str-move-up"]')).toBeDisabled();
		await expect(page.locator('[data-testid="str-tree-pending"]')).toHaveCount(1);

		// An indicator with a target on the new objective, through the inline editor.
		await page.locator('[data-testid="str-tree-node"][data-node-type="Strategic Objective"]').filter({ hasText: "telemedicine" }).locator('[data-testid="str-add-child"]').click();
		await page.locator('[data-testid="str-indicator-name"]').fill("Percentage of underserved counties with telemedicine services");
		await page.locator('[data-testid="str-indicator-definition"]').fill("Counties with an operational telemedicine site divided by all underserved counties.");
		await page.locator('[data-testid="str-indicator-unit"]').fill("Percentage");
		await page.locator('[data-testid="str-add-target"]').click();
		const editor = page.locator('[data-testid="str-target-editor"]');
		await expect(editor).toContainText("Add performance target");
		await expect(editor.locator('[data-testid="str-target-unit"]')).toHaveText("%");
		await editor.locator('[data-testid="str-target-period"]').selectOption("2027-2028");
		await editor.locator('[data-testid="str-target-value"]').fill("60");
		await editor.locator('[data-testid="str-target-confirm"]').click();
		await expect(page.locator('[data-testid="str-target-row"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="str-target-result"]')).toHaveText("At least 60%");

		// §12.3 — leaving with unsaved work offers Save / Discard / Stay.
		await page.locator('[data-testid="str-tab-overview"]').click();
		const guard = page.locator('[data-testid="str-unsaved-dialog"]');
		await expect(guard).toBeVisible();
		await expect(guard).toContainText("Discard unsaved changes");
		await guard.locator('[data-testid="str-confirm-cancel"]').click();
		await expect(guard).toBeHidden();
		await expect(page).toHaveURL(/\/version\/2\/structure$/);

		// §8.2 — Submit saves the pending set first, then submits the confirmed Draft.
		await page.locator('[data-testid="str-submit"]').click();
		await expect(page).toHaveURL(/\/version\/2$/, { timeout: 30_000 });
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Awaiting approval");
		await expect(page.locator('[data-testid="str-awaiting-review"]')).toContainText("Awaiting Strategy Approver review");
		await expect(page.locator('[data-testid="str-objective-title"]')).toHaveCount(2);
		await expectNoFrappeModal(page);

		// Saved on the server: reload keeps the exact version route and content.
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-eyebrow"]')).toContainText("VERSION 2");
		await expect(page.locator('[data-testid="str-objective-title"]')).toHaveCount(2);

		// History is version-scoped with readable labels; back/forward restore the tab.
		await page.locator('[data-testid="str-tab-history"]').click();
		await expect(page).toHaveURL(/\/version\/2\/history$/);
		const first = page.locator('[data-testid="str-history-row"]').first();
		await expect(first).toContainText("Submitted for approval");
		await expect(first).toContainText("Esther Muthoni");
		await expect(page.locator('[data-testid="str-history-row"]').last()).toContainText("Draft update created from Version 1");
		await page.goBack();
		await expect(page.locator('[data-testid="str-plan"]')).toHaveAttribute("data-tab", "overview");
		await page.goForward();
		await expect(page.locator('[data-testid="str-plan"]')).toHaveAttribute("data-tab", "history");

		// The Current version still leads on the plan route, with the update noted separately.
		await gotoStrategy(page, `/plan/${fixture.plan_reference}`);
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Current");
		await expect(page.locator('[data-testid="str-pending-update"]')).toContainText("Update awaiting Strategy Approver review");
		await expect(page.locator('[data-testid="str-update-plan"]')).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("creates a plan, lands in its structure and is told inline what is missing", async ({ page }) => {
		resetFixture("reset_default");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		await page.locator('[data-testid="str-new-plan"]').click();
		await expect(page).toHaveURL(/\/strategy\/new$/);
		await expect(page.locator("h1")).toHaveText("Create strategic plan");
		await expect(page.locator('[data-testid="str-new-plan-form"]')).toBeVisible();
		// STR-DES-02 — no generated-reference input before creation.
		await expect(page.locator('[data-testid="str-new-plan-form"]')).not.toContainText("Not assigned");

		await page.locator('[data-testid="str-save-draft"]').click();
		await expect(page.locator('[data-testid="str-field-error-title"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-field-error-period-start"]')).toBeVisible();
		await expectNoFrappeModal(page);

		await page.locator('[data-testid="str-plan-title"]').fill(NEW_PLAN_TITLE);
		await page.locator('[data-testid="str-period-start"]').fill("2028-07-01");
		await page.locator('[data-testid="str-period-end"]').fill("2033-06-30");
		await page.locator('[data-testid="str-save-draft"]').click();

		// STR18-AC-003 — creation opens the structure of the exact new Draft.
		await expect(page).toHaveURL(/\/strategy\/plan\/MOH-SP-\d{4}\/version\/1\/structure$/, { timeout: 30_000 });
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Draft");
		await expect(page.locator('[data-testid="str-no-structure"]')).toHaveText("Add a pillar to start the plan structure.");

		// STR-BR-012 — readiness blocks submission with the actual missing item, inline.
		await page.locator('[data-testid="str-submit"]').click();
		await expect(page.locator('[data-testid="str-action-error"]')).toContainText("Add a pillar");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Draft");
		await expectNoFrappeModal(page);

		await page.locator('[data-testid="str-add-pillar"]').click();
		await page.locator('[data-testid="str-node-title"]').fill("Universal health coverage");
		await page.locator('[data-testid="str-node-save"]').click();
		await expect(page.locator('[data-testid="str-structure-editor"]')).toHaveAttribute("data-dirty", "false", { timeout: 30_000 });
		await expect(page.locator('[data-testid="str-tree-node"][data-node-type="Pillar"]')).toHaveCount(1);

		// §11.3A — the first Draft's Overview carries the identity fields and Save plan details.
		await page.locator('[data-testid="str-tab-overview"]').click();
		await expect(page.locator('[data-testid="str-draft-details"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-identity-title"]')).toHaveValue(NEW_PLAN_TITLE);
		await expect(page.locator('[data-testid="str-readiness-failures"]')).toContainText("Add at least one objective");

		// Both plans in the register; the status filter is server-side (§12.1).
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(2);
		await page.locator('[data-testid="str-status-filter"]').selectOption("Draft");
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="str-row-action"]')).toHaveText("Continue draft");
		await expect(page.locator('[data-testid="str-count-label"]')).toHaveText("Showing 1 of 1 plan");
		await page.locator('[data-testid="str-search"]').fill("nothing matches this");
		await expect(page.locator('[data-testid="str-no-match"]')).toBeVisible();
		await page.locator('[data-testid="str-clear-filters"]').click();
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(2);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
