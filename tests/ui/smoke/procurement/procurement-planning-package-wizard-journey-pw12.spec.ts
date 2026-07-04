/**
 * PW12 — Package Creation Wizard end-to-end journey (Planning Workbench v4).
 *
 * Exercises the real "In Creation" placeholder-row entry point wired in
 * PW7-PW11 (pp2_planning_router.js -> PlanningPackageWizard) against the
 * canonical WORKS master seed at the INCLUDED_IN_PLAN checkpoint:
 *   Step 1 (Select Demands) -> Step 2 (Configure Package) -> Step 3
 *   (Review and Create), asserting the readiness checklist renders live
 *   backend data and gates the "Create Package" button on funding
 *   readiness exactly as the wizard spec requires.
 *
 * The canonical seed's budget line intentionally has less "available"
 * headroom than the demand's own reserved amount (amount_allocated
 * 120M, amount_reserved 98.2M -> amount_available ~21.8M), so the
 * funding readiness check is expected to report "Blocked" and disable
 * Create — this is a real backend business rule (kentender_budget
 * check_available_budget), not a wizard defect, and is asserted here to
 * lock in the negative/blocked path. The happy-path create orchestration
 * itself is covered by the PW5/PW6 backend integration test suites
 * (test_pw5_wizard_readiness.py::test_fully_eligible_demand_allows_create,
 * test_pw6_wizard_create_orchestration.py), which use fixtures with
 * sufficient available funds.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';

const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');
const PLAN_CODE = 'PLAN-MOH-2026';
const WORKS_DEMAND_TITLE = 'District Hospital Renovation Works';

function resetWorksMasterSeedIncludedInPlan(): void {
	execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master ' +
			'--kwargs \'{"checkpoint": "INCLUDED_IN_PLAN", "force_reset": True}\'',
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

test.describe('PW12 Package Creation Wizard journey (In Creation placeholder entry point)', () => {
	test.beforeAll(() => {
		resetWorksMasterSeedIncludedInPlan();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
	});

	test('opens from the In Creation placeholder row and walks Steps 1-3 with live data', async ({ page }) => {
		await page.goto(`/desk/procurement-planning?plan=${PLAN_CODE}&queue=draft_packages`, {
			waitUntil: 'domcontentloaded',
		});

		const workbenchFrame = page.frameLocator('[data-testid="pp4-workbench-design-iframe"]');
		const placeholderRow = workbenchFrame.locator('tr[data-inclusion-code]').first();
		await expect(placeholderRow).toBeVisible({ timeout: 30000 });
		await expect(placeholderRow).toContainText(WORKS_DEMAND_TITLE);
		await placeholderRow.click();

		// Step 1 — Select Demands: pre-selected inclusion, compatibility computed live.
		const step1 = page.locator('[data-testid="pp2-package-wizard-step1"]');
		await expect(step1).toBeVisible({ timeout: 30000 });
		await expect(step1.getByRole('heading', { name: /Step 1 of 3: Select Demands/ })).toBeVisible();
		const demandCheckbox = step1.locator('[data-testid="pp2-wizard-demand-checkbox"]').first();
		await expect(demandCheckbox).toBeChecked();
		await expect(step1.locator('[data-testid="pp2-wizard-compatible"]')).toBeVisible({ timeout: 15000 });

		await step1.getByRole('button', { name: 'Next' }).click();

		// Step 2 — Configure Package: defaults populated from the demand/session user.
		const step2 = page.locator('[data-testid="pp2-package-wizard-step2"]');
		await expect(step2).toBeVisible({ timeout: 30000 });
		await expect(step2.getByRole('heading', { name: /Step 2 of 3: Configure Package/ })).toBeVisible();
		await expect(step2.locator('[data-testid="pp2-wizard-lines-table"]')).toBeVisible({ timeout: 15000 });
		await expect(step2.locator('[data-testid="pp2-wizard-funding-summary"]')).toBeVisible();
		await expect(step2.locator('[data-testid="pp2-wizard-doc-path-summary"]')).toBeVisible();

		await step2.getByRole('button', { name: 'Next' }).click();

		// Step 3 — Review and Create: readiness checklist reflects real backend
		// funding evaluation and gates the Create action.
		const step3 = page.locator('[data-testid="pp2-package-wizard-step3"]');
		await expect(step3).toBeVisible({ timeout: 30000 });
		await expect(step3.getByRole('heading', { name: /Step 3 of 3: Review and Create/ })).toBeVisible();

		const readinessRows = step3.locator('[data-testid="pp2-wizard-readiness-row"]');
		await expect(readinessRows.first()).toBeVisible({ timeout: 15000 });
		const fundingRow = readinessRows.filter({ hasText: 'Funding linked / reserved' });
		await expect(fundingRow).toHaveAttribute('data-status', 'Blocked', { timeout: 15000 });

		const createButton = step3.getByRole('button', { name: 'Create Package' });
		await expect(createButton).toBeDisabled();

		await page.screenshot({ path: 'artifacts/pw12-package-wizard-step3-blocked.png', fullPage: true });

		// Close without creating — journey validation only, seed stays clean
		// for other specs relying on the INCLUDED_IN_PLAN checkpoint.
		await step3.getByRole('button', { name: 'Back' }).click();
		await expect(step2).toBeVisible({ timeout: 15000 });
	});
});
