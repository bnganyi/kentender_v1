/**
 * P2-007 — SelectedWorkSummary renders PP3 selected item contract.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const WORKLIST_METHOD =
	'kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model';

const FORBIDDEN_LEAKAGE = [
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/technical_refs_json/i,
	/audit_event_ref/i,
];

const NEEDS_PLANNING_FIXTURE = {
	ok: true,
	queue: 'needs_planning',
	total: 1,
	start: 0,
	limit: 20,
	items: [
		{
			work_item_id: 'needs_planning:DEM-MOH-2026-001',
			title: 'District Hospital Renovation Works',
			subtitle: 'Works · 98,000,000 KES · Budget linked',
			state_label: 'Needs planning',
			list_next_action: 'Add to active plan',
			next_action_label: 'Add to Active Plan',
			summary_detail_line: 'Approved demand · Works · KES 98,000,000',
			status_headline: 'Ready to plan',
			status_detail: 'Funding is linked. No blockers found.',
			next_step_detail: 'Add this demand to the active procurement plan.',
			blockers: [],
			primary_action: { label: 'Add to Active Plan', action: 'include_in_plan', target: 'DEM-MOH-2026-001' },
			secondary_actions: [
				{ label: 'View Demand', action: 'view_demand', target: 'DEM-MOH-2026-001' },
				{ label: 'View Evidence', action: 'open_evidence', target: 'DEM-MOH-2026-001' },
			],
		},
	],
};

async function mockWorkbenchItems(
	page: import('@playwright/test').Page,
) {
	await page.route('**/api/method/**', async (route) => {
		const request = route.request();
		const url = request.url();
		const postData = request.postData() || '';
		if (!url.includes('get_pp_workbench_item_view_model') && !postData.includes(WORKLIST_METHOD)) {
			await route.continue();
			return;
		}
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: NEEDS_PLANNING_FIXTURE }),
		});
	});
}

test.describe('P2-007 SelectedWorkSummary', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('renders selected summary with one primary action and evidence button', async ({ page }) => {
		await mockWorkbenchItems(page);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-work-list')).toBeVisible({ timeout: 30000 });
		const summary = page.getByTestId('pp3-selected-work-summary');
		await expect(summary).toBeVisible({ timeout: 30000 });
		await expect(summary).toContainText('Selected Work');
		await expect(summary).toContainText('District Hospital Renovation Works');
		await expect(summary).toContainText('Ready to plan');
		await expect(summary).toContainText('Add to Active Plan');
		await expect(summary.getByTestId('pp3-primary-action')).toHaveCount(1);
		await expect(summary.getByTestId('pp3-secondary-actions')).toBeVisible();
		await expect(summary.getByTestId('pp3-view-evidence-button')).toBeVisible();
		const summaryText = await summary.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(summaryText).not.toMatch(pattern);
		}
	});
});
