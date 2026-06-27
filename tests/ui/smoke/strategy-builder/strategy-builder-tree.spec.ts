/**
 * Live hierarchy tree smoke tests.
 *
 * SEEDED_PLAN (PE-MOH-SP-2026-0077) — Active status — used for read-only / lock tests.
 * DRAFT_PLAN  (MOH-SP-2026-0031)    — Draft status  — used for create/edit modal tests.
 */
import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

const SEEDED_PLAN = 'PE-MOH-SP-2026-0077';
const DRAFT_PLAN  = 'MOH-SP-2026-0031';

async function openWorkbench(page: import('@playwright/test').Page, planName: string) {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const planCard = page.locator(`[data-plan-name="${planName}"]`);
	await expect(planCard).toBeVisible({ timeout: 25_000 });
	await planCard.locator('.kt-sph-card-title').first().click();

	await expect(page).toHaveURL(/strategy-builder/, { timeout: 20_000 });
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 60_000 });
}

async function openSeededWorkbench(page: import('@playwright/test').Page) {
	return openWorkbench(page, SEEDED_PLAN);
}

async function openDraftWorkbench(page: import('@playwright/test').Page) {
	return openWorkbench(page, DRAFT_PLAN);
}

async function waitForTree(page: import('@playwright/test').Page) {
	const treeBody = page.getByTestId('swb-tree-body');
	await expect(treeBody).toBeVisible({ timeout: 30_000 });
	await expect(page.locator('.kt-swb-prog-row').first()).toBeVisible({ timeout: 60_000 });
}

// ── Rendering ─────────────────────────────────────────────────────────────────

test('Tree body renders with live program rows', async ({ page }) => {
	await openSeededWorkbench(page);
	await waitForTree(page);

	const progRows = page.locator('.kt-swb-prog-row');
	const count = await progRows.count();
	expect(count).toBeGreaterThanOrEqual(1);
});

test('Programs start expanded showing sub-program rows', async ({ page }) => {
	await openSeededWorkbench(page);
	await waitForTree(page);

	/* After load Programs are auto-expanded; sub-program (obj-row) must be visible */
	await expect(page.locator('.kt-swb-obj-row').first()).toBeVisible({ timeout: 10_000 });
});

// ── Expand / Collapse ─────────────────────────────────────────────────────────

test('Clicking expand arrow on a Sub-program reveals Indicator rows', async ({ page }) => {
	await openSeededWorkbench(page);
	await waitForTree(page);

	/* Find first sub-program ROW div (not the add-button which also has data-ntype) */
	const firstSP = page.locator('div[data-ntype="SubProgram"]').first();
	await expect(firstSP).toBeVisible({ timeout: 10_000 });

	/* Click its expand arrow */
	const arrow = firstSP.locator('[data-expand]').first();
	await arrow.click();

	/* An Indicator row should now appear */
	await expect(page.locator('div[data-ntype="Indicator"]').first()).toBeVisible({ timeout: 8_000 });
});

test('Clicking expand on an Indicator reveals Target rows', async ({ page }) => {
	await openSeededWorkbench(page);
	await waitForTree(page);

	/* Ensure sub-program is expanded first */
	const firstSP = page.locator('div[data-ntype="SubProgram"]').first();
	await firstSP.locator('[data-expand]').first().click();
	const firstInd = page.locator('div[data-ntype="Indicator"]').first();
	await expect(firstInd).toBeVisible({ timeout: 8_000 });

	/* Expand first indicator */
	await firstInd.locator('[data-expand]').first().click();
	await expect(page.locator('div[data-ntype="Target"]').first()).toBeVisible({ timeout: 8_000 });
});

test('Expand-all button shows all 4 levels', async ({ page }) => {
	await openSeededWorkbench(page);
	await waitForTree(page);

	await page.getByTestId('swb-expand-all-btn').click();

	/* After expand-all every level type should be visible */
	await expect(page.locator('div[data-ntype="SubProgram"]').first()).toBeVisible();
	await expect(page.locator('div[data-ntype="Indicator"]').first()).toBeVisible();
	await expect(page.locator('div[data-ntype="Target"]').first()).toBeVisible({ timeout: 10_000 });
});

// ── Toolbar: search ──────────────────────────────────────────────────────────

