/**
 * P2-009 — Permission-aware technical details toggle in PP3 EvidenceDrawer.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const WORKLIST_METHOD =
	'kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model';
const EVIDENCE_METHOD =
	'kentender_procurement.procurement_planning.api.evidence_view_model.get_pp_evidence_view_model';

const WORKLIST_FIXTURE = {
	ok: true,
	queue: 'draft_packages',
	total: 1,
	start: 0,
	limit: 20,
	items: [
		{
			work_item_id: 'draft_packages:PKG-MOH-2026-001',
			title: 'District Hospital Renovation Works Package',
			subtitle: 'Works · Open Tender · 98,000,000 KES',
			state_label: 'Draft package',
			next_action_label: 'Open Package',
			blockers: [],
			underlying_object_type: 'procurement_package',
			underlying_object_code: 'PKG-MOH-2026-001',
			primary_action: { label: 'Open Package', action: 'open_package', target: 'PKG-MOH-2026-001' },
			secondary_actions: [{ label: 'View Package', action: 'view_package', target: 'PKG-MOH-2026-001' }],
		},
	],
};

const AUTHORIZED_EVIDENCE_FIXTURE = {
	ok: true,
	title: 'District Hospital Renovation Works Package',
	timeline: [{ label: 'Demand approved', status: 'complete' }],
	records: [{ label: 'Demand Approval Certificate', type: 'demand_approval' }],
	technical_details: {
		visible_by_default: false,
		requires_permission: true,
		may_view_technical: true,
		codes: ['PLANINCL-MOH-2026-001', 'PKGREL-MOH-2026-001', 'PKGCONSUME-MOH-2026-001'],
		fields: [
			{ key: 'source_object_code', value: 'DEM-MOH-2026-001' },
			{ key: 'target_object_code', value: 'PKG-MOH-2026-001' },
			{ key: 'locked_summary_json', value: '{"package_code":"PKG-MOH-2026-001"}' },
			{ key: 'passed_forward_summary_json', value: '{"release_code":"PKGREL-MOH-2026-001"}' },
			{ key: 'technical_refs_json', value: '{"inclusion":"PLANINCL-MOH-2026-001"}' },
			{ key: 'audit_event_ref', value: 'AUD-PP2-MOH-2026-001' },
		],
	},
};

const UNAUTHORIZED_EVIDENCE_FIXTURE = {
	ok: true,
	title: 'District Hospital Renovation Works Package',
	timeline: [{ label: 'Demand approved', status: 'complete' }],
	records: [{ label: 'Demand Approval Certificate', type: 'demand_approval' }],
	technical_details: {
		visible_by_default: false,
		requires_permission: true,
		may_view_technical: false,
	},
};

async function mockWorkbenchAndEvidence(
	page: import('@playwright/test').Page,
	evidenceFixture: object,
) {
	await page.route('**/api/method/**', async (route) => {
		const request = route.request();
		const url = request.url();
		const postData = request.postData() || '';
		if (url.includes('get_pp_workbench_item_view_model') || postData.includes(WORKLIST_METHOD)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ message: WORKLIST_FIXTURE }),
			});
			return;
		}
		if (url.includes('get_pp_evidence_view_model') || postData.includes(EVIDENCE_METHOD)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ message: evidenceFixture }),
			});
			return;
		}
		await route.continue();
	});
}

test.describe('P2-009 TechnicalDetailsToggle', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('authorized payload shows collapsed toggle then expands to technical refs', async ({ page }) => {
		await mockWorkbenchAndEvidence(page, AUTHORIZED_EVIDENCE_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning?queue=draft_packages`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp3-work-list')).toBeVisible({ timeout: 30000 });
		await page.getByTestId('pp3-view-evidence-button').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await expect(drawer).toBeVisible({ timeout: 30000 });

		const toggle = drawer.getByTestId('pp3-technical-details-toggle');
		const panel = drawer.getByTestId('pp3-technical-details-panel');
		await expect(toggle).toBeVisible();
		await expect(panel).toBeHidden();
		await toggle.click();
		await expect(panel).toBeVisible();
		await expect(panel).toContainText('PLANINCL-MOH-2026-001');
		await expect(panel).toContainText('source_object_code');
	});

	test('unauthorized payload hides technical toggle and panel', async ({ page }) => {
		await mockWorkbenchAndEvidence(page, UNAUTHORIZED_EVIDENCE_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning?queue=draft_packages`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp3-work-list')).toBeVisible({ timeout: 30000 });
		await page.getByTestId('pp3-view-evidence-button').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await expect(drawer).toBeVisible({ timeout: 30000 });
		await expect(drawer.getByTestId('pp3-technical-details-toggle')).toHaveCount(0);
		await expect(drawer.getByTestId('pp3-technical-details-panel')).toHaveCount(0);
	});
});
