/**
 * F5 — Add Program → new row visible in tree  (submit form, verify tree update)
 * F6 — Full happy-path: Add Sub-program → Indicator → Target (nested creation)
 * F7 — Edit + Save a Target node (modal pre-fills, saves correctly)
 */
import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

const DRAFT_PLAN = 'MOH-SP-2026-0031';

// ── Helpers ───────────────────────────────────────────────────────────────────

async function openWorkbench(page: import('@playwright/test').Page) {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);
	const card = page.locator(`[data-plan-name="${DRAFT_PLAN}"]`);
	await expect(card).toBeVisible({ timeout: 25_000 });
	await card.locator('.kt-sph-card-title').first().click();
	await expect(page).toHaveURL(/strategy-builder/, { timeout: 20_000 });
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 60_000 });
}

async function waitForTree(page: import('@playwright/test').Page) {
	await expect(page.getByTestId('swb-tree-body')).toBeVisible({ timeout: 30_000 });
	/* Wait until at least one program row is rendered */
	await expect(page.locator('.kt-swb-prog-row').first()).toBeVisible({ timeout: 15_000 });
}

async function expandAll(page: import('@playwright/test').Page) {
	const expandBtn = page.getByTestId('swb-expand-all-btn');
	if (await expandBtn.count() > 0) {
		const expanded = await expandBtn.getAttribute('data-expanded');
		if (expanded !== 'true') await expandBtn.click();
		/* Give the tree a moment to re-render */
		await page.waitForTimeout(600);
	}
}

async function fillModal(
	page: import('@playwright/test').Page,
	fieldName: string,
	value: string,
) {
	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 8_000 });
	await modal.locator(`[name="${fieldName}"]`).fill(value);
	await page.getByTestId('kt-modal-submit').click();
	await expect(modal).not.toBeVisible({ timeout: 10_000 });
}

// ── F5: Add Program → new row appears in tree ─────────────────────────────────

test('F5: submitting Add Program form adds the row to the tree', async ({ page }) => {
	await openWorkbench(page);
	await waitForTree(page);

	const addBtn = page.getByTestId('swb-add-program-btn');
	await expect(addBtn).toBeEnabled({ timeout: 10_000 });
	await addBtn.click();

	const uniqueTitle = `F5 Program ${Date.now()}`;
	await fillModal(page, 'node_title', uniqueTitle);

	/* Tree reloads — new row should be selected and visible */
	const selectedRow = page.locator('.kt-swb-selected');
	await expect(selectedRow).toBeVisible({ timeout: 15_000 });
	await expect(selectedRow).toContainText(uniqueTitle);
});

// ── F6: Add Sub-program → Indicator → Target (nested happy path) ──────────────

test('F6: can add a Sub-program under an existing Program', async ({ page }) => {
	await openWorkbench(page);
	await waitForTree(page);

	/* Click "Add Sub-program" on the first Program row */
	const addSpBtn = page.locator('[data-act="add"][data-ntype="SubProgram"]').first();
	await expect(addSpBtn).toBeVisible({ timeout: 10_000 });
	await addSpBtn.click();

	const spTitle = `F6 Sub-program ${Date.now()}`;
	await fillModal(page, 'node_title', spTitle);

	/* New sub-program row should be selected */
	const selectedRow = page.locator('.kt-swb-selected');
	await expect(selectedRow).toBeVisible({ timeout: 15_000 });
	await expect(selectedRow).toContainText(spTitle);
});

test('F6: can add an Indicator under an existing Sub-program', async ({ page }) => {
	await openWorkbench(page);
	await waitForTree(page);
	await expandAll(page);

	/* Click "Add Indicator" on the first visible Sub-program row */
	const addIndBtn = page.locator('[data-act="add"][data-ntype="Indicator"]').first();
	await expect(addIndBtn).toBeVisible({ timeout: 12_000 });
	await addIndBtn.click();

	const indTitle = `F6 Indicator ${Date.now()}`;
	await fillModal(page, 'node_title', indTitle);

	const selectedRow = page.locator('.kt-swb-selected');
	await expect(selectedRow).toBeVisible({ timeout: 15_000 });
	await expect(selectedRow).toContainText(indTitle);
});

test('F6: can add a Target under an existing Indicator', async ({ page }) => {
	await openWorkbench(page);
	await waitForTree(page);
	await expandAll(page);

	/* Click "Add Target" on the first visible Indicator row */
	const addTgtBtn = page.locator('[data-act="add"][data-ntype="Target"]').first();
	await expect(addTgtBtn).toBeVisible({ timeout: 12_000 });
	await addTgtBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 8_000 });

	const tgtTitle = `F6 Target ${Date.now()}`;
	await modal.locator('[name="node_title"]').fill(tgtTitle);

	/* Measurement type defaults to Numeric — fill required target value */
	const tvField = modal.locator('[name="target_value_numeric"]');
	if (await tvField.count() > 0) await tvField.fill('10');

	await page.getByTestId('kt-modal-submit').click();
	await expect(modal).not.toBeVisible({ timeout: 10_000 });

	const selectedRow = page.locator('.kt-swb-selected');
	await expect(selectedRow).toBeVisible({ timeout: 15_000 });
	await expect(selectedRow).toContainText(tgtTitle);
});

// ── F7: Edit + Save a Target node ─────────────────────────────────────────────

test('F7: Edit Target modal pre-fills title and saves updated value', async ({ page }) => {
	await openWorkbench(page);
	await waitForTree(page);
	await expandAll(page);

	/* Click edit on the first Target row */
	const editBtn = page.locator('[data-act="edit"][data-ntype="Target"]').first();
	await expect(editBtn).toBeVisible({ timeout: 12_000 });
	await editBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 8_000 });
	await expect(page.getByTestId('kt-modal-title')).toContainText('Edit');

	/* Title field must be pre-filled */
	const titleField = modal.locator('[name="node_title"]');
	await expect(titleField).toBeVisible();
	const originalTitle = await titleField.inputValue();
	expect(originalTitle.length).toBeGreaterThan(0);

	/* Update the title */
	const updatedTitle = `Edited Target ${Date.now()}`;
	await titleField.fill(updatedTitle);
	await page.getByTestId('kt-modal-submit').click();
	await expect(modal).not.toBeVisible({ timeout: 10_000 });

	/* Tree reloads — the updated title should appear in a Target row */
	await expect(page.locator('[data-ntype="Target"]').filter({ hasText: updatedTitle }))
		.toBeVisible({ timeout: 15_000 });
});

test('F7: Edit Target modal cancel leaves tree unchanged', async ({ page }) => {
	await openWorkbench(page);
	await waitForTree(page);
	await expandAll(page);

	const editBtn = page.locator('[data-act="edit"][data-ntype="Target"]').first();
	await expect(editBtn).toBeVisible({ timeout: 12_000 });

	/* Read the original title before editing */
	const tgtRow = editBtn.locator('..').locator('..').locator('..');
	await editBtn.click();

	const modal = page.getByTestId('kt-modal-box');
	await expect(modal).toBeVisible({ timeout: 8_000 });

	const originalTitle = await modal.locator('[name="node_title"]').inputValue();

	/* Cancel without saving */
	await page.getByTestId('kt-modal-cancel').click();
	await expect(modal).not.toBeVisible({ timeout: 5_000 });

	/* Original title must still be in the tree */
	await expect(page.locator('[data-ntype="Target"]').filter({ hasText: originalTitle }))
		.toBeVisible({ timeout: 10_000 });
});