test('Search input filters program rows to matching title', async ({ page }) => {
	await openSeededWorkbench(page);
	await waitForTree(page);

	const searchInput = page.getByTestId('swb-tree-search');
	await expect(searchInput).toBeVisible();

	/* Count before filtering */
	const beforeCount = await page.locator('.kt-swb-prog-row').count();

	/* Type a string unlikely to match all programs */
	await searchInput.fill('zzzznonexistent999');
	await expect(page.locator('.kt-swb-prog-row')).toHaveCount(0, { timeout: 5_000 });

	/* Clear — all programs return */
	await searchInput.fill('');
	await expect(page.locator('.kt-swb-prog-row')).toHaveCount(beforeCount, { timeout: 5_000 });
});

// ── Add dialogs (Draft plan) ──────────────────────────────────────────────────

test('Toolbar + Program button opens Add Program modal', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	await page.getByTestId('swb-add-program-btn').click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });
	await expect(page.getByTestId('kt-modal-title')).toContainText('Add Program');

	await page.keyboard.press('Escape');
	await expect(modal).not.toBeVisible({ timeout: 3_000 });
});

test('Inline + Sub-program row-action opens Add Sub-program modal', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	const addBtn = page
		.locator('[data-ntype="Program"]')
		.first()
		.locator('[data-act="add"][data-ntype="SubProgram"]')
		.first();
	await expect(addBtn).toBeVisible({ timeout: 8_000 });
	await addBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });
	await expect(page.getByTestId('kt-modal-title')).toContainText('Sub-program');

	await page.keyboard.press('Escape');
});

test('Add Program modal Cancel button closes modal', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	await page.getByTestId('swb-add-program-btn').click();
	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });

	await page.getByTestId('kt-modal-cancel').click();
	await expect(modal).not.toBeVisible({ timeout: 3_000 });
});

test('Add Target modal opens from inline + button and shows measurement type select', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	/* Expand sub-programs so Indicator rows appear */
	await page.getByTestId('swb-expand-all-btn').click();
	const firstInd = page.locator('div[data-ntype="Indicator"]').first();
	await expect(firstInd).toBeVisible({ timeout: 15_000 });

	const addTargetBtn = firstInd
		.locator('[data-act="add"][data-ntype="Target"]')
		.first();
	await expect(addTargetBtn).toBeVisible({ timeout: 8_000 });
	await addTargetBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });
	await expect(page.getByTestId('kt-modal-title')).toContainText('Target');

	/* Measurement Type select must be present */
	const mtSelect = modal.locator('[name="measurement_type"]');
	await expect(mtSelect).toBeVisible();

	await page.keyboard.press('Escape');
});

test('Add Target modal — Milestone type hides numeric fields, shows description', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	await page.getByTestId('swb-expand-all-btn').click();
	const firstInd = page.locator('div[data-ntype="Indicator"]').first();
	await expect(firstInd).toBeVisible({ timeout: 15_000 });

	const addTargetBtn = firstInd
		.locator('[data-act="add"][data-ntype="Target"]')
		.first();
	await addTargetBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });

	/* Switch to Milestone */
	await modal.locator('[name="measurement_type"]').selectOption('Milestone');

	/* Numeric block hidden, text block visible */
	await expect(modal.locator('.kt-swb-mt-numeric')).toBeHidden();
	await expect(modal.locator('.kt-swb-mt-text')).toBeVisible();

	/* Switch back to Numeric */
	await modal.locator('[name="measurement_type"]').selectOption('Numeric');
	await expect(modal.locator('.kt-swb-mt-numeric')).toBeVisible();
	await expect(modal.locator('.kt-swb-mt-text')).toBeHidden();

	await page.keyboard.press('Escape');
});

// ── Lock banner (Active plan) ──────────────────────────────────────────────────

test('Active plan shows lock banner and disables Add Program button', async ({ page }) => {
	await openSeededWorkbench(page);
	await waitForTree(page);

	/* Lock banner must be visible */
	await expect(page.getByTestId('swb-lock-banner')).toBeVisible({ timeout: 10_000 });

	/* Add Program button must be disabled */
	const addProgBtn = page.getByTestId('swb-add-program-btn');
	await expect(addProgBtn).toBeDisabled({ timeout: 5_000 });
});

// ── Context menu (Draft plan) ─────────────────────────────────────────────────

