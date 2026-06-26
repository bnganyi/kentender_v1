/**
 * P5-002 — Workbench Include in Plan opens active-plan modal (golden path, live data).
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

test.describe('P5-002 Include in Plan action (golden path)', () => {
	test.beforeAll(() => {
		seedP5NeedsPlanningReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('Include in Plan on selected WORKS demand opens include modal', async ({ page }) => {
		await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		const worksRow = page
			.getByTestId('pp3-work-item-row')
			.filter({ has: page.getByTestId('pp3-work-item-title').filter({ hasText: WORKS_DEMAND_TITLE }) })
			.first();
		await expect(worksRow).toBeVisible({ timeout: 30000 });
		await worksRow.click();

		const includeButton = page.getByTestId('pp3-primary-action');
		await expect(includeButton).toBeVisible();
		await expect(includeButton).toHaveText('Add to Active Plan');
		await includeButton.click();

		const modal = page.getByTestId('pp2-include-plan-modal');
		await expect(modal).toBeVisible({ timeout: 30000 });
		await expect(modal).toContainText(WORKS_DEMAND_TITLE);
		await expect(page.getByTestId('pp2-confirm-include-plan')).toBeVisible();

		await page.screenshot({ path: 'artifacts/p5-002-include-in-plan-modal-open.png', fullPage: true });
	});
});
