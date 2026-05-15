/**
 * UI-HARD-1610 — Release UI smoke (pack §21 ticket 1610, doc §21.2).
 *
 * Desk path: Procurement Planning workbench (`procurement_planning_workspace.js`).
 * Login: `Administrator` (workspace Page read); PP list/detail/landing responses are mocked.
 * `UI-SMOKE-REL-003` / `UI-SMOKE-REL-004` run in Vitest — see `ReleaseToTenderPage.spec.tsx`
 * and `npm run test:ui:smoke:rel-1610`.
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

type DetailMode = 'release_ok' | 'release_blocked_plan';

test.describe('UI-HARD-1610 — UI-SMOKE-REL-* (Desk Procurement Planning)', () => {
	test.setTimeout(180_000);

	test('UI-SMOKE-REL-001 — Approved plan shows Release to Tender', async ({ page, baseURL }) => {
		await installPpPlanningRouteMocks(page, { detailMode: 'release_ok' });
		/* Desk workspace route requires a user with Page/workspace access; API payloads are mocked separately. */
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/procurement-planning`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.getByTestId('pp-page-title')).toContainText('Procurement Planning', { timeout: 90_000 });
		await page.getByTestId('pp-tab-ready').click();
		await expect(page.getByTestId('pp-queue-ready-for-tender')).toBeVisible({ timeout: 30_000 });
		await page.getByTestId('pp-row-moh-rel-001').click();
		await expect(page.getByTestId('pp-action-release-to-tender')).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId('pp-action-release-to-tender')).toHaveText('Release to Tender');
	});

	test('UI-SMOKE-REL-002 — Blocked package shows plan release blocker', async ({ page, baseURL }) => {
		await installPpPlanningRouteMocks(page, { detailMode: 'release_blocked_plan' });
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/procurement-planning`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.getByTestId('pp-page-title')).toContainText('Procurement Planning', { timeout: 90_000 });
		await page.getByTestId('pp-tab-ready').click();
		await page.getByTestId('pp-row-moh-rel-001').click();
		const hint = page.getByTestId('pp-detail-release-blocked-hint');
		await expect(hint).toBeVisible({ timeout: 30_000 });
		await expect(hint).toContainText('release is blocked until the procurement plan is approved');
		await expect(page.getByTestId('pp-action-release-to-tender')).toHaveCount(0);
	});
});

function landingPayload() {
	return {
		ok: true,
		role_key: 'authority',
		currency: 'KES',
		current_plan: {
			name: 'PLAN-MOCK-REL',
			plan_name: 'Mock Annual Plan',
			plan_code: 'PLAN-REL-2026',
			fiscal_year: '2026',
			procuring_entity: 'ENTITY-1',
			procuring_entity_label: 'MOH',
			status: 'Approved',
			is_active: 1,
		},
		plans: [
			{
				name: 'PLAN-MOCK-REL',
				label: 'PLAN-REL-2026 — Mock Annual Plan',
				plan_code: 'PLAN-REL-2026',
				status: 'Approved',
			},
		],
		kpis: [
			{ id: 'total_packages', label: 'Total Packages', value: 1, format: 'int', testid: 'pp-kpi-total-packages' },
			{
				id: 'total_planned_value',
				label: 'Total Planned Value',
				value: 0,
				format: 'currency',
				currency: 'KES',
				testid: 'pp-kpi-total-value',
			},
			{ id: 'approved_packages', label: 'Approved Packages', value: 0, format: 'int', testid: 'pp-kpi-approved-packages' },
			{ id: 'ready_for_tender', label: 'Ready for Tender', value: 1, format: 'int', testid: 'pp-kpi-ready-for-tender' },
			{ id: 'high_risk_packages', label: 'High-Risk Packages', value: 0, format: 'int', testid: 'pp-kpi-high-risk' },
		],
		queue_tabs: {
			mywork: [
				{ id: 'pending_approval', label: 'Pending Approval', testid: 'pp-queue-pending-approval' },
				{
					id: 'high_risk_escalation',
					label: 'High-Risk Requiring Escalation',
					testid: 'pp-queue-high-risk-escalation',
				},
				{ id: 'method_override', label: 'Method Override Cases', testid: 'pp-queue-method-override' },
				{ id: 'high_risk_packages', label: 'High-Risk Packages', testid: 'pp-queue-high-risk-packages' },
			],
			all: [
				{ id: 'all_packages', label: 'All packages', testid: 'pp-queue-all-packages' },
				{ id: 'draft_packages', label: 'Draft Packages', testid: 'pp-queue-draft-packages' },
				{ id: 'ready_for_tender', label: 'Ready for Tender', testid: 'pp-queue-ready-for-tender' },
			],
			approved: [
				{ id: 'submitted_packages', label: 'Submitted Packages', testid: 'pp-queue-submitted-packages' },
				{
					id: 'high_risk_escalation',
					label: 'High-Risk Requiring Escalation',
					testid: 'pp-queue-high-risk-escalation',
				},
			],
			ready: [
				{ id: 'ready_for_tender', label: 'Ready for Tender', testid: 'pp-queue-ready-for-tender' },
				{
					id: 'approved_not_handed_off',
					label: 'Approved Not Yet Handed Off',
					testid: 'pp-queue-approved-not-handed-off',
				},
			],
		},
		show_new_plan: false,
		show_new_package: false,
		show_apply_template: false,
		show_submit_plan: false,
		show_approve_plan: false,
		show_return_plan: false,
		show_reject_plan: false,
		show_lock_plan: false,
		plan_submit_ready: true,
		plan_submit_blockers: [],
		plan_submit_blocker_codes: [],
	};
}

