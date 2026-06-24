/**
 * P5-008 — Workbench state update after package creation (golden path).
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

	const createModal = page.getByTestId('pp2-create-package-modal');
	const duplicateDialog = page.getByTestId('pp2-create-package-duplicate-dialog');

	const openedCreateModal = await createModal
		.waitFor({ state: 'visible', timeout: 15000 })
		.then(() => true)
		.catch(() => false);

	if (openedCreateModal) {
		await page.getByTestId('pp2-confirm-create-package').click();
		await expect(page.getByTestId('pp2-create-package-success')).toBeVisible({ timeout: 30000 });
		return;
	}

	await expect(duplicateDialog).toBeVisible({ timeout: 15000 });
	await page.getByTestId('pp2-open-existing-package').click();
	await page.waitForURL(/queue=draft-packages/, { timeout: 30000 });
}

test.describe('P5-008 Workbench state update (golden path)', () => {
	test.beforeAll(() => {
		seedP5NeedsPlanningReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('package moves to Draft Packages and leaves Needs Planning', async ({ page }) => {
		await createPackageFromGoldenPath(page);

		const onSuccessPanel = await page
			.getByTestId('pp2-create-package-success')
			.isVisible()
			.catch(() => false);
		if (onSuccessPanel) {
			await page.getByTestId('pp3-back-to-workbench').click();
			await page.waitForURL(/queue=draft-packages/, { timeout: 30000 });
		}

		const draftTab = page.getByTestId('pp3-queue-draft-packages');
		await expect(draftTab).toHaveClass(/is-active/, { timeout: 30000 });

		const packageRow = page
			.getByTestId('pp3-work-item-row')
			.filter({ has: page.getByTestId('pp3-work-item-title').filter({ hasText: WORKS_DEMAND_TITLE }) })
			.first();
		await expect(packageRow).toBeVisible({ timeout: 30000 });
		await expect(packageRow.getByTestId('pp3-work-item-state')).toContainText('Draft');
		await expect(packageRow.getByTestId('pp3-work-item-next-action')).toHaveText(/Open Package|Complete Package/);

		await page.getByTestId('pp3-queue-needs-planning').click();
		await expect(page.getByTestId('pp3-queue-needs-planning')).toHaveClass(/is-active/);
		const needsPlanningWorks = page
			.getByTestId('pp3-work-item-row')
			.filter({ has: page.getByTestId('pp3-work-item-title').filter({ hasText: WORKS_DEMAND_TITLE }) });
		await expect(needsPlanningWorks).toHaveCount(0, { timeout: 30000 });

		await page.screenshot({ path: 'artifacts/p5-008-workbench-state-update.png', fullPage: true });
	});
});
