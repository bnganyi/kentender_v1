/**
 * P7-002..P7-010 — Released to Tender follow-up and evidence drawer.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsAdministrator, loginAsProcurementPlanner } from '../../helpers/auth';
import { pp3Root } from '../../helpers/pp3Workbench';

const PKG_CODE = 'PKG-MOH-2026-001';
const PKG_TITLE = 'District Hospital Renovation Works';
const TENDER_CODE = 'TND-MOH-2026-001';

const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');

const FORBIDDEN_LEAKAGE = [
	/PLANINCL-/i,
	/PKGREL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/technical_refs_json/i,
];

test.describe.configure({ mode: 'serial' });

function seedConsumedByTender(): void {
	execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master ' +
			'--kwargs \'{"checkpoint": "CONSUMED_BY_TENDER", "force_reset": True}\'',
		{
			cwd: BENCH_ROOT,
			stdio: 'pipe',
			encoding: 'utf8',
		},
	);
}

async function gotoReleasedSurface(page: import('@playwright/test').Page): Promise<void> {
	await page.goto(`${pp3Root}/desk/procurement-planning/releases`, {
		waitUntil: 'domcontentloaded',
	});
	await expect(page.getByTestId('pp3-released-to-tender-page')).toHaveCount(1, { timeout: 30000 });
	await expect(masterReleasedRow(page)).toBeVisible({ timeout: 30000 });
}

function masterReleasedRow(page: import('@playwright/test').Page) {
	return page.getByTestId('pp3-released-row').filter({ hasText: PKG_TITLE });
}

test.beforeAll(() => {
	seedConsumedByTender();
});

test.describe('P7-002 Released list', () => {

	test.beforeEach(async ({ page }) => {
		await loginAsProcurementPlanner(page);
	});

	test('shows released package with tender-created status', async ({ page }) => {
		await gotoReleasedSurface(page);
		const row = masterReleasedRow(page);
		await expect(row).toContainText(PKG_TITLE);
		await expect(row.getByTestId('pp3-released-row-status')).toHaveText('Released · Tender created');
		await page.screenshot({ path: 'artifacts/p7-002-released-list-tender-created.png', fullPage: true });
	});
});

test.describe('P7-003 Release summary', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsProcurementPlanner(page);
	});

	test('shows tender, status, next action, and action buttons', async ({ page }) => {
		await gotoReleasedSurface(page);
		await masterReleasedRow(page).click();
		const summary = page.getByTestId('pp3-release-summary');
		await expect(summary).toBeVisible({ timeout: 30000 });
		await expect(summary.getByTestId('pp3-release-summary-headline')).toContainText(
			'Released to Tender Management',
		);
		await expect(summary.getByTestId('pp3-release-summary-tender')).toContainText(TENDER_CODE);
		await expect(summary.getByTestId('pp3-release-summary-status')).toContainText('Tender created');
		await expect(summary.getByTestId('pp3-release-summary-next-action')).toContainText('Continue in Tender');
		await expect(page.getByTestId('pp3-open-tender-button')).toBeVisible();
		await expect(page.getByTestId('pp3-open-package-button')).toBeVisible();
		await expect(page.getByTestId('pp3-view-release-evidence')).toBeVisible();
		await page.screenshot({ path: 'artifacts/p7-003-release-summary.png', fullPage: true });
	});
});

test.describe('P7-004 Open Tender', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsProcurementPlanner(page);
	});

	test('Open Tender navigates to Tender Management', async ({ page }) => {
		await gotoReleasedSurface(page);
		await expect(page.getByTestId('pp3-open-tender-button')).toBeVisible({ timeout: 30000 });
		await page.getByTestId('pp3-open-tender-button').click();
		await expect(page).toHaveURL(/\/desk\/.*tm2-tender/i, { timeout: 30000 });
	});
});

test.describe('P7-005 Evidence drawer on request', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsProcurementPlanner(page);
	});

	test('drawer stays closed until View Evidence is clicked', async ({ page }) => {
		await gotoReleasedSurface(page);
		await expect(page.getByTestId('pp3-evidence-drawer')).toHaveCount(0);
		await page.getByTestId('pp3-view-release-evidence').click();
		await expect(page.getByTestId('pp3-evidence-drawer')).toBeVisible({ timeout: 30000 });
	});
});

test.describe('P7-006 Evidence timeline', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('shows business timeline events', async ({ page }) => {
		await gotoReleasedSurface(page);
		await page.getByTestId('pp3-view-release-evidence').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await expect(drawer.getByTestId('pp3-evidence-timeline')).toContainText('Demand entered planning queue', {
			timeout: 30000,
		});
		await page.screenshot({ path: 'artifacts/p7-006-evidence-timeline.png', fullPage: true });
	});
});

test.describe('P7-007 Evidence records', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('shows business-labeled evidence records', async ({ page }) => {
		await gotoReleasedSurface(page);
		await page.getByTestId('pp3-view-release-evidence').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await expect(drawer.getByTestId('pp3-evidence-record-list')).toContainText(
			'Demand Approval Certificate',
			{ timeout: 30000 },
		);
		await expect(drawer.getByTestId('pp3-evidence-record-list')).toContainText('Procurement Package');
		const drawerText = await drawer.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(drawerText).not.toMatch(pattern);
		}
		await page.screenshot({ path: 'artifacts/p7-007-evidence-records.png', fullPage: true });
	});
});

test.describe('P7-008 Technical Details collapsed', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('technical panel is collapsed by default', async ({ page }) => {
		await gotoReleasedSurface(page);
		await page.getByTestId('pp3-view-release-evidence').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await expect(drawer.getByTestId('pp3-technical-details-toggle')).toBeVisible({ timeout: 30000 });
		await expect(drawer.getByTestId('pp3-technical-details-panel')).toBeHidden();
	});
});

test.describe('P7-009 Technical Details permission', () => {
	test('authorized user can expand technical details', async ({ page }) => {
		await loginAsAdministrator(page);
		await gotoReleasedSurface(page);
		await page.getByTestId('pp3-view-release-evidence').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await drawer.getByTestId('pp3-technical-details-toggle').click();
		await expect(drawer.getByTestId('pp3-technical-details-panel')).toBeVisible({ timeout: 30000 });
		await expect(drawer.getByTestId('pp3-technical-details-code').first()).toBeVisible();
	});

	test('unauthorized planner cannot expand technical details', async ({ page }) => {
		await loginAsProcurementPlanner(page);
		await gotoReleasedSurface(page);
		await page.getByTestId('pp3-view-release-evidence').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await expect(drawer.getByTestId('pp3-evidence-timeline')).toBeVisible({ timeout: 30000 });
		await expect(drawer.getByTestId('pp3-technical-details-toggle')).toHaveCount(0);
	});
});

test.describe('P7-010 Supplier denied', () => {
	const SUPPLIER_EMAIL = 'supplier.p7-010@moh.test';
	const SUPPLIER_PASSWORD = 'test';

	test.beforeAll(() => {
		execSync(
			'bench --site kentender.midas.com execute ' +
				'kentender_procurement.procurement_planning.tests.pp3_ui_suppliers.ensure_p7_010_supplier_user',
			{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
		);
	});

	test('supplier cannot load released packages list', async ({ page }) => {
		await page.goto(`${pp3Root}/login`);
		await page.fill('#login_email', SUPPLIER_EMAIL);
		await page.fill('#login_password', SUPPLIER_PASSWORD);
		await page.click('button[type="submit"]');
		await page.waitForURL(/\/(desk|portal)(\/|$)/, { timeout: 30000 });
		await page.goto(`${pp3Root}/desk/procurement-planning/releases`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByRole('heading', { name: 'Not Permitted' })).toBeVisible({ timeout: 30000 });
		await expect(page.locator('body')).toContainText(/not permitted/i);
		await expect(page.getByTestId('pp3-released-to-tender-page')).toHaveCount(0);
		await expect(page.getByTestId('pp3-evidence-drawer')).toHaveCount(0);
	});
});
