/**
 * P6-003 — P6-014 Package Detail tabs and context preservation.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import { assertNoOrdinaryFlowLeakage } from '../../helpers/procurementPlanningLeakage';
import { prepareWorkbenchSession, pp3Root } from '../../helpers/pp3Workbench';

const PKG_CODE = 'PKG-MOH-2026-001';

const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');

const TAB_SPECS = [
	{ testId: 'pp3-package-overview-tab', panel: 'pp3-package-overview-panel', label: 'Overview' },
	{
		testId: 'pp3-package-lines-funding-tab',
		panel: 'pp3-package-lines-funding-panel',
		label: 'Lines & Funding',
	},
	{ testId: 'pp3-package-readiness-tab', panel: 'pp3-package-readiness-panel', label: 'Readiness' },
	{ testId: 'pp3-package-review-tab', panel: 'pp3-package-review-panel', label: 'Review' },
	{ testId: 'pp3-package-release-tab', panel: 'pp3-package-release-panel', label: 'Release' },
];

function seedPackageDraftReady(): void {
	execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master ' +
			'--kwargs \'{"checkpoint": "PACKAGE_DRAFT", "force_reset": True}\'',
		{
			cwd: BENCH_ROOT,
			stdio: 'pipe',
			encoding: 'utf8',
		},
	);
}

async function openPackageDetail(page: import('@playwright/test').Page): Promise<void> {
	await page.goto(`${pp3Root}/desk/procurement-planning/packages/${PKG_CODE}`, {
		waitUntil: 'domcontentloaded',
	});
	await expect(page.getByTestId('pp3-package-detail')).toHaveCount(1, { timeout: 30000 });
}

test.describe('P6-003 Package Detail tabs', () => {
	test.beforeAll(() => {
		seedPackageDraftReady();
	});

	test.beforeEach(async ({ page }) => {
		await loginAsProcurementPlanner(page);
		await prepareWorkbenchSession(page);
	});

	test('shows only wireframe tabs', async ({ page }) => {
		await openPackageDetail(page);
		await expect(page.getByTestId('pp3-package-tabs')).toBeVisible();
		for (const tab of TAB_SPECS) {
			await expect(page.getByTestId(tab.testId)).toHaveCount(1);
		}
	});

	test('P6-004/P6-005 no Evidence or Advanced default tabs', async ({ page }) => {
		await openPackageDetail(page);
		await expect(page.getByTestId('pp3-package-tabs')).toBeVisible();
		const tabsText = await page.getByTestId('pp3-package-tabs').innerText();
		for (const forbidden of ['Evidence', 'Advanced', 'Technical Details', 'Audit Trail', 'Handoff History']) {
			expect(tabsText).not.toContain(forbidden);
		}
	});

	test('P6-006 overview tab content', async ({ page }) => {
		await openPackageDetail(page);
		await expect(page.getByTestId('pp3-package-overview-panel')).toBeVisible();
		await expect(page.getByTestId('pp3-package-overview-source-demand')).toBeVisible();
		await page.screenshot({ path: 'artifacts/p6-006-package-detail-overview.png', fullPage: true });
	});

	test('P6-007 lines and funding tab', async ({ page }) => {
		await openPackageDetail(page);
		await page.getByTestId('pp3-package-lines-funding-tab').click();
		await expect(page.getByTestId('pp3-package-lines-funding-panel')).toBeVisible();
		await expect(page.getByTestId('pp3-package-lines-table')).toBeVisible();
		await page.screenshot({ path: 'artifacts/p6-007-package-detail-lines-funding.png', fullPage: true });
	});

	test('P6-008 readiness tab', async ({ page }) => {
		await openPackageDetail(page);
		await page.getByTestId('pp3-package-readiness-tab').click();
		await expect(page.getByTestId('pp3-package-readiness-panel')).toBeVisible();
		await expect(page.getByTestId('pp3-package-readiness-checks')).toBeVisible();
		await page.screenshot({ path: 'artifacts/p6-008-package-detail-readiness.png', fullPage: true });
	});

	test('P6-010 review tab', async ({ page }) => {
		await openPackageDetail(page);
		await page.getByTestId('pp3-package-review-tab').click();
		await expect(page.getByTestId('pp3-package-review-panel')).toBeVisible();
		await expect(page.getByTestId('pp3-package-review-status')).toContainText(/Not submitted|Needs review|Approved/);
	});

	test('P6-011 release tab before release', async ({ page }) => {
		await openPackageDetail(page);
		await page.getByTestId('pp3-package-release-tab').click();
		await expect(page.getByTestId('pp3-package-release-panel')).toBeVisible();
		await expect(page.getByTestId('pp3-package-release-protected')).toBeVisible();
		await expect(page.getByTestId('pp3-package-release-warning')).toBeVisible();
		const body = await page.getByTestId('pp3-package-detail').innerText();
		assertNoOrdinaryFlowLeakage(body, 'package detail release tab');
		await page.screenshot({ path: 'artifacts/p6-011-package-detail-release-before.png', fullPage: true });
	});

	test('P6-014 header persists across tab switches', async ({ page }) => {
		await openPackageDetail(page);
		await expect(page.getByTestId('pp3-package-header')).toBeVisible();
		for (const tab of TAB_SPECS.slice(1)) {
			await page.getByTestId(tab.testId).click();
			await expect(page.getByTestId('pp3-package-header')).toBeVisible();
			await expect(page.getByTestId(tab.panel)).toBeVisible();
		}
	});

	test('P6-015 no release technical card in default UI', async ({ page }) => {
		await openPackageDetail(page);
		await page.getByTestId('pp3-package-release-tab').click();
		await expect(page.getByTestId('pp3-package-release-panel')).toBeVisible();
		await expect(page.locator('[data-testid="pp2-planning-handoff-stack"]')).toHaveCount(0);
		const body = await page.getByTestId('pp3-package-detail').innerText();
		expect(body).not.toContain('PKGREL-MOH-2026-001');
		expect(body).not.toContain('Planning Release Package');
		assertNoOrdinaryFlowLeakage(body, 'package detail default surface');
	});
});
