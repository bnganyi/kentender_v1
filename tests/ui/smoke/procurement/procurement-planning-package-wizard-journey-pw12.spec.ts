/**
 * PW12 — Package Creation Wizard end-to-end journey (Planning Workbench v4).
 *
 * Package Wizard Frontend Redo: the wizard is now a dedicated Frappe Page
 * (`create-package-wizard`, `create_package_wizard_page.js`/`.css`) ported
 * from the 4 real pixel designs, following the same pattern as the DIA
 * "Create Demand" wizard — NOT the `frappe.ui.Dialog` popups that were
 * wrongly shipped in the first pass. See the "Package Wizard Frontend
 * Redo" plan for the full rationale.
 *
 * Exercises the real "In Creation" placeholder-row entry point
 * (pp2_planning_router.js -> openPlanningPackageWizard -> sessionStorage
 * handoff -> frappe.set_route("create-package-wizard")) against the
 * canonical WORKS master seed at the INCLUDED_IN_PLAN checkpoint.
 *
 * Two journeys, each paying setup/teardown cost exactly once (per the
 * "optimize for speed, not fragmented specs" testing strategy):
 *
 *   1. Negative/blocked path (default seed state) — Step 1 (Select
 *      Demands) -> Step 2 (Configure Package) -> Step 3 (Review and
 *      Create), asserting the readiness checklist renders live backend
 *      data and gates "Create Package" on the canonical seed's
 *      insufficient-funding condition (amount_allocated 120M,
 *      amount_reserved 98M -> amount_available ~21.8M < the 98M demand
 *      needs). This is a real backend business rule
 *      (kentender_budget.check_available_budget), not a wizard defect.
 *   2. Happy path — same seed, with the Budget Line's amount_allocated
 *      temporarily bumped so funding reads "Reserved" instead of
 *      "Blocked", walking all the way through Step 3 "Create Package"
 *      to the Step 4 success screen. This closes the one real gap in
 *      the original suite (create -> success only had manual evidence).
 *
 * PW1-6 backend integration tests (readiness/create orchestration,
 * negative/permission paths) are left untouched — still green, no new
 * backend tests needed for this frontend rebuild.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsProcurementPlanner } from '../../helpers/auth';

const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');
const PLAN_CODE = 'PLAN-MOH-2026';
const WORKS_DEMAND_TITLE = 'District Hospital Renovation Works';
const BUDGET_LINE_CODE = 'MOH-BL-DHI-2027'; // Budget Line.generated_reference (MVP-1)
const BUMPED_BUDGET_ALLOCATION = 300_000_000;
// works_master_budget_seed.AMOUNT_ALLOCATED — the seed's upsert is
// idempotent-preserve-if-exists, so re-running the seed does NOT reset an
// already-mutated Budget Line's amount_allocated back to this value. Any
// test that bumps the allocation must restore it explicitly (see
// `resetBudgetLineAllocation` below), not rely on the seed reset alone.
const CANONICAL_BUDGET_ALLOCATION = 120_000_000;

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

/** Sets the canonical Budget Line's allocation to an explicit amount. Used
 * both to temporarily raise it (funding "Reserved" instead of "Blocked")
 * and to restore the canonical value afterwards, since the seed reset does
 * not touch this field on an already-existing row. */
