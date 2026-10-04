import { expect, test } from "@playwright/test";

import { login } from "../../helpers/auth";
import {
	AUTHOR,
	PASSWORD,
	collectConsoleErrors,
	expectNoFrappeModal,
	expectScreen,
	gotoStrategy,
	resetFixture,
	type DefaultFixture,
} from "./helpers";

/**
 * GitHub #13, #14 and #15 — pending work is visible and never lost silently.
 *
 * #15: Update plan starts the Draft from a full copy of the current plan,
 *      so nothing has to be typed again.
 * #13: Submit for approval asks once before the draft is locked for review.
 * #14: switching items in the structure keeps typed values (by design) and
 *      the page shows a discreet "Unsaved changes" tag until they are saved;
 *      the plan details form offers Save / Discard / Stay before leaving.
 */

test.describe.configure({ mode: "serial", timeout: 240_000 });

const unsaved = '[data-testid="str-unsaved-indicator"]';

test.describe("Strategy — unsaved changes and Update plan copy", () => {
	let fixture: DefaultFixture;

	test.beforeAll(() => {
		fixture = resetFixture("reset_default");
	});

	test.afterAll(() => {
		resetFixture("reset_default");
	});

	test("Update plan copies the whole current plan into the draft", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);

		await gotoStrategy(page, `/plan/${fixture.plan_reference}/version/1/structure`);
		await expectScreen(page, "plan");
		const currentNodes = page.locator('[data-testid="str-tree-node"]');
		await expect(currentNodes.first()).toBeVisible();
		// Compare item text only; the editable tree adds "Add …" child buttons.
		const itemText = (texts: string[]) =>
			texts.map((t) => t.replace(/\bAdd (pillar|programme|sub-programme|objective|indicator|target)\b/gi, "").replace(/\s+/g, " ").trim());
		const currentTitles = itemText(await currentNodes.allInnerTexts());
		expect(currentTitles.length).toBeGreaterThan(3);

		await gotoStrategy(page, `/plan/${fixture.plan_reference}`);
		await expectScreen(page, "plan");
		await page.locator('[data-testid="str-update-plan"]').click();
		await page.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page).toHaveURL(/\/version\/2\/structure$/, { timeout: 30_000 });
		await expectScreen(page, "plan");

		const draftNodes = page.locator('[data-testid="str-tree-node"]');
		await expect(draftNodes).toHaveCount(currentTitles.length);
		expect(itemText(await draftNodes.allInnerTexts())).toEqual(currentTitles);
		await expect(page.locator(unsaved)).toHaveCount(0);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("structure edits survive switching items and show an Unsaved changes tag", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/plan/${fixture.plan_reference}/version/2/structure`);
		await expectScreen(page, "plan");
		await expect(page.locator(unsaved)).toHaveCount(0);

		const objective = page.locator('[data-testid="str-tree-node"][data-node-type="Strategic Objective"]').first();
		await objective.click();
		const edited = "Strengthen interoperable national digital health services (edited)";
		await page.locator('[data-testid="str-node-title"]').fill(edited);
		await expect(page.locator(unsaved)).toHaveText("Unsaved changes");

		// Switching to another item is not a leave: no dialog, the typed value stays.
		await page.locator('[data-testid="str-tree-node"][data-node-type="Pillar"]').first().click();
		await expect(page.locator('[data-testid="str-unsaved-dialog"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="str-selected-type"]')).toHaveText("Pillar");
		await expect(page.locator(unsaved)).toBeVisible();
		await objective.click();
		await expect(page.locator('[data-testid="str-node-title"]')).toHaveValue(edited);

		await page.locator('[data-testid="str-save-changes"]').click();
		await expect(page.locator('[data-testid="str-structure-editor"]')).toHaveAttribute("data-dirty", "false", { timeout: 30_000 });
		await expect(page.locator(unsaved)).toHaveCount(0);
		await expectNoFrappeModal(page);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("plan details offer Save / Discard / Stay before leaving", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/plan/${fixture.plan_reference}/version/2`);
		await expectScreen(page, "plan");
		const useUntil = page.locator('[data-testid="str-use-until"]');
		const saved = await useUntil.inputValue();
		expect(saved).not.toBe("");
		await expect(page.locator(unsaved)).toHaveCount(0);

		await useUntil.fill("2028-06-29");
		await expect(page.locator(unsaved)).toHaveText("Unsaved changes");

		// Stay here keeps the page and the typed value.
		await page.locator('[data-testid="str-tab-history"]').click();
		const guard = page.locator('[data-testid="str-details-unsaved-dialog"]');
		await expect(guard).toBeVisible();
		await expect(guard).toContainText("Discard unsaved changes");
		await guard.locator('[data-testid="str-confirm-cancel"]').click();
		await expect(guard).toBeHidden();
		await expect(page.locator('[data-testid="str-plan"]')).toHaveAttribute("data-tab", "overview");
		await expect(useUntil).toHaveValue("2028-06-29");

		// Discard restores the saved value and continues to the chosen tab.
		await page.locator('[data-testid="str-tab-history"]').click();
		await guard.locator('[data-testid="str-confirm-secondary"]').click();
		await expect(page).toHaveURL(/\/version\/2\/history$/);
		await page.locator('[data-testid="str-tab-overview"]').click();
		await expect(page.locator('[data-testid="str-plan"]')).toHaveAttribute("data-tab", "overview");
		await expect(useUntil).toHaveValue(saved);
		await expect(page.locator(unsaved)).toHaveCount(0);

		// Save commits the value, then continues.
		await useUntil.fill("2028-06-29");
		await page.locator('[data-testid="str-tab-history"]').click();
		await guard.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page).toHaveURL(/\/version\/2\/history$/, { timeout: 30_000 });
		await page.reload({ waitUntil: "domcontentloaded" });
		await expectScreen(page, "plan");
		await page.locator('[data-testid="str-tab-overview"]').click();
		await expect(useUntil).toHaveValue("2028-06-29");
		await expect(page.locator(unsaved)).toHaveCount(0);
		await expectNoFrappeModal(page);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("the rail breadcrumb and browser Back ask before leaving unsaved work", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/plan/${fixture.plan_reference}/version/2`);
		await expectScreen(page, "plan");
		await page.locator('[data-testid="str-tab-structure"]').click();
		await expect(page).toHaveURL(/\/version\/2\/structure$/);
		await expectScreen(page, "plan");

		await page.locator('[data-testid="str-tree-node"][data-node-type="Pillar"]').first().click();
		await page.locator('[data-testid="str-node-title"]').fill("Digital health systems (unsaved)");
		const guard = page.locator('[data-testid="str-unsaved-dialog"]');

		// The breadcrumb leaves the screen: held, and Stay here keeps everything.
		await page.locator(".kt-rail-crumb-link", { hasText: "Strategy Alignment" }).click();
		await expect(guard).toBeVisible();
		await guard.locator('[data-testid="str-confirm-cancel"]').click();
		await expect(guard).toBeHidden();
		await expect(page).toHaveURL(/\/version\/2\/structure$/);
		await expect(page.locator('[data-testid="str-node-title"]')).toHaveValue("Digital health systems (unsaved)");

		// Browser Back: held with the page's URL put back; Discard then goes back.
		await page.goBack();
		await expect(guard).toBeVisible();
		await expect(page).toHaveURL(/\/version\/2\/structure$/);
		await guard.locator('[data-testid="str-confirm-secondary"]').click();
		await expect(page).toHaveURL(/\/version\/2$/, { timeout: 30_000 });
		await expect(page.locator('[data-testid="str-plan"]')).toHaveAttribute("data-tab", "overview");

		// Plan details: the breadcrumb is held the same way.
		await page.locator('[data-testid="str-use-until"]').fill("2028-06-28");
		await page.locator(".kt-rail-crumb-link", { hasText: "Strategy Alignment" }).click();
		const detailsGuard = page.locator('[data-testid="str-details-unsaved-dialog"]');
		await expect(detailsGuard).toBeVisible();
		await detailsGuard.locator('[data-testid="str-confirm-secondary"]').click();
		await expect(page).toHaveURL(/\/strategy$/, { timeout: 30_000 });
		await expectScreen(page, "portfolio");

		// Nothing unsaved: leaving is not asked about.
		await gotoStrategy(page, `/plan/${fixture.plan_reference}/version/2/structure`);
		await expectScreen(page, "plan");
		await page.locator(".kt-rail-crumb-link", { hasText: "Strategy Alignment" }).click();
		await expect(page).toHaveURL(/\/strategy$/);
		await expect(guard).toHaveCount(0);
		await expectNoFrappeModal(page);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});

	test("Submit for approval asks for confirmation first", async ({ page }) => {
		const errors = collectConsoleErrors(page);
		await login(page, AUTHOR, PASSWORD);
		await gotoStrategy(page, `/plan/${fixture.plan_reference}/version/2/structure`);
		await expectScreen(page, "plan");

		const confirm = page.locator('[data-testid="str-confirm-submit"]');
		await page.locator('[data-testid="str-submit"]').click();
		await expect(confirm).toBeVisible();
		await expect(confirm).toContainText("Submit this version for approval?");
		await confirm.locator('[data-testid="str-confirm-cancel"]').click();
		await expect(confirm).toBeHidden();
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Draft update");
		await expect(page).toHaveURL(/\/version\/2\/structure$/);

		await page.locator('[data-testid="str-submit"]').click();
		await confirm.locator('[data-testid="str-confirm-ok"]').click();
		await expect(page).toHaveURL(/\/version\/2$/, { timeout: 30_000 });
		await expectScreen(page, "plan");
		await expect(page.locator('[data-testid="str-plan-status"]')).toHaveText("Awaiting approval");
		await expect(page.locator('[data-testid="str-unsaved-dialog"]')).toHaveCount(0);
		await expectNoFrappeModal(page);

		expect(errors, `page console errors: ${errors.join(" | ")}`).toEqual([]);
	});
});
