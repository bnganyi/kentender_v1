/**
 * P2-006 — WorkList renders PP3 business rows on Workbench route.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const WORKLIST_API =
	'**/api/method/**get_pp_workbench_item_view_model*';

const FORBIDDEN_LEAKAGE = [
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/technical_refs_json/i,
	/audit_event_ref/i,
];

const QUEUE_FIXTURES: Record<string, object> = {
	needs_planning: {
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
				next_action_label: 'Include in Plan',
			},
		],
	},
	draft_packages: {
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
			},
		],
	},
};

async function mockWorkbenchItems(
	page: import('@playwright/test').Page,
) {
	await page.route(WORKLIST_API, async (route) => {
		let queue = 'needs_planning';
		try {
			const current = new URL(page.url());
			const byLocation = current.searchParams.get('queue');
			if (byLocation) queue = byLocation;
		} catch (_e) {
			/* ignore page URL parse failures */
		}
		const postData = route.request().postData() || '';
		if (postData) {
			try {
				const params = new URLSearchParams(postData);
				const argsRaw = params.get('args');
				if (argsRaw) {
					const parsed = JSON.parse(argsRaw) as { queue?: string };
					if (parsed.queue) queue = parsed.queue;
				}
			} catch (_e) {
				/* ignore malformed payload */
			}
		}
		const payload = QUEUE_FIXTURES[queue] || QUEUE_FIXTURES.needs_planning;
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
}

test.describe('P2-006 WorkList', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('renders PP3 work list rows with business labels on Workbench root', async ({ page }) => {
		await mockWorkbenchItems(page);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-work-list')).toBeVisible({ timeout: 30000 });
		const row = page.getByTestId('pp3-work-item-row').first();
		await expect(row).toBeVisible();
		await expect(row.getByTestId('pp3-work-item-title')).toHaveText('District Hospital Renovation Works');
		await expect(row.getByTestId('pp3-work-item-state')).toHaveText('Needs planning');
		await expect(row.getByTestId('pp3-work-item-next-action')).toHaveText('Include in Plan');
		const rowText = await row.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(rowText).not.toMatch(pattern);
		}
	});

	test('switching queue updates rows and keeps business copy', async ({ page }) => {
		await mockWorkbenchItems(page);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-work-list')).toBeVisible({ timeout: 30000 });
		await page.getByTestId('pp3-queue-draft-packages').click();
		await expect(page).toHaveURL(/queue=draft_packages/, { timeout: 30000 });
		const row = page.getByTestId('pp3-work-item-row').first();
		await expect(row.getByTestId('pp3-work-item-state')).toHaveText('Draft package');
		await expect(row.getByTestId('pp3-work-item-next-action')).toHaveText('Open Package');
		const rowText = await row.innerText();
		expect(rowText).not.toContain('PKG-MOH-2026-001');
	});
});
