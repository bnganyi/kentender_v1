/**
 * P5-003 — Include in Plan modal shows demand, value, funding, active plan; no technical IDs.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import { prepareWorkbenchSession, pp3Root } from '../../helpers/pp3Workbench';

const WORKS_DEMAND_TITLE = 'District Hospital Renovation Works';
const ACTIVE_PLAN_TITLE = 'Ministry of Health Procurement Plan FY 2026/2027';

const FORBIDDEN_LEAKAGE = [
	/DEM-MOH-2026-001/i,
	/DEMITEM-MOH-/i,
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/technical_refs_json/i,
	/locked_summary_json/i,
];

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

test.describe('P5-003 Include in Plan modal content (golden path)', () => {
	test.beforeAll(() => {
		seedP5NeedsPlanningReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('modal shows business context without technical leakage', async ({ page }) => {
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

		await expect(page.getByTestId('pp2-include-plan-demand')).toContainText(WORKS_DEMAND_TITLE);
		await expect(page.getByTestId('pp2-include-plan-value')).toContainText('98,000,000');
		await expect(page.getByTestId('pp2-include-plan-value')).toContainText('KES');
		await expect(page.getByTestId('pp2-include-plan-funding')).toContainText('Budget linked');
		await expect(page.getByTestId('pp2-include-plan-active-plan')).toContainText(ACTIVE_PLAN_TITLE);

		await expect(page.getByTestId('pp2-target-plan-select')).toHaveCount(0);
		await expect(page.getByRole('dialog')).toContainText('Add to Active Plan');
		await expect(page.getByTestId('pp2-confirm-include-plan')).toBeVisible();

		const modalText = await modal.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(modalText).not.toMatch(pattern);
		}

		await page.screenshot({ path: 'artifacts/p5-003-include-in-plan-modal-content.png', fullPage: true });
	});
});
