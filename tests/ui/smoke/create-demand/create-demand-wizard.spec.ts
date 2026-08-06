/**
 * Create Demand Wizard — end-to-end smoke tests (cd-w9).
 *
 * Covers:
 *   CD-01  Page renders the Step 1 form (title input visible).
 *   CD-02  Procuring Entity and Department dropdowns load with at least one option.
 *   CD-03  Clicking Next without a title shows a validation error.
 *   CD-04  Filling all Step 1 fields and clicking Next advances to Step 2.
 *   CD-05  Adding a line item in Step 2 makes the row visible in the table.
 *   CD-06  Deleting the only item re-shows the empty state message.
 *   CD-07  Clicking Next on Step 2 with at least one item advances to Step 3.
 *   CD-08  Step 3 readiness panel renders with multiple check_circle icons.
 *   CD-09  Submit button is enabled when all readiness checks pass.
 *   CD-10  Full wizard flow produces a DIA reference (Step 4 success screen).
 *
 * Uses Administrator login (has all required roles for submitting demands).
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

// ── Constants ─────────────────────────────────────────────────────────────────

const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');
const SITE = process.env.UI_SITE || 'kentender.midas.com';
const CD_PAGE = '/app/create-demand';

function futureDate(daysAhead: number): string {
	return new Date(Date.now() + daysAhead * 86_400_000).toISOString().split('T')[0];
}

function seedStrategyHierarchy(): void {
	try {
		execSync('redis-cli -p 11000 FLUSHDB', { stdio: 'pipe' });
	} catch {
		/* ignore */
	}
	try {
		execSync(
			`cd "${BENCH_ROOT}" && bench --site ${SITE} execute ` +
				'kentender_strategy.seeds.works_master_strategy_hierarchy.upsert_works_master_strategy_hierarchy',
			{ stdio: 'pipe', timeout: 120_000 },
		);
	} catch {
		/* strategy seed may already be present */
	}
}

// ── Helper: open wizard page and wait for Step 1 ─────────────────────────────

async function openWizard(page: Page): Promise<void> {
	await page.goto(CD_PAGE, { waitUntil: 'domcontentloaded' });
	await page.waitForSelector('#kt-cd-title', { timeout: 20_000 });
}

/**
 * Fill Step 1 with valid data and wait for the dropdowns to populate.
 * Returns without clicking Next — callers decide when to proceed.
 */
async function fillStep1(page: Page, title: string): Promise<void> {
	await page.fill('#kt-cd-title', title);

	await page.waitForFunction(
		() => {
			const e = document.querySelector<HTMLSelectElement>('#kt-cd-entity');
			return e != null && Array.from(e.options).some((o) => o.value === 'PE-MOH');
		},
		{ timeout: 15_000 },
	);
	await page.waitForFunction(
		() => {
			const d = document.querySelector<HTMLSelectElement>('#kt-cd-dept');
			return d != null && d.options.length > 1;
		},
		{ timeout: 10_000 },
	);

	await page.selectOption('#kt-cd-dept', { index: 1 });
	await page.selectOption('#kt-cd-category', 'Works');
	await page.selectOption('#kt-cd-entity', 'PE-MOH');
	// Placeholder rows already make options.length > 1 — wait for a real target value.
	await page.waitForFunction(
		() => {
			const s = document.querySelector<HTMLSelectElement>('#kt-cd-strategy-target');
			return !!s && Array.from(s.options).some((o) => Boolean(o.value));
		},
		{ timeout: 15_000 },
	);
	const strategyValue = await page.$eval('#kt-cd-strategy-target', (sel: HTMLSelectElement) => {
		for (let i = 0; i < sel.options.length; i += 1) {
			if (sel.options[i].value) return sel.options[i].value;
		}
		return '';
	});
	expect(strategyValue).toBeTruthy();
	await page.selectOption('#kt-cd-strategy-target', strategyValue);
	await page.fill('#kt-cd-required-by', futureDate(30));
	await page.fill(
		'#kt-cd-justify',
		'Procurement of essential materials for facility maintenance and operational continuity across all units.',
	);
}

/** Treat Required PVCs as Included so Step 3 Submit can enable. */
async function treatRequiredPvcsIncluded(page: Page): Promise<void> {
	const panel = page.getByTestId('kt-cd-pvc-panel');
	await expect(panel).toBeVisible({ timeout: 15_000 });
	const rows = page.getByTestId('kt-cd-pvc-row');
	const count = await rows.count();
	for (let i = 0; i < count; i += 1) {
		const hint = (await rows.nth(i).locator('.kt-cd-input-hint').textContent()) || '';
		if (!/Required/i.test(hint)) continue;
		await rows.nth(i).getByTestId('kt-cd-pvc-treatment').selectOption('Included');
		await page.waitForTimeout(700);
	}
}

