/**
 * P2-008 — EvidenceDrawer opens contextually from PP3 selected summary.
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

const FORBIDDEN_LEAKAGE = [
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/technical_refs_json/i,
	/audit_event_ref/i,
];

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

const EVIDENCE_FIXTURE = {
	ok: true,
	title: 'District Hospital Renovation Works Package',
	timeline: [
		{ label: 'Demand approved', status: 'complete' },
		{ label: 'Demand included in procurement plan', status: 'complete' },
		{ label: 'Package prepared', status: 'complete' },
	],
	records: [
		{ label: 'Demand Approval Certificate', type: 'demand_approval' },
		{ label: 'Planning Inclusion Record', type: 'planning_inclusion' },
		{ label: 'Procurement Package', type: 'procurement_package' },
	],
	technical_details: {
		visible_by_default: false,
		requires_permission: true,
		may_view_technical: true,
	},
};

async function mockWorkbenchAndEvidence(
	page: import('@playwright/test').Page,
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
				body: JSON.stringify({ message: EVIDENCE_FIXTURE }),
			});
			return;
		}
		await route.continue();
	});
}

test.describe('P2-008 EvidenceDrawer', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('stays closed by default then opens from PP3 View Evidence action', async ({ page }) => {
		await mockWorkbenchAndEvidence(page);
		await page.goto(`${root}/desk/procurement-planning?queue=draft_packages`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp3-work-list')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-selected-work-summary')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-evidence-drawer')).toHaveCount(0);

		await page.getByTestId('pp3-view-evidence-button').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await expect(drawer).toBeVisible({ timeout: 30000 });
		await expect(drawer.getByTestId('pp3-evidence-title')).toHaveText(
			'District Hospital Renovation Works Package',
		);
		await expect(drawer.getByTestId('pp3-evidence-timeline')).toContainText('Demand approved');
		await expect(drawer.getByTestId('pp3-evidence-record-list')).toContainText(
			'Demand Approval Certificate',
		);
		await expect(drawer.getByTestId('pp3-technical-details-toggle')).toBeVisible();
		await expect(drawer.getByTestId('pp3-technical-details-panel')).toBeHidden();

		const drawerText = await drawer.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(drawerText).not.toMatch(pattern);
		}
	});
});
