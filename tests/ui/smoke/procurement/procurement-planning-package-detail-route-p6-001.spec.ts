/**
 * P6-001 — Package Detail route opens contextual package detail surface.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import { prepareWorkbenchSession, pp3Root } from '../../helpers/pp3Workbench';

const PKG_CODE = 'PKG-MOH-2026-001';
const PKG_TITLE = 'District Hospital Renovation Works';

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

async function tryLoginAsPlanner(page: import('@playwright/test').Page): Promise<boolean> {
	try {
		await loginAsProcurementPlanner(page);
		return true;
	} catch (e) {
		const msg = e instanceof Error ? e.message : String(e);
		if (msg.includes('Invalid Login')) {
			return false;
		}
		throw e;
	}
}

test.describe('P6-001 Package Detail route', () => {
	test.beforeAll(() => {
		seedPackageDraftReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('package detail route renders contextual surface without workbench chrome', async ({ page }) => {
		await page.goto(`${pp3Root}/desk/procurement-planning/packages/${PKG_CODE}`, {
			waitUntil: 'domcontentloaded',
		});

		await expect(page).toHaveURL(new RegExp(`/desk/procurement-planning/packages/${PKG_CODE}(?:\\?|$)`));
		await expect(page.getByTestId('pp3-package-detail')).toHaveCount(1, { timeout: 30000 });
		await expect(page.getByTestId('pp3-package-header')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-package-header')).toContainText(PKG_TITLE);
		await expect(page.getByTestId('pp3-back-to-workbench')).toBeVisible();
		await expect(page.getByTestId('pp2-page-title')).toHaveText('Package Detail', { timeout: 30000 });

		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toHaveCount(0);
		await expect(page.getByTestId('pp3-work-list')).toHaveCount(0);
		await expect(page.getByTestId('pp3-active-plan-banner')).toHaveCount(0);
		await expect(page.getByTestId('pp3-planning-workbench')).toHaveCount(0);

		await page.screenshot({ path: 'artifacts/p6-001-package-detail-route.png', fullPage: true });

		await page.getByTestId('pp3-back-to-workbench').click();
		await page.waitForURL(/\/desk\/procurement-planning(?:\?|$)/, { timeout: 30000 });
		await expect(page.getByTestId('pp3-active-plan-banner')).toBeVisible({ timeout: 30000 });
	});
});
