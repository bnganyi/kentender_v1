/**
 * P5-007 — Create Package success offers Open Package (Workbench golden path).
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import { prepareWorkbenchSession, pp3Root } from '../../helpers/pp3Workbench';

const WORKS_DEMAND_TITLE = 'District Hospital Renovation Works';

const FORBIDDEN_LEAKAGE = [/PKG-MOH-/i, /PLANINCL-/i, /source_object_code/i, /target_object_code/i];

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

async function createPackageFromGoldenPath(page: import('@playwright/test').Page): Promise<void> {
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

	await page.getByTestId('pp2-create-package-next-action').click();
	await expect(page.getByTestId('pp2-create-package-modal')).toBeVisible({ timeout: 30000 });
	await page.getByTestId('pp2-confirm-create-package').click();
	await expect(page.getByTestId('pp2-create-package-success')).toBeVisible({ timeout: 30000 });
}

test.describe('P5-007 Create Package success (golden path)', () => {
	test.beforeAll(() => {
		seedP5NeedsPlanningReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('success summary offers Open Package after create', async ({ page }) => {
		await createPackageFromGoldenPath(page);

		const success = page.getByTestId('pp2-create-package-success');
		await expect(success).toBeVisible({ timeout: 30000 });
		await expect(success).toContainText('Package created.');
		await expect(success).toContainText('Complete readiness and submit for review.');
		await expect(page.getByTestId('pp2-open-package-next-action')).toBeVisible();
		await expect(page.getByTestId('pp3-back-to-workbench')).toBeVisible();

		const successText = await success.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(successText).not.toMatch(pattern);
		}

		await page.getByTestId('pp2-open-package-next-action').click();
		await page.waitForURL(/queue=draft-packages/, { timeout: 30000 });
		expect(page.url()).toMatch(/package_code=/);

		await page.screenshot({ path: 'artifacts/p5-007-create-package-success.png', fullPage: true });
	});
});
