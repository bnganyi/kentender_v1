/**
 * P7-001 — Released to Tender route opens dedicated follow-up list.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import { pp3Root } from '../../helpers/pp3Workbench';

const PKG_CODE = 'PKG-MOH-2026-001';
const PKG_TITLE = 'District Hospital Renovation Works';

const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');

function seedReleasedToTender(): void {
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

test.describe('P7-001 Released to Tender route', () => {
	test.beforeAll(() => {
		seedReleasedToTender();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
	});

	test('releases route renders follow-up list without workbench chrome', async ({ page }) => {
		await page.goto(`${pp3Root}/desk/procurement-planning/releases`, {
			waitUntil: 'domcontentloaded',
		});

		await expect(page).toHaveURL(/\/desk\/procurement-planning\/releases(?:\?|$)/);
		await expect(page.getByTestId('pp3-released-to-tender-page')).toHaveCount(1, {
			timeout: 30000,
		});
		await expect(page.getByTestId('pp2-page-title')).toHaveText('Released to Tender', {
			timeout: 30000,
		});
		await expect(page.getByTestId('pp3-released-list')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-released-search')).toBeVisible();
		await expect(page.getByTestId('pp3-release-summary')).toBeVisible();

		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toHaveCount(0);
		await expect(page.getByTestId('pp3-work-list')).toHaveCount(0);
		await expect(page.getByTestId('pp3-active-plan-banner')).toHaveCount(0);
		await expect(page.getByTestId('pp3-planning-workbench')).toHaveCount(0);

		await expect(page.getByTestId('pp3-released-row').filter({ hasText: PKG_TITLE })).toBeVisible({
			timeout: 30000,
		});
		await expect(page.getByTestId('pp3-released-row').filter({ hasText: PKG_TITLE })).toContainText(
			PKG_TITLE,
		);

		await page.screenshot({ path: 'artifacts/p7-001-released-to-tender-route.png', fullPage: true });
	});
});
