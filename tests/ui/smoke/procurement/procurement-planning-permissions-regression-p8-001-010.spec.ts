/**
 * P8-001..P8-010 — Permissions, leakage, and navigation regression gate.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import { loginAsAdministrator, loginAsProcurementPlanner } from '../../helpers/auth';
import { pp3Root } from '../../helpers/pp3Workbench';
import {
	P5_ORDINARY_FLOW_FORBIDDEN_LEAKAGE,
	assertNoOrdinaryFlowLeakage,
} from '../../helpers/procurementPlanningLeakage';

const PKG_CODE = 'PKG-MOH-2026-001';
const PKG_TITLE = 'District Hospital Renovation Works';
const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');

const P8_FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/feature content deferred/i,
	/\bstub content\b/i,
	/P5 surfaces completed/i,
	/Planning Workflow Status/i,
	/Canonical PP2 rendering is active/i,
];

const P8_FORBIDDEN_NAV_LABELS = [
	/Planning Home/i,
	/Approved Demands/i,
	/^Packages$/i,
	/Planning Evidence/i,
];

const ACTIVE_PLAN_API = '**/api/method/**get_pp_active_plan_view_model*';

const NO_ACTIVE_FIXTURE = {
	ok: true,
	role_key: 'planner',
	has_active_plan: false,
	fiscal_year: '2026/2027',
	message: 'No active procurement plan exists for FY 2026/2027.',
	primary_action: { label: 'Create Plan', action: 'create_plan' },
	secondary_action: { label: 'Activate Existing Plan', action: 'activate_existing_plan' },
	can_change_plan: false,
	can_view_plan: false,
};

function seedConsumedByTender(): void {
	execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master ' +
			'--kwargs \'{"checkpoint": "CONSUMED_BY_TENDER", "force_reset": True}\'',
		{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
	);
}

async function mockNoActivePlan(page: import('@playwright/test').Page): Promise<void> {
	await page.route(ACTIVE_PLAN_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: NO_ACTIVE_FIXTURE }),
		});
	});
}

test.describe.configure({ mode: 'serial' });

test.beforeAll(() => {
	seedConsumedByTender();
});

test.describe('P8-001 Role/state action matrix', () => {
	test.beforeAll(() => {
		execSync(
			'bench --site kentender.midas.com execute ' +
				'kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master ' +
				'--kwargs \'{"checkpoint": "PACKAGE_DRAFT", "force_reset": True}\'',
			{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
		);
	});

	test.beforeEach(async ({ page }) => {
		await loginAsProcurementPlanner(page);
	});

	test('draft package detail hides release action for planner', async ({ page }) => {
		await page.goto(`/app/package-detail/${PKG_CODE}`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('kt-pd-detail')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('kt-pd-release-action')).toHaveCount(0);
	});

	test.afterAll(() => {
		seedConsumedByTender();
	});
});

test.describe('P8-002 No active plan enforcement', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await mockNoActivePlan(page);
	});

	test('workbench hides Include in Plan without active plan', async ({ page }) => {
		await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-planning-work-unavailable')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-primary-action')).toHaveCount(0);
		await expect(page.locator('body')).not.toContainText('Add to Active Plan');
	});
});

test.describe('P8-006 Technical leakage scan', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsProcurementPlanner(page);
	});

	test('released follow-up surface has no prohibited technical tokens', async ({ page }) => {
		await page.goto(`${pp3Root}/desk/procurement-planning/releases`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp3-released-to-tender-page')).toHaveCount(1, { timeout: 30000 });
		const bodyText = await page.locator('body').innerText();
		for (const pattern of P5_ORDINARY_FLOW_FORBIDDEN_LEAKAGE) {
			expect(bodyText).not.toMatch(pattern);
		}
		assertNoOrdinaryFlowLeakage(bodyText, 'releases surface');
	});
});

test.describe('P8-007 Implementation copy scan', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('canonical PP3 routes contain no forbidden implementation copy', async ({ page }) => {
		const routes = [
			'/desk/procurement-planning',
			'/desk/procurement-planning/plans',
			'/desk/procurement-planning/releases',
		];
		for (const route of routes) {
			await page.goto(`${pp3Root}${route}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
			const bodyText = await page.locator('body').innerText();
			for (const pattern of P8_FORBIDDEN_IMPLEMENTATION_COPY) {
				expect(bodyText).not.toMatch(pattern);
			}
		}
	});
});

test.describe('P8-008 Navigation negative test', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('workbench header and sidebar exclude legacy five-screen labels', async ({ page }) => {
		await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-page-title')).toHaveText('Workbench', { timeout: 30000 });
		const bodyText = await page.locator('body').innerText();
		for (const pattern of P8_FORBIDDEN_NAV_LABELS) {
			expect(bodyText).not.toMatch(pattern);
		}
	});
});

test.describe('P8-009 Evidence permission', () => {
	test('administrator can expand technical details from released surface', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`${pp3Root}/desk/procurement-planning/releases`, {
			waitUntil: 'domcontentloaded',
		});
		await page.getByTestId('pp3-view-release-evidence').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await drawer.getByTestId('pp3-technical-details-toggle').click();
		await expect(drawer.getByTestId('pp3-technical-details-panel')).toBeVisible({ timeout: 30000 });
	});

	test('planner cannot expand technical details', async ({ page }) => {
		await loginAsProcurementPlanner(page);
		await page.goto(`${pp3Root}/desk/procurement-planning/releases`, {
			waitUntil: 'domcontentloaded',
		});
		await page.getByTestId('pp3-view-release-evidence').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await expect(drawer.getByTestId('pp3-evidence-timeline')).toBeVisible({ timeout: 30000 });
		await expect(drawer.getByTestId('pp3-technical-details-toggle')).toHaveCount(0);
	});
});

test.describe('P8-010 Supplier confidentiality', () => {
	const SUPPLIER_EMAIL = 'supplier.p8-010@moh.test';
	const SUPPLIER_PASSWORD = 'test';

	test.beforeAll(() => {
		execSync(
			'bench --site kentender.midas.com execute ' +
				'kentender_procurement.procurement_planning.tests.pp3_ui_suppliers.ensure_p7_010_supplier_user ' +
				'--kwargs \'{"email": "supplier.p8-010@moh.test", "password": "test"}\'',
			{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
		);
	});

	test('supplier is denied Planning workbench and evidence', async ({ page }) => {
		await page.goto(`${pp3Root}/login`);
		await page.fill('#login_email', SUPPLIER_EMAIL);
		await page.fill('#login_password', SUPPLIER_PASSWORD);
		await page.click('button[type="submit"]');
		await page.waitForURL(/\/(desk|portal)(\/|$)/, { timeout: 30000 });
		await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByRole('heading', { name: 'Not Permitted' })).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-evidence-drawer')).toHaveCount(0);
	});
});
