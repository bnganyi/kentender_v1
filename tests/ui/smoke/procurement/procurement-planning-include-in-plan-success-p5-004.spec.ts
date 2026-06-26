/**
 * P5-004 — Include in Plan success offers Create Package (Workbench golden path).
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import { prepareWorkbenchSession, pp3Root } from '../../helpers/pp3Workbench';

const WORKS_DEMAND_TITLE = 'District Hospital Renovation Works';

const FORBIDDEN_LEAKAGE = [/PLANINCL-/i, /source_object_code/i, /target_object_code/i];

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

test.describe('P5-004 Include in Plan success (golden path)', () => {
	test.beforeAll(() => {
		seedP5NeedsPlanningReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('success summary offers Create Package after include', async ({ page }) => {
		await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		const worksRow = page
			.getByTestId('pp3-work-item-row')
			.filter({ has: page.getByTestId('pp3-work-item-title').filter({ hasText: WORKS_DEMAND_TITLE }) })
			.first();
		await expect(worksRow).toBeVisible({ timeout: 30000 });
		await worksRow.click();

		await page.getByTestId('pp3-primary-action').click();
		const modal = page.getByTestId('pp2-include-plan-modal');
		await expect(modal).toBeVisible({ timeout: 30000 });
		await page.getByTestId('pp2-confirm-include-plan').click();

		const success = page.getByTestId('pp2-include-plan-success');
		await expect(success).toBeVisible({ timeout: 30000 });
		await expect(success).toContainText('Added to active plan');
		await expect(success).toContainText('This demand has been added to:');
		await expect(success).toContainText('Create a procurement package for this demand.');
		await expect(page.getByTestId('pp2-create-package-next-action')).toBeVisible();
		await expect(page.getByTestId('pp3-view-demand-button')).toBeVisible();
		await expect(page.getByTestId('pp3-view-evidence-button')).toBeVisible();

		const worksRowAfter = page
			.getByTestId('pp3-work-item-row')
			.filter({ has: page.getByTestId('pp3-work-item-title').filter({ hasText: WORKS_DEMAND_TITLE }) });
		await expect(worksRowAfter).toHaveCount(0, { timeout: 30000 });

		const successText = await success.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(successText).not.toMatch(pattern);
		}

		await page.screenshot({ path: 'artifacts/p5-004-include-in-plan-success.png', fullPage: true });
	});
});
