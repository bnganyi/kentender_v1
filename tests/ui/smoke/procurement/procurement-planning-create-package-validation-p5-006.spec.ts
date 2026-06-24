/**
 * P5-006 — Create Package validation blocks duplicate package and offers Open Package.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import { prepareWorkbenchSession, pp3Root } from '../../helpers/pp3Workbench';

const WORKS_DEMAND_TITLE = 'District Hospital Renovation Works';

const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');

function seedP5NeedsPlanningReady(): void {
	execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.seeds.seed_pp5_golden_path.ensure_pp5_needs_planning_ready ' +
			'--kwargs \'{"force_reset": True}\'',
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

async function includeDemandAndReachCreatePackageAction(
	page: import('@playwright/test').Page,
): Promise<void> {
	await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

	const worksRow = page
		.getByTestId('pp3-work-item-row')
		.filter({ has: page.getByTestId('pp3-work-item-title').filter({ hasText: WORKS_DEMAND_TITLE }) })
		.first();
	await expect(worksRow).toBeVisible({ timeout: 30000 });
	await worksRow.click();

	await page.getByTestId('pp3-primary-action').click();
	await expect(page.getByTestId('pp2-include-plan-modal')).toBeVisible({ timeout: 30000 });
	await page.getByTestId('pp2-confirm-include-plan').click();
	await expect(page.getByTestId('pp2-include-plan-success')).toBeVisible({ timeout: 30000 });
}

async function reachDuplicatePackageBlocker(page: import('@playwright/test').Page): Promise<void> {
	await page.getByTestId('pp2-create-package-next-action').click();

	const duplicateDialog = page.getByTestId('pp2-create-package-duplicate-dialog');
	const createModal = page.getByTestId('pp2-create-package-modal');

	const duplicateAlreadyVisible = await duplicateDialog
		.waitFor({ state: 'visible', timeout: 15000 })
		.then(() => true)
		.catch(() => false);

	if (duplicateAlreadyVisible) {
		return;
	}

	await expect(createModal).toBeVisible({ timeout: 15000 });
	await page.getByTestId('pp2-confirm-create-package').click();
	await expect(createModal).toHaveCount(0, { timeout: 30000 });
	await page.getByTestId('pp2-create-package-next-action').click();
	await expect(duplicateDialog).toBeVisible({ timeout: 30000 });
}

test.describe('P5-006 Create Package validation (golden path)', () => {
	test.beforeAll(() => {
		seedP5NeedsPlanningReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('duplicate package shows blocker with Open Package action', async ({ page }) => {
		await includeDemandAndReachCreatePackageAction(page);
		await reachDuplicatePackageBlocker(page);

		const duplicateDialog = page.getByTestId('pp2-create-package-duplicate-dialog');
		await expect(duplicateDialog).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-create-package-blocker-message')).toContainText(
			'already exists'
		);
		await expect(page.getByTestId('pp2-create-package-existing-package-name')).not.toBeEmpty();
		await expect(page.getByTestId('pp2-create-package-modal')).toHaveCount(0);
		await expect(page.getByTestId('pp2-open-existing-package')).toBeVisible();

		const dialogText = await duplicateDialog.innerText();
		expect(dialogText).not.toMatch(/PKG-MOH-/i);
		expect(dialogText).not.toMatch(/PLANINCL-/i);

		await page.screenshot({ path: 'artifacts/p5-006-create-package-duplicate-blocker.png', fullPage: true });
	});
});
