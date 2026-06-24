/**
 * P5-009 — Golden-path ordinary flow hides PLANINCL / source-target technical labels.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';
import {
	assertNoOrdinaryFlowLeakage,
	P5_ORDINARY_FLOW_FORBIDDEN_LEAKAGE,
} from '../../helpers/procurementPlanningLeakage';
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

async function collectOrdinaryFlowText(page: import('@playwright/test').Page): Promise<string> {
	const chunks: string[] = [];
	const selectors = [
		'pp3-active-plan-banner',
		'pp3-workbench-queue-tabs',
		'pp3-work-list',
		'pp3-selected-work-summary',
		'pp2-include-plan-modal',
		'pp2-include-plan-success',
		'pp2-create-package-modal',
		'pp2-create-package-success',
		'pp2-create-package-duplicate-dialog',
	];
	for (const testId of selectors) {
		const node = page.getByTestId(testId);
		if (await node.isVisible().catch(() => false)) {
			chunks.push(await node.innerText());
		}
	}
	const dialog = page.locator('.modal-dialog:visible').first();
	if (await dialog.isVisible().catch(() => false)) {
		chunks.push(await dialog.innerText());
	}
	return chunks.join('\n');
}

function scanOrdinaryFlowText(text: string, step: string): void {
	try {
		assertNoOrdinaryFlowLeakage(text, step);
	} catch (error) {
		const message = error instanceof Error ? error.message : String(error);
		expect(message, step).toBe('');
	}
}

test.describe('P5-009 No technical leakage (golden path ordinary flow)', () => {
	test.beforeAll(() => {
		seedP5NeedsPlanningReady();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
		await prepareWorkbenchSession(page);
	});

	test('Needs Planning → Include → Create Package surfaces stay business-safe', async ({ page }) => {
		await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-active-plan-banner')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-work-list')).toBeVisible({ timeout: 30000 });

		scanOrdinaryFlowText(await collectOrdinaryFlowText(page), 'initial workbench');

		const worksRow = page
			.getByTestId('pp3-work-item-row')
			.filter({ has: page.getByTestId('pp3-work-item-title').filter({ hasText: WORKS_DEMAND_TITLE }) })
			.first();
		await expect(worksRow).toBeVisible({ timeout: 30000 });
		await worksRow.click();
		scanOrdinaryFlowText(await collectOrdinaryFlowText(page), 'selected demand summary');

		await page.getByTestId('pp3-primary-action').click();
		await expect(page.getByTestId('pp2-include-plan-modal')).toBeVisible({ timeout: 30000 });
		scanOrdinaryFlowText(await collectOrdinaryFlowText(page), 'include in plan modal');

		await page.getByTestId('pp2-confirm-include-plan').click();
		await expect(page.getByTestId('pp2-include-plan-success')).toBeVisible({ timeout: 30000 });
		scanOrdinaryFlowText(await collectOrdinaryFlowText(page), 'include in plan success');

		await page.getByTestId('pp2-create-package-next-action').click();

		const createModal = page.getByTestId('pp2-create-package-modal');
		const duplicateDialog = page.getByTestId('pp2-create-package-duplicate-dialog');
		const openedCreateModal = await createModal
			.waitFor({ state: 'visible', timeout: 15000 })
			.then(() => true)
			.catch(() => false);

		if (openedCreateModal) {
			scanOrdinaryFlowText(await collectOrdinaryFlowText(page), 'create package modal');
			await page.getByTestId('pp2-confirm-create-package').click();
			await expect(page.getByTestId('pp2-create-package-success')).toBeVisible({ timeout: 30000 });
			scanOrdinaryFlowText(await collectOrdinaryFlowText(page), 'create package success');
			await page.getByTestId('pp3-back-to-workbench').click();
			await page.waitForURL(/queue=draft-packages/, { timeout: 30000 });
		} else {
			await expect(duplicateDialog).toBeVisible({ timeout: 15000 });
			scanOrdinaryFlowText(await collectOrdinaryFlowText(page), 'duplicate package dialog');
			await page.getByTestId('pp2-open-existing-package').click();
			await page.waitForURL(/queue=draft-packages/, { timeout: 30000 });
		}

		await expect(page.getByTestId('pp3-queue-draft-packages')).toHaveClass(/is-active/, { timeout: 30000 });
		scanOrdinaryFlowText(await collectOrdinaryFlowText(page), 'draft packages queue');

		const visibleText = await collectOrdinaryFlowText(page);
		for (const pattern of P5_ORDINARY_FLOW_FORBIDDEN_LEAKAGE) {
			expect(visibleText, `draft packages queue must not match ${pattern}`).not.toMatch(pattern);
		}

		await page.screenshot({ path: 'artifacts/p5-009-no-technical-leakage.png', fullPage: true });
	});
});
