/**
 * P6-002 — Package Detail header shows title, method, value, active plan, state, funding, blockers, next action.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import { prepareWorkbenchSession, pp3Root } from '../../helpers/pp3Workbench';

const PKG_CODE = 'PKG-MOH-2026-001';
const PKG_TITLE = 'District Hospital Renovation Works';
const PLAN_LABEL = 'Ministry of Health Procurement Plan FY 2026/2027';

const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');

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

test.describe('P6-002 Package Detail header', () => {
	test.beforeAll(() => {
		seedPackageDraftReady();
	});

	test.beforeEach(async ({ page }) => {
		await loginAsProcurementPlanner(page);
		await prepareWorkbenchSession(page);
	});

	test('header shows business context fields', async ({ page }) => {
		await page.goto(`${pp3Root}/desk/procurement-planning/packages/${PKG_CODE}`, {
			waitUntil: 'domcontentloaded',
		});

		const header = page.getByTestId('pp3-package-header');
		await expect(header).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-package-title')).toContainText(PKG_TITLE);
		await expect(page.getByTestId('pp3-package-meta')).toContainText('Open Tender');
		await expect(page.getByTestId('pp3-package-active-plan')).toContainText(PLAN_LABEL);
		await expect(page.getByTestId('pp3-package-status')).toContainText('Draft Package');
		await expect(page.getByTestId('pp3-package-funding')).toContainText('Budget linked');
		await expect(page.getByTestId('pp3-package-blockers')).toContainText('None');
		await expect(page.getByTestId('pp3-package-next-action')).toBeVisible();

		await page.screenshot({ path: 'artifacts/p6-002-package-detail-header.png', fullPage: true });
	});
});
