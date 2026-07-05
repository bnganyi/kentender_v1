/**
 * PD11 — Package Detail dedicated page journey.
 *
 * Validates the canonical package-detail Frappe Page (`package_detail_page.js`)
 * and Workbench title-link routing (PD9) against the WORKS master seed.
 */
import { execSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';
import {
	loginAsPlanningAuthority,
	loginAsPlanningReviewer,
	loginAsProcurementPlanner,
} from '../../helpers/auth';

const BENCH_ROOT = path.resolve(__dirname, '../../../../../../');
const PLAN_CODE = 'PLAN-MOH-2026';
const PKG_CODE = 'PKG-MOH-2026-001';
const PKG_TITLE = 'District Hospital Renovation Works';

function resetWorksMasterSeedPackageDraft(): void {
	execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master ' +
			'--kwargs \'{"checkpoint": "PACKAGE_DRAFT", "force_reset": True}\'',
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

async function tryLoginAsAuthority(page: import('@playwright/test').Page): Promise<boolean> {
	try {
		await loginAsPlanningAuthority(page);
		return true;
	} catch (e) {
		const msg = e instanceof Error ? e.message : String(e);
		if (msg.includes('Invalid Login')) {
			return false;
		}
		throw e;
	}
}

function ensurePackageSchedule(): void {
	execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.tests.pp3_ui_journey_helpers.ensure_works_master_package_schedule',
		{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
	);
}

function markPackageReadyForRelease(): void {
	execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.tests.pp3_ui_journey_helpers.mark_works_master_package_ready_for_release',
		{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
	);
}

function releasePackageForUiJourney(): void {
	execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.tests.pp3_ui_journey_helpers.release_works_master_package_for_ui_journey',
		{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
	);
}

async function openPackageDetail(page: import('@playwright/test').Page): Promise<void> {
	await page.goto(`/app/package-detail/${PKG_CODE}`, { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('kt-pd-detail')).toBeVisible({ timeout: 30000 });
}

async function expectStatusPill(page: import('@playwright/test').Page, pattern: RegExp): Promise<void> {
	await expect(page.getByTestId('kt-pd-status-pill')).toContainText(pattern, { timeout: 90000 });
}

function getPackageStatus(): string {
	const out = execSync(
		'bench --site kentender.midas.com execute ' +
			'kentender_procurement.procurement_planning.tests.pp3_ui_journey_helpers.get_works_master_package_status',
		{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
	);
	const parsed = JSON.parse(out.trim()) as { status?: string };
	return String(parsed.status || '');
}

async function dismissFrappeDialog(page: import('@playwright/test').Page): Promise<void> {
	const dialog = page.getByRole('dialog');
	if (await dialog.isVisible().catch(() => false)) {
		await dialog.getByRole('button').first().click();
	}
}

async function clickPackageDetailAction(
	page: import('@playwright/test').Page,
	testId: string,
	methodPath: string,
): Promise<void> {
	const responsePromise = page.waitForResponse(
		(response) =>
			response.url().includes(`/api/method/${methodPath}`) &&
			response.request().method() === 'POST',
		{ timeout: 90000 },
	);
	await page.getByTestId(testId).click();
	const response = await responsePromise;
	const payload = (await response.json()) as {
		exc?: string;
		_server_messages?: string;
		message?: { status?: string; ok?: boolean; error_code?: string; message?: string };
	};
	if (payload.exc) {
		throw new Error(`${methodPath} failed: ${payload.exc}`);
	}
	if (payload._server_messages) {
		const messages = JSON.parse(payload._server_messages) as Array<[string, string?, string?, string?]>;
		const errorText = messages.map((row) => row[0]).join(' ');
		if (/error|not permitted|invalid/i.test(errorText)) {
			throw new Error(`${methodPath} failed: ${errorText}`);
		}
	}
	const message = payload.message;
	if (message && typeof message === 'object' && message.ok === false) {
		throw new Error(`${methodPath} failed: ${message.error_code || message.message || 'unknown error'}`);
	}
	await dismissFrappeDialog(page);
	await expect(page.getByTestId('kt-pd-loading')).toBeHidden({ timeout: 90000 });
}

async function tryLoginAsReviewer(page: import('@playwright/test').Page): Promise<boolean> {
	try {
		await loginAsPlanningReviewer(page);
		return true;
	} catch (e) {
		const msg = e instanceof Error ? e.message : String(e);
		if (msg.includes('Invalid Login')) {
			return false;
		}
		throw e;
	}
}

test.describe('PD11a Full lifecycle journey', () => {
	test.describe.configure({ mode: 'serial' });

	test.beforeAll(() => {
		resetWorksMasterSeedPackageDraft();
		ensurePackageSchedule();
	});

	test.afterAll(() => {
		resetWorksMasterSeedPackageDraft();
	});

	test('draft through released keeps shell mounted with status-specific panels', async ({ page }) => {
		test.setTimeout(240000);
		if (!(await tryLoginAsPlanner(page))) {
			test.skip(true, 'planner@moh.test not configured on target site');
		}

		await openPackageDetail(page);
		await expectStatusPill(page, /IN CREATION/i);
		await expect(page.getByTestId('kt-pd-submit-review')).toBeVisible();
		await expect(page.getByTestId('kt-pd-release-action')).toHaveCount(0);
		await expect(page.getByTestId('kt-pd-header')).toBeVisible();
		await expect(page.getByTestId('kt-pd-tabs')).toBeVisible();

		await clickPackageDetailAction(
			page,
			'kt-pd-submit-review',
			'kentender_procurement.procurement_planning.api.workflow.submit_package',
		);
		await expectStatusPill(page, /AWAITING REVIEW/i);
		expect(getPackageStatus()).toMatch(/In Review/i);

		await page.context().clearCookies();
		if (!(await tryLoginAsReviewer(page))) {
			test.skip(true, 'planning.reviewer@moh.test not configured on target site');
		}
		await openPackageDetail(page);
		await expectStatusPill(page, /AWAITING REVIEW/i);
		await page.getByTestId('kt-pd-tab-review').click();
		await expect(page.getByTestId('kt-pd-approve')).toBeVisible();
		await expect(page.getByTestId('kt-pd-return')).toBeVisible();
		await clickPackageDetailAction(
			page,
			'kt-pd-approve',
			'kentender_procurement.procurement_planning.api.workflow.approve_package',
		);
		await expectStatusPill(page, /APPROVED/i);

		await page.getByTestId('kt-pd-tab-release').click();
		await expect(page.getByTestId('kt-pd-approved-note')).toBeVisible();
		await expect(page.getByTestId('kt-pd-release-action')).toBeDisabled();

		await page.context().clearCookies();
		if (!(await tryLoginAsPlanner(page))) {
			test.skip(true, 'planner@moh.test not configured on target site');
		}
		await openPackageDetail(page);
		await page.getByTestId('kt-pd-tab-readiness').click();
		await clickPackageDetailAction(
			page,
			'kt-pd-run-readiness',
			'kentender_procurement.procurement_planning.api.package_readiness.run_pp_package_readiness_checks',
		);
		await expect(page.getByTestId('kt-pd-panel-readiness')).toContainText(/Passed/i, {
			timeout: 90000,
		});

		markPackageReadyForRelease();

		await page.context().clearCookies();
		if (!(await tryLoginAsAuthority(page))) {
			test.skip(true, 'planning.authority@moh.test not configured on target site');
		}
		await openPackageDetail(page);
		await expectStatusPill(page, /READY FOR RELEASE/i);
		await page.getByTestId('kt-pd-tab-release').click();
		await expect(page.getByTestId('kt-pd-release-action')).toBeEnabled();

		releasePackageForUiJourney();
		await page.reload({ waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('kt-pd-detail')).toBeVisible({ timeout: 30000 });
		await expectStatusPill(page, /RELEASED/i);
		await page.getByTestId('kt-pd-tab-release').click();
		await expect(page.getByTestId('kt-pd-panel-release')).toContainText(/Successfully Released/i);
		await expect(page.getByTestId('kt-pd-header')).toBeVisible();
		await expect(page.getByTestId('kt-pd-tabs')).toBeVisible();
		await expect(page.getByTestId('kt-pd-release-checklist')).toBeVisible();
	});
});

test.describe('PD11 Package Detail page journey', () => {
	test.beforeAll(() => {
		resetWorksMasterSeedPackageDraft();
	});

	test('direct route renders shared shell, tabs, and draft overview', async ({ page }) => {
		if (!(await tryLoginAsPlanner(page))) {
			test.skip(true, 'planner@moh.test not configured on target site');
		}

		await page.goto(`/app/package-detail/${PKG_CODE}`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('kt-pd-detail')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('kt-pd-canvas')).toBeVisible();
		await expect(page.getByTestId('kt-pd-breadcrumb')).toBeVisible();
		await expect(page.getByTestId('kt-pd-title')).toContainText(PKG_TITLE);
		await expect(page.getByTestId('kt-pd-status-pill')).toBeVisible();
		await expect(page.getByTestId('kt-pd-tabs')).toBeVisible();
		await expect(page.getByTestId('kt-pd-tab-overview')).toBeVisible();
		await expect(page.getByTestId('kt-pd-panel-overview')).toBeVisible();
		await expect(page.getByTestId('kt-pd-sidebar')).toBeVisible();
		await expect(page.getByTestId('kt-pd-summary-card')).toBeVisible();
		await expect(page.getByTestId('kt-pd-footer')).toBeVisible();

		await page.getByTestId('kt-pd-tab-lines-funding').click();
		await expect(page.getByTestId('kt-pd-header')).toBeVisible();
		await expect(page.getByTestId('kt-pd-tabs')).toBeVisible();
		await expect(page.getByTestId('kt-pd-panel-lines-funding')).toBeVisible();
	});

	test('workbench In Creation title link opens package-detail page', async ({ page }) => {
		if (!(await tryLoginAsPlanner(page))) {
			test.skip(true, 'planner@moh.test not configured on target site');
		}

		await page.goto(`/desk/procurement-planning?plan=${PLAN_CODE}&queue=draft_packages`, {
			waitUntil: 'domcontentloaded',
		});

		const workbenchFrame = page.frameLocator('[data-testid="pp4-workbench-design-iframe"]');
		await workbenchFrame.getByRole('button', { name: /In Creation/i }).click();
		const packageRow = workbenchFrame.locator('tr', { hasText: PKG_CODE });
		await expect(packageRow.first()).toBeVisible({ timeout: 45000 });
		await packageRow.first().click();

		await page.waitForURL(/package-detail/, { timeout: 15000 });
		await expect(page.getByTestId('kt-pd-detail')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('kt-pd-title')).toContainText(PKG_TITLE);
	});
});

test.describe('PD11c In Review reviewer actions', () => {
	test.beforeAll(() => {
		resetWorksMasterSeedPackageDraft();
		execSync(
			'bench --site kentender.midas.com execute frappe.db.set_value ' +
				`--kwargs '{"dt": "Procurement Package", "dn": "${PKG_CODE}", "field": "status", "val": "In Review"}'`,
			{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
		);
	});

	test('review tab exposes approve, return, and clarify actions', async ({ page }) => {
		if (!(await tryLoginAsReviewer(page))) {
			test.skip(true, 'planning.reviewer@moh.test not configured on target site');
		}
		await page.goto(`/app/package-detail/${PKG_CODE}`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('kt-pd-detail')).toBeVisible({ timeout: 30000 });
		await page.getByTestId('kt-pd-tab-review').click();
		await expect(page.getByTestId('kt-pd-approve')).toBeVisible();
		await expect(page.getByTestId('kt-pd-return')).toBeVisible();
		await expect(page.getByTestId('kt-pd-clarify')).toBeVisible();
		await expect(page.getByTestId('kt-pd-header')).toBeVisible();
	});
});

test.describe('PD11b Package Detail blocker banner', () => {
	test.beforeAll(() => {
		resetWorksMasterSeedPackageDraft();
		execSync(
			'bench --site kentender.midas.com execute frappe.db.set_value ' +
				`--kwargs '{"dt": "Procurement Package", "dn": "${PKG_CODE}", "field": "status", "val": "Returned for Correction"}'`,
			{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
		);
	});

	test('returned package shows blocker banner on overview', async ({ page }) => {
		if (!(await tryLoginAsPlanner(page))) {
			test.skip(true, 'planner@moh.test not configured on target site');
		}

		await page.goto(`/app/package-detail/${PKG_CODE}`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('kt-pd-detail')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('kt-pd-blocker-banner')).toBeVisible({ timeout: 15000 });
		await expect(page.getByTestId('kt-pd-status-info')).toBeVisible();
		await expect(page.getByTestId('kt-pd-view-block-history')).toBeVisible();
	});

	test('readiness failure shows readiness blocker banner', async ({ page }) => {
		if (!(await tryLoginAsPlanner(page))) {
			test.skip(true, 'planner@moh.test not configured on target site');
		}
		resetWorksMasterSeedPackageDraft();
		execSync(
			'bench --site kentender.midas.com execute frappe.db.set_value ' +
				`--kwargs '{"dt": "Procurement Package", "dn": "${PKG_CODE}", "field": "readiness_status", "val": "Failed"}'`,
			{ cwd: BENCH_ROOT, stdio: 'pipe', encoding: 'utf8' },
		);
		await page.goto(`/app/package-detail/${PKG_CODE}`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('kt-pd-blocker-banner')).toBeVisible({ timeout: 15000 });
		await expect(page.getByTestId('kt-pd-blocker-banner')).toContainText(/Readiness/i);
	});
});