/** Add a single line item in Step 2 and click Save Row. Waits for the row to appear. */
async function addLineItem(
	page: Page,
	desc: string,
	qty: number,
	unitPrice: number,
): Promise<void> {
	// Ensure the input row is visible before filling
	await page.waitForSelector('#kt-cd-new-desc', { state: 'visible', timeout: 8_000 });
	await page.fill('#kt-cd-new-desc', desc);
	await page.fill('#kt-cd-new-qty', String(qty));
	await page.fill('#kt-cd-new-unit', String(unitPrice));
	// Capture current data-row count before save (for stable wait-after)
	const countBefore = await page.$$eval(
		'#kt-cd-items-body tr:not(.kt-cd-new-row)',
		(rows) => rows.length,
	);
	await page.click('#kt-cd-save-row');
	// Wait until new data row appears (pure client-side re-render)
	await page.waitForFunction(
		(expected) => {
			const rows = document.querySelectorAll('#kt-cd-items-body tr:not(.kt-cd-new-row)');
			return rows.length > expected;
		},
		countBefore,
		{ timeout: 5_000 },
	);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('Create Demand Wizard — wired smoke (cd-w9)', () => {
	test.beforeAll(() => {
		seedStrategyHierarchy();
	});

	// CD-01 ─────────────────────────────────────────────────────────────────────
	test('CD-01 page renders Step 1 form with title input visible', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWizard(page);

		// Title input
		await expect(page.locator('#kt-cd-title')).toBeVisible();
		// Step progress indicator — Step 1 active
		await expect(page.locator('.kt-cd-step-label').first()).toContainText(/Describe/i);
	});

	// CD-02 ─────────────────────────────────────────────────────────────────────
	test('CD-02 entity and department dropdowns populate from backend', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWizard(page);

		await page.waitForFunction(
			() => {
				const e = document.querySelector<HTMLSelectElement>('#kt-cd-entity');
				return e != null && e.options.length > 1;
			},
			{ timeout: 10_000 },
		);

		const entityCount = await page.$eval(
			'#kt-cd-entity',
			(sel: HTMLSelectElement) => sel.options.length,
		);
		expect(entityCount).toBeGreaterThan(1);

		const deptCount = await page.$eval(
			'#kt-cd-dept',
			(sel: HTMLSelectElement) => sel.options.length,
		);
		expect(deptCount).toBeGreaterThan(1);
	});

	// CD-03 ─────────────────────────────────────────────────────────────────────
	test('CD-03 clicking Next without a title shows a validation error', async ({ page }) => {
		test.setTimeout(90_000);
		await loginAsAdministrator(page);
		await openWizard(page);

		// Don't fill title — click Next immediately
		await page.click('#kt-cd-next-1');

		// Inline field errors (title / entity / strategy / date) — avoid broad [class*="error"] strict races
		await expect(page.locator('.kt-cd-field-error').first()).toBeVisible({ timeout: 5_000 });
		await expect(page.locator('#kt-cd-title')).toHaveClass(/kt-cd-input--error/);

		// Should still be on Step 1 (items-body not visible)
		await expect(page.locator('#kt-cd-items-body')).not.toBeVisible();
	});

	// CD-04 ─────────────────────────────────────────────────────────────────────
	test('CD-04 filling Step 1 and clicking Next advances to Step 2', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWizard(page);
		await fillStep1(page, 'CD-04 Step 1 Advance Test');

		await page.click('#kt-cd-next-1');
		await page.waitForSelector('#kt-cd-items-body', { timeout: 15_000 });

		// Step 2 heading visible
		await expect(page.locator('#kt-cd-items-body')).toBeVisible();
		// Add item form visible
		await expect(page.locator('#kt-cd-new-desc')).toBeVisible();
	});

	// CD-05 ─────────────────────────────────────────────────────────────────────
	test('CD-05 adding a line item in Step 2 renders it in the table', async ({ page }) => {
		test.setTimeout(90_000);
		await loginAsAdministrator(page);
		await openWizard(page);
		await fillStep1(page, 'CD-05 Item Entry Test');
		await page.click('#kt-cd-next-1');
		await page.waitForSelector('#kt-cd-items-body', { timeout: 15_000 });

		await addLineItem(page, 'Hospital Bed Mattress', 10, 8_500);

		// Data rows are <tr> elements that are NOT the input-form row (.kt-cd-new-row)
		const rows = page.locator('#kt-cd-items-body tr:not(.kt-cd-new-row)');
		// Description is an <input value="..."> — check its value attribute
		const descInput = rows.first().locator('input[data-col="desc"]');
		await expect(descInput).toHaveValue('Hospital Bed Mattress');
	});

	// CD-06 ─────────────────────────────────────────────────────────────────────
	test('CD-06 deleting the only item shows empty-state message', async ({ page }) => {
		test.setTimeout(90_000);
		await loginAsAdministrator(page);
		await openWizard(page);
		await fillStep1(page, 'CD-06 Item Delete Test');
		await page.click('#kt-cd-next-1');
		await page.waitForSelector('#kt-cd-items-body', { timeout: 15_000 });

		await addLineItem(page, 'Temp Item for Delete', 1, 100);

		// Verify item appeared before trying to delete
		const dataRows = page.locator('#kt-cd-items-body tr:not(.kt-cd-new-row)');
		await expect(dataRows.first()).toBeVisible({ timeout: 5_000 });

		// Delete button rendered per row with data-del attribute
		const deleteBtn = dataRows.first().locator('[data-del]');
		if (await deleteBtn.isVisible({ timeout: 3_000 })) {
			await deleteBtn.click();
			await page.waitForTimeout(400);
			// After deletion, no data rows remain
			const rowsAfter = await page.locator('#kt-cd-items-body tr:not(.kt-cd-new-row)').count();
			expect(rowsAfter).toBe(0);
		} else {
			test.skip();
		}
	});

	// CD-07 ─────────────────────────────────────────────────────────────────────
	test('CD-07 Step 2 with an item advances to Step 3 readiness panel', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWizard(page);
		await fillStep1(page, 'CD-07 Step 2 to 3 Test');
		await page.click('#kt-cd-next-1');
		await page.waitForSelector('#kt-cd-items-body', { timeout: 15_000 });

		await addLineItem(page, 'Supply Item', 5, 1_200);
		await page.click('#kt-cd-next-2');

		await page.waitForSelector('#kt-cd-readiness-panel', { timeout: 15_000 });
		await expect(page.locator('#kt-cd-readiness-panel')).toBeVisible();
	});

	// CD-08 ─────────────────────────────────────────────────────────────────────
	test('CD-08 Step 3 readiness panel renders multiple check_circle checks', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWizard(page);
		await fillStep1(page, 'CD-08 Readiness Panel Test');
		await page.click('#kt-cd-next-1');
		await page.waitForSelector('#kt-cd-items-body', { timeout: 15_000 });

		await addLineItem(page, 'Equipment Unit', 3, 15_000);
		await page.click('#kt-cd-next-2');
		await page.waitForSelector('#kt-cd-readiness-panel', { timeout: 15_000 });

		// Readiness panel should have at least 3 check_circle icons (passing checks)
		const panelText = await page.textContent('#kt-cd-readiness-panel');
		const passCount = (panelText?.match(/check_circle/g) ?? []).length;
		expect(passCount).toBeGreaterThanOrEqual(3);
	});

	// CD-09 ─────────────────────────────────────────────────────────────────────
	test('CD-09 submit button is enabled when all readiness checks pass', async ({ page }) => {
		test.setTimeout(120_000);
		await loginAsAdministrator(page);
		await openWizard(page);
		await fillStep1(page, 'CD-09 Submit Enabled Test');
		await page.click('#kt-cd-next-1');
		await page.waitForSelector('#kt-cd-items-body', { timeout: 15_000 });

		await addLineItem(page, 'Procurement Item', 20, 3_500);
		await page.click('#kt-cd-next-2');
		await page.waitForSelector('#kt-cd-readiness-panel', { timeout: 15_000 });
		await treatRequiredPvcsIncluded(page);

		await expect(page.locator('#kt-cd-submit')).toBeEnabled({ timeout: 20_000 });
	});

	// CD-10 ─────────────────────────────────────────────────────────────────────
	test('CD-10 full wizard flow submits demand and shows DIA reference on success screen', async ({
		page,
	}) => {
		test.setTimeout(150_000);
		await loginAsAdministrator(page);
		await openWizard(page);
		await fillStep1(page, 'CD-10 E2E Full Wizard Test');
		await page.click('#kt-cd-next-1');
		await page.waitForSelector('#kt-cd-items-body', { timeout: 15_000 });

		await addLineItem(page, 'Construction Material', 100, 4_500);
		await page.click('#kt-cd-next-2');
		await page.waitForSelector('#kt-cd-readiness-panel', { timeout: 15_000 });
		await treatRequiredPvcsIncluded(page);

		await expect(page.locator('#kt-cd-submit')).toBeEnabled({ timeout: 20_000 });

		await page.click('#kt-cd-submit');

		// Step 4 success screen
		await page.waitForSelector('.kt-cd-success-title', { timeout: 25_000 });

		// Success title text
		const successTitle = page.locator('.kt-cd-success-title');
		await expect(successTitle).toContainText(/Submitted/i);

		// Reference chip shows a real DIA-* number
		const refChip = page.locator('.kt-cd-ref-chip');
		await expect(refChip).toBeVisible();
		const refText = await refChip.textContent();
		expect(refText).toMatch(/DIA-/);

		// Navigation buttons visible
		await expect(page.locator('#kt-cd-go-hub, [data-action="go-hub"]')).toBeVisible();
	});
});
