/**
 * P5-005 — Create Package modal shows business context (Workbench golden path).
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
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
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

async function openCreatePackageModalFromGoldenPath(page: import('@playwright/test').Page): Promise<void> {
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
}

test.describe('P5-005 Create Package modal (golden path)', () => {
	test.beforeAll(() => {
		seedP5NeedsPlanningReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('modal shows demand, plan, category, method, value, funding, package title', async ({ page }) => {
		await openCreatePackageModalFromGoldenPath(page);

		const modal = page.getByTestId('pp2-create-package-modal');
		await expect(modal).toBeVisible({ timeout: 30000 });
		await expect(page.getByRole('dialog')).toContainText('Create Package');

		await expect(page.getByTestId('pp2-create-package-demand')).toContainText(WORKS_DEMAND_TITLE);
		await expect(page.getByTestId('pp2-create-package-active-plan')).toContainText(ACTIVE_PLAN_TITLE);
		await expect(page.getByTestId('pp2-create-package-category')).toContainText('Works');
		await expect(page.getByTestId('pp2-create-package-method')).toContainText('Open Tender');
		await expect(page.getByTestId('pp2-create-package-value')).toContainText('98,000,000');
		await expect(page.getByTestId('pp2-create-package-value')).toContainText('KES');
		await expect(page.getByTestId('pp2-create-package-funding')).toContainText('Budget linked');
		await expect(page.getByTestId('pp2-create-package-title-input')).toHaveValue(WORKS_DEMAND_TITLE);
		await expect(page.getByTestId('pp2-confirm-create-package')).toBeVisible();

		const modalText = await modal.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(modalText).not.toMatch(pattern);
		}

		await page.screenshot({ path: 'artifacts/p5-005-create-package-modal.png', fullPage: true });
	});
});