const listPayload = {
	ok: true,
	role_key: 'authority',
	queue_id: 'ready_for_tender',
	plan: { name: 'PLAN-MOCK-REL', plan_code: 'PLAN-REL-2026', plan_name: 'Mock Annual Plan' },
	rows: [
		{
			name: 'PKG-REL-MOCK',
			package_code: 'MOH-REL-001',
			package_name: 'Smoke Release Package',
			procurement_method: 'Open Tender',
			estimated_value: 100000,
			currency: 'KES',
			template_name: 'Works template',
			badges: { high_risk: false, emergency: 0, submitted: false, ready: true },
		},
	],
};

function detailPayload(mode: DetailMode) {
	const blocked = mode === 'release_blocked_plan';
	return {
		ok: true,
		role_key: 'authority',
		name: 'PKG-REL-MOCK',
		package_code: 'MOH-REL-001',
		package_name: 'Smoke Release Package',
		template_name: 'Works',
		procurement_method: 'Open Tender',
		contract_type: 'Works',
		currency: 'KES',
		estimated_value: 100000,
		schedule_start: null,
		schedule_end: null,
		status: 'Ready for Tender',
		plan_status: blocked ? 'Submitted' : 'Approved',
		release_blocked_by_plan: blocked,
		planning_status: '',
		method_override_flag: false,
		method_override_reason: '',
		workflow_reason: '',
		badges: {
			high_risk: false,
			emergency: false,
			submitted: false,
			ready: true,
			released: false,
		},
		actions: {
			edit: false,
			add_demand_lines: false,
			remove_demand_lines: false,
			complete: false,
			submit: false,
			approve: false,
			return: false,
			reject: false,
			mark_ready: false,
			release: !blocked,
		},
		definition: {
			package_name: 'Smoke Release Package',
			package_code: 'MOH-REL-001',
			template_name: 'Works',
			procurement_method: 'Open Tender',
			contract_type: 'Works',
			status: 'Ready for Tender',
			plan_status: blocked ? 'Submitted' : 'Approved',
			method_override_flag: false,
		},
		financial: { estimated_value: 100000, currency: 'KES', schedule_start: null, schedule_end: null },
		demand_lines: [],
		risk: { profile_name: '', profile_code: '', risk_level: '', risks: [] },
		kpi: { profile_name: '', profile_code: '', metrics: [] },
		decision_criteria: { profile_name: '', profile_code: '', criteria: [] },
		vendor_management: { profile_name: '', profile_code: '', monitoring_summary: [], escalation_summary: [] },
		workflow: {
			status: 'Ready for Tender',
			created_by: '',
			approved_by: '',
			approved_at: null,
			rejected_by: '',
			rejected_at: null,
			workflow_reason: '',
			planning_status: '',
		},
	};
}

async function installPpPlanningRouteMocks(page: Page, opts: { detailMode: DetailMode }) {
	const detailMode = opts.detailMode;
	await page.route('**/api/method/**get_pp_landing_shell_data*', async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: landingPayload() }),
		});
	});
	await page.route('**/api/method/**get_pp_package_list*', async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: listPayload }),
		});
	});
	await page.route('**/api/method/**get_pp_package_detail*', async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: detailPayload(detailMode) }),
		});
	});
}