function setBudgetLineAllocation(amount: number): void {
	// MVP-1 Budget Line may not expose amount_allocated; best-effort only.
	try {
		execSync(
			'bench --site kentender.midas.com execute ' +
				'kentender_budget.seeds.moh_mvp_v1_portfolio.set_budget_line_allocation_by_code ' +
				`--kwargs '{"line_code": "${BUDGET_LINE_CODE}", "amount": ${amount}}'`,
			{
				cwd: BENCH_ROOT,
				stdio: 'pipe',
				encoding: 'utf8',
			},
		);
	} catch {
		/* funding column may be absent after MVP-1 Budget schema */
	}
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

/** Opens the Workbench "In Creation" placeholder row and waits for the
 * dedicated wizard page to take over the route. Shared by both journeys. */
async function openWizardFromPlaceholderRow(page: import('@playwright/test').Page): Promise<void> {
	await page.goto(`/desk/procurement-planning?plan=${PLAN_CODE}&queue=draft_packages`, {
		waitUntil: 'domcontentloaded',
	});

	const workbenchFrame = page.frameLocator('[data-testid="pp4-workbench-design-iframe"]');
	const placeholderRow = workbenchFrame.locator('tr[data-inclusion-code]').first();
	await expect(placeholderRow).toBeVisible({ timeout: 30000 });
	await expect(placeholderRow).toContainText(WORKS_DEMAND_TITLE);
	await placeholderRow.click();

	// pp2_planning_router.js stores the pre-selection handoff in
	// sessionStorage and navigates the top-level Desk app (not the
	// Workbench iframe) to the dedicated wizard page.
	await page.waitForURL(/create-package-wizard/, { timeout: 15000 });
}

test.describe('PW12 Package Creation Wizard journey (dedicated page, In Creation entry point)', () => {
	test.beforeAll(() => {
		// Restore the canonical allocation first in case a previous run's
		// happy-path describe (below) was interrupted before its own
		// afterAll could run, leaving the shared fixture bumped.
		setBudgetLineAllocation(CANONICAL_BUDGET_ALLOCATION);
		resetWorksMasterSeedIncludedInPlan();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
	});

	test('walks Steps 1-3 with live data and gates Create on the funding-blocked seed condition', async ({ page }) => {
		await openWizardFromPlaceholderRow(page);

		// Step 1 — Select Demands: pre-selected inclusion, live eligibility
		// list, compatibility computed live (single selection, no conflict).
		await expect(page.locator('.kt-pw-title')).toHaveText('Create Package', { timeout: 20000 });
		const demandCard = page.locator('[data-testid="kt-pw-demand-card"]').first();
		await expect(demandCard).toBeVisible({ timeout: 20000 });
		await expect(demandCard.locator('[data-testid="kt-pw-demand-title"]')).toContainText(WORKS_DEMAND_TITLE);
		await expect(demandCard.locator('[data-testid="kt-pw-select-demand"]')).toContainText('Selected');
		// XMOD-STR-004 — Demand Strategy Reference as Name (CODE).
		const strategy = demandCard.locator('[data-testid="kt-pw-demand-strategy"]');
		await expect(strategy).toBeVisible({ timeout: 10000 });
		await expect(strategy).toContainText('MOH-TGT-AVAIL-2028');
		await expect(strategy).toContainText('(');
		await expect(strategy).not.toHaveText(/^[a-z0-9]{8,14}$/);

		const step1Next = page.locator('[data-testid="kt-pw-step1-next"]');
		await expect(step1Next).toBeEnabled();
		await step1Next.click();

		// Step 2 — Configure Package: defaults populated from the demand,
		// lines table, funding summary and doc-path preview render live.
		const titleInput = page.locator('[data-testid="kt-pw-title-input"]');
		await expect(titleInput).toBeVisible({ timeout: 20000 });
		await expect(titleInput).not.toHaveValue('');
		await expect(page.locator('.kt-pw-table')).toBeVisible();
		await expect(page.locator('.kt-pw-summary-panel-dark')).toContainText('Funding Status');
		await expect(page.getByText('Document / STD Path')).toBeVisible();

		await page.locator('[data-testid="kt-pw-step2-next"]').click();

		// Step 3 — Review and Create: readiness checklist reflects real
		// backend funding evaluation and gates the Create action.
		const readinessItems = page.locator('[data-testid="kt-pw-readiness-item"]');
		await expect(readinessItems.first()).toBeVisible({ timeout: 20000 });
		const fundingRow = readinessItems.filter({ hasText: 'Funding linked / reserved' });
		await expect(fundingRow).toHaveAttribute('data-status', 'blocked', { timeout: 15000 });

		const createButton = page.locator('[data-testid="kt-pw-create-button"]');
		await expect(createButton).toBeDisabled();

		await page.screenshot({ path: 'artifacts/pw12-package-wizard-step3-blocked.png', fullPage: true });

		// Close without creating — journey validation only, seed stays
		// clean for the happy-path describe block below.
		await page.locator('[data-testid="kt-pw-step3-back"]').click();
		await expect(titleInput).toBeVisible({ timeout: 15000 });
	});
});

test.describe('PW12b Package Creation Wizard happy-path create (funded seed)', () => {
	test.beforeAll(() => {
		resetWorksMasterSeedIncludedInPlan();
		setBudgetLineAllocation(BUMPED_BUDGET_ALLOCATION);
	});

	test.afterAll(() => {
		// Explicitly restores the canonical Budget Line allocation — the
		// seed reset alone does NOT do this (idempotent-preserve-if-exists
		// upsert leaves amount_allocated untouched on an existing row) — and
		// re-seeds INCLUDED_IN_PLAN so later specs relying on that
		// checkpoint (e.g. the blocked-path describe above, on a re-run)
		// see the untouched canonical seed again.
		setBudgetLineAllocation(CANONICAL_BUDGET_ALLOCATION);
		resetWorksMasterSeedIncludedInPlan();
	});

	test.beforeEach(async ({ page }) => {
		const loggedIn = await tryLoginAsPlanner(page);
		test.skip(!loggedIn, 'Procurement Planner (planner@moh.test) not configured on target site');
	});

	test('creates a package end-to-end and lands on the Step 4 success screen', async ({ page }) => {
		await openWizardFromPlaceholderRow(page);

		await expect(page.locator('[data-testid="kt-pw-demand-card"]').first()).toBeVisible({ timeout: 20000 });
		await page.locator('[data-testid="kt-pw-step1-next"]').click();

		await expect(page.locator('[data-testid="kt-pw-title-input"]')).toBeVisible({ timeout: 20000 });
		await page.locator('[data-testid="kt-pw-step2-next"]').click();

		const createButton = page.locator('[data-testid="kt-pw-create-button"]');
		await expect(createButton).toBeEnabled({ timeout: 20000 });
		await createButton.click();

		const success = page.locator('[data-testid="kt-pw-success"]');
		await expect(success).toBeVisible({ timeout: 20000 });
		await expect(success.locator('.kt-pw-success-title')).toContainText('Package Created Successfully');

		// Package Reference chip shows a real PKG-* code, not a placeholder.
		const refValue = success.locator('.kt-pw-success-meta-grid .kt-pw-demand-meta-value').first();
		await expect(refValue).not.toHaveText('');
		await expect(refValue).toHaveText(/PKG-/);

		await expect(page.locator('[data-testid="kt-pw-open-package"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-pw-back-to-workbench"]')).toBeVisible();
	});
});