test('"⋮" more menu on a Program shows Edit and Delete', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	const moreBtn = page
		.locator('[data-ntype="Program"]')
		.first()
		.locator('[data-act="more"]')
		.first();
	await expect(moreBtn).toBeVisible({ timeout: 8_000 });
	await moreBtn.click();

	const menu = page.locator('.kt-swb-ctx-menu');
	await expect(menu).toBeVisible({ timeout: 5_000 });
	await expect(menu).toContainText('Edit');
	await expect(menu).toContainText('Delete');

	/* Close by clicking elsewhere */
	await page.keyboard.press('Escape');
});

test('Edit from context menu on a Program opens Edit modal with pre-filled title', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	const firstProg = page.locator('div[data-ntype="Program"]').first();
	const moreBtn = firstProg.locator('[data-act="more"]').first();
	await expect(moreBtn).toBeVisible({ timeout: 8_000 });
	await moreBtn.click();

	const menu = page.locator('.kt-swb-ctx-menu');
	await expect(menu).toBeVisible({ timeout: 3_000 });
	await menu.locator('[data-act2="edit"]').click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });
	await expect(page.getByTestId('kt-modal-title')).toContainText('Edit');

	/* Title input should have a non-empty pre-filled value */
	const titleInput = modal.locator('[name="node_title"]');
	await expect(titleInput).toBeVisible();
	const val = await titleInput.inputValue();
	expect(val.length).toBeGreaterThan(0);

	await page.keyboard.press('Escape');
});

// ── Target edit button (Draft plan) ────────────────────────────────────────────

test('Edit button on a Target opens Edit Target modal', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	/* Expand-all to expose Targets */
	await page.getByTestId('swb-expand-all-btn').click();
	const firstTarget = page.locator('div[data-ntype="Target"]').first();
	await expect(firstTarget).toBeVisible({ timeout: 15_000 });

	const editBtn = firstTarget.locator('[data-act="edit"]').first();
	await expect(editBtn).toBeVisible({ timeout: 5_000 });
	await editBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });
	await expect(page.getByTestId('kt-modal-title')).toContainText('Edit');

	/* Measurement type select must be present */
	await expect(modal.locator('[name="measurement_type"]')).toBeVisible();

	await page.keyboard.press('Escape');
});

test('Edit Target modal pre-fills node_title from existing data', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	await page.getByTestId('swb-expand-all-btn').click();
	const firstTarget = page.locator('div[data-ntype="Target"]').first();
	await expect(firstTarget).toBeVisible({ timeout: 15_000 });

	const editBtn = firstTarget.locator('[data-act="edit"]').first();
	await editBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });

	const titleInput = modal.locator('[name="node_title"]');
	await expect(titleInput).toBeVisible();
	const val = await titleInput.inputValue();
	expect(val.length).toBeGreaterThan(0);

	await page.keyboard.press('Escape');
});

// ── Edit Plan modal (Draft plan) ────────────────────────────────────────────────

test('Edit Plan button opens plan edit modal with pre-filled title', async ({ page }) => {
	await openDraftWorkbench(page);
	await waitForTree(page);

	const editPlanBtn = page.locator('[data-swb="edit-plan-btn"]');
	await expect(editPlanBtn).toBeVisible({ timeout: 10_000 });
	await editPlanBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });
	await expect(page.getByTestId('kt-modal-title')).toContainText('Edit Plan');

	const titleInput = modal.locator('[name="plan_title"]');
	await expect(titleInput).toBeVisible();
	const val = await titleInput.inputValue();
	expect(val.length).toBeGreaterThan(0);

	await page.keyboard.press('Escape');
});

// ── C19: post-create focus / scroll-to-new-node ───────────────────────────────

test('Creating a Program selects and highlights the new row in the tree', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openDraftWorkbench(page);
	await waitForTree(page);

	/* Open the Add Program modal */
	const addBtn = page.getByTestId('swb-add-program-btn');
	await expect(addBtn).toBeVisible({ timeout: 10_000 });
	await addBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 5_000 });

	/* Fill in a unique title */
	const uniqueTitle = `AutoTest Program ${Date.now()}`;
	await modal.locator('[name="node_title"]').fill(uniqueTitle);

	/* Submit */
	await page.getByTestId('kt-modal-submit').click();
	await expect(modal).not.toBeVisible({ timeout: 10_000 });

	/* Tree reloads — new row should exist and carry the .kt-swb-selected class */
	const newRow = page.locator('.kt-swb-selected');
	await expect(newRow).toBeVisible({ timeout: 15_000 });

	/* Confirm it is the row we just created */
	await expect(newRow).toContainText(uniqueTitle);
});
