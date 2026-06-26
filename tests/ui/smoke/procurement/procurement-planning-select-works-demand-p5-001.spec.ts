/**
 * P5-001 — Golden path: WORKS demand appears in Needs Planning (live data).
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import { prepareWorkbenchSession, pp3Root } from '../../helpers/pp3Workbench';

const WORKS_DEMAND_TITLE = 'District Hospital Renovation Works';

const FORBIDDEN_LEAKAGE = [
	/DEM-MOH-2026-001/i,
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/technical_refs_json/i,
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

test.describe('P5-001 Select WORKS demand (golden path)', () => {
	test.beforeAll(() => {
		seedP5NeedsPlanningReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('District Hospital Renovation Works appears and can be selected in Needs Planning', async ({
		page,
	}) => {
		await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp3-active-plan-banner')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-active-plan-banner')).toContainText('Active Procurement Plan');
		await expect(page.getByTestId('pp3-active-plan-banner')).toContainText('Ministry of Health Procurement Plan');
		await expect(page.getByTestId('pp3-active-plan-banner')).toContainText('2026/2027');

		const needsTab = page.getByTestId('pp3-queue-needs-planning');
		await expect(needsTab).toBeVisible({ timeout: 30000 });
		await expect(needsTab).toHaveClass(/is-active/);
		await expect(needsTab).toHaveAttribute('aria-selected', 'true');

		const workList = page.getByTestId('pp3-work-list');
		await expect(workList).toBeVisible();

		const worksRow = page
			.getByTestId('pp3-work-item-row')
			.filter({ has: page.getByTestId('pp3-work-item-title').filter({ hasText: WORKS_DEMAND_TITLE }) })
			.first();
		await expect(worksRow).toBeVisible({ timeout: 30000 });
		await expect(worksRow.getByTestId('pp3-work-item-title')).toHaveText(WORKS_DEMAND_TITLE);
		await expect(worksRow.getByTestId('pp3-work-item-state')).toHaveText('Planning pending');
		await expect(worksRow.getByTestId('pp3-work-item-next-action')).toHaveText('Add to active plan');
		await expect(worksRow).toContainText('Works');
		await expect(worksRow).toContainText('Budget linked');

		const rowText = await worksRow.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(rowText).not.toMatch(pattern);
		}

		await worksRow.click();
		await expect(worksRow).toHaveClass(/is-active/);

		const summary = page.getByTestId('pp3-selected-work-summary');
		await expect(summary).toBeVisible();
		await expect(summary).toContainText(WORKS_DEMAND_TITLE);
		await expect(page.getByTestId('pp3-primary-action')).toHaveText('Add to Active Plan');

		await page.screenshot({ path: 'artifacts/p5-001-select-works-demand.png', fullPage: true });
	});
});
