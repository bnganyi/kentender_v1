import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUTHOR,
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
 * STR-CHG-001 v1.7 §16.2 (12) — the Strategy Author journey in a real
 * browser: Portfolio → successor Draft → structure editing → submission,
 * plus the brand-new-plan path (STR-AC-003) with its inline refusals
 * (KT-STD-001 §3A, AGENTS.md §6.10) and the §10 route table under direct
 * load, reload and back/forward.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

test.describe("STR-UI-01..03 — Strategy Author", () => {
	let fixture: DefaultFixture;

	test.beforeAll(() => {
		fixture = resetFixture("reset_default");
	});

	// Leave the site exactly as the §14 seed defines it: the canonical plan at
	// Version 1 Active, no "Playwright —" plans (feedback: always remove test data).
	test.afterAll(() => {
		resetFixture("reset_default");
	});

	test("opens the Portfolio, creates a successor Draft, edits the structure and submits it", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");

		// STR-DES-01 — the seeded plan, Active at Version 1, offered as View.
		const row = page.locator('[data-testid="str-plan-row"]');
		await expect(row).toHaveCount(1);
		await expect(row).toContainText(PLAN_TITLE);
		await expect(row).toContainText(fixture.plan_reference);
		await expect(row.locator(".kt-status")).toHaveText("Active");
		await expect(row.locator('[data-testid="str-row-action"]')).toHaveText("View");
		await expect(page.locator('[data-testid="str-new-plan"]')).toBeVisible();

		await row.locator('[data-testid="str-row-action"]').click();
		await expectScreen(page, "plan");
		await expect(page).toHaveURL(new RegExp(`/strategy/plan/${fixture.plan_reference}$`));
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Active");
		await expect(page.locator('[data-testid="str-approved-by"]')).toHaveText("Dr Alfred Ochieng");
		await expect(page.locator('[data-testid="str-count-objectives"]')).toHaveText("1");

		// An Active version's structure is read-only (§12.2).
		await page.locator('[data-testid="str-tab-structure"]').click();
		await expect(page).toHaveURL(/\/version\/1\/structure$/);
		await expect(page.locator('[data-testid="str-tree-node"]')).toHaveCount(6);
		await expect(page.locator('[data-testid="str-add-child"]')).toHaveCount(0);

		// Create successor version — server-side copy of the Active version.
		await page.locator('[data-testid="str-tab-overview"]').click();
		await page.locator('[data-testid="str-create-successor"]').click();
		await page.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page).toHaveURL(/\/version\/2\/structure$/, { timeout: 30_000 });
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Draft");
		await expect(page.locator('[data-testid="str-plan-eyebrow"]')).toContainText("VERSION 2");
		await expect(page.locator('[data-testid="str-add-pillar"]')).toBeVisible();

		// STR-DES-05 — the §14.4 change: FY 2027/28 target 80% → 85%.
		await page.locator('[data-testid="str-tree-node"][data-node-type="Performance Indicator"]').first().click();
		await expect(page.locator('[data-testid="str-target-result"]')).toHaveText("At least 80%");
		await page.locator('[data-testid="str-target-edit"]').click();
		await page.locator('[data-testid="str-target-edit-value"]').fill("85");
		await page.locator('[data-testid="str-target-edit-save"]').click();
		await expect(page.locator('[data-testid="str-target-result"]')).toHaveText("At least 85%");

		// A second Objective under the Sub-programme, with its own indicator and target.
		await page.locator('[data-testid="str-tree-node"][data-node-type="Sub-programme"] [data-testid="str-add-child"]').click();
		await page.locator('[data-testid="str-node-title"]').fill("Expand telemedicine coverage in underserved counties");
		await page.locator('[data-testid="str-node-save"]').click();
		const objectives = page.locator('[data-testid="str-tree-node"][data-node-type="Strategic Objective"]');
		await expect(objectives).toHaveCount(2);
		await objectives.filter({ hasText: "telemedicine" }).locator('[data-testid="str-add-child"]').click();
		await page.locator('[data-testid="str-indicator-name"]').fill("Percentage of underserved counties with telemedicine services");
		await page.locator('[data-testid="str-indicator-definition"]').fill("Counties with an operational telemedicine site divided by all underserved counties.");
		await page.locator('[data-testid="str-indicator-unit"]').fill("Percentage");
		await page.locator('[data-testid="str-node-save"]').click();
		const indicators = page.locator('[data-testid="str-tree-node"][data-node-type="Performance Indicator"]');
		await expect(indicators).toHaveCount(2);
		await indicators.filter({ hasText: "telemedicine" }).click();
		await page.locator('[data-testid="str-add-target"]').click();
		const dialog = page.locator('[data-testid="str-add-target-dialog"]');
		await expect(dialog).toBeVisible();
		await expect(dialog.locator('[data-testid="str-target-unit"]')).toHaveText("Percentage");
		await dialog.locator('[data-testid="str-target-period"]').selectOption("2027-2028");
		await dialog.locator('[data-testid="str-target-value"]').fill("60");
		await dialog.locator('[data-testid="str-target-confirm"]').click();
		await expect(dialog).toBeHidden();
		await expect(page.locator('[data-testid="str-target-row"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="str-target-result"]')).toHaveText("At least 60%");

		// §12.3 — one target per Fiscal Year; refused inline in the dialog, never as a Frappe modal.
		await page.locator('[data-testid="str-add-target"]').click();
		await dialog.locator('[data-testid="str-target-period"]').selectOption("2027-2028");
		await dialog.locator('[data-testid="str-target-value"]').fill("70");
		await dialog.locator('[data-testid="str-target-confirm"]').click();
		await expect(dialog.locator('[data-testid="str-add-target-error"]')).toContainText("already has a target for 2027-2028");
		await expectNoFrappeModal(page);
		await page.keyboard.press("Escape");
		await expect(dialog).toBeHidden();

		// Reload keeps the §10 route and the saved structure.
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan"]')).toHaveAttribute("data-tab", "structure");
		await expect(page.locator('[data-testid="str-tree-node"]')).toHaveCount(9);

		// Submit for approval.
		await page.locator('[data-testid="str-submit"]').click();
		await page.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Submitted for approval", { timeout: 30_000 });
		await expectScreen(page, "plan");
		await expect(page).toHaveURL(new RegExp(`/strategy/plan/${fixture.plan_reference}$`));
		await expect(page.locator('[data-testid="str-readiness-row"] .kt-status')).toHaveText(["Ready", "Ready", "Ready", "Ready"]);
		await expect(page.locator('[data-testid="str-submit"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-open-approval"]')).toBeVisible();

		// History is version-scoped and names the actor; back/forward restore the tab.
		await page.locator('[data-testid="str-tab-history"]').click();
		await expect(page).toHaveURL(/\/history$/);
		const first = page.locator('[data-testid="str-history-row"]').first();
		await expect(first).toContainText("Submit for approval");
		await expect(first).toContainText("Esther Muthoni");
		await page.goBack();
		await expect(page.locator('[data-testid="str-plan"]')).toHaveAttribute("data-tab", "overview");
		await page.goForward();
		await expect(page.locator('[data-testid="str-plan"]')).toHaveAttribute("data-tab", "history");
		await expect(page.locator('[data-testid="str-history-row"]').first()).toBeVisible();

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("creates a brand-new Draft plan and is told inline what is missing", async ({ page }) => {
		resetFixture("reset_default");
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		await page.locator('[data-testid="str-new-plan"]').click();
		await expect(page).toHaveURL(/\/strategy\/new$/);
		await expect(page.locator('[data-testid="str-new-plan-form"]')).toBeVisible();

		// AGENTS.md §6.10 — a missing field is reported next to the field, not as a Message dialog.
		await page.locator('[data-testid="str-save-draft"]').click();
		await expect(page.locator('[data-testid="str-field-error-title"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-field-error-period-start"]')).toBeVisible();
		await expectNoFrappeModal(page);
		await expect(page.locator(".modal-title", { hasText: "Message" })).toHaveCount(0);

		await page.locator('[data-testid="str-plan-title"]').fill("Playwright — Strategy Plan (Demo)");
		await page.locator('[data-testid="str-period-start"]').fill("2028-07-01");
		await page.locator('[data-testid="str-period-end"]').fill("2033-06-30");
		await page.locator('[data-testid="str-save-draft"]').click();

		// STR-AC-003 — the server assigns the generated references.
		await expect(page).toHaveURL(/\/strategy\/plan\/MOH-SP-\d{4}$/, { timeout: 30_000 });
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-eyebrow"]')).toHaveText(/^MOH-SP-\d{4}$/);
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Draft");
		await expect(page.locator('[data-testid="str-identity-edit"]')).toBeVisible();
		await expect(page.locator('[data-testid="str-readiness-row"] .kt-status')).toHaveText(["Ready", "Not ready", "Not ready", "Ready"]);

		await page.locator('[data-testid="str-tab-structure"]').click();
		await expect(page).toHaveURL(/\/version\/1\/structure$/);
		await page.locator('[data-testid="str-add-pillar"]').click();
		await page.locator('[data-testid="str-node-title"]').fill("Universal health coverage");
		await page.locator('[data-testid="str-node-save"]').click();
		await expect(page.locator('[data-testid="str-tree-node"][data-node-type="Pillar"]')).toHaveCount(1);

		// STR-BR-012 — readiness blocks submission, inline and without changing status.
		await page.locator('[data-testid="str-submit"]').click();
		await page.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page.locator('[data-testid="str-action-error"]')).toContainText("Not ready for submission");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Draft");
		await expectNoFrappeModal(page);

		// Both plans in the register; the status filter is server-side (§12.1).
		await gotoStrategy(page);
		await expectScreen(page, "portfolio");
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(2);
		await page.locator('[data-testid="str-status-filter"]').selectOption("Draft");
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(1);
		await expect(page.locator('[data-testid="str-count-label"]')).toHaveText("Showing 1 of 1 plan");
		await page.locator('[data-testid="str-search"]').fill("nothing matches this");
		await expect(page.locator('[data-testid="str-no-match"]')).toBeVisible();
		await page.locator('[data-testid="str-clear-filters"]').click();
		await expect(page.locator('[data-testid="str-plan-row"]')).toHaveCount(2);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
