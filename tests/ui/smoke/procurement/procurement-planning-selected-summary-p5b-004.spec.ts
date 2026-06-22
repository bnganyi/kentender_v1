/**
 * P5B-004 — Selected summary panel in PP2 right panel.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const WORKBENCH_PATHS = [
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
] as const;

const PACKAGE_FIXTURE_ITEM = {
	id: 'pkg-moh-2026-001',
	title: 'District Hospital Renovation Works',
	subtitle: 'Works · Open Tender · 98,000,000 KES',
	status_label: 'Released',
	status_tone: 'success',
	funding_label: 'Budget linked',
	blocker_count: 0,
	next_action_label: 'Open Tender',
	primary_action: { label: 'Open Tender', action: 'open_tender' },
	secondary_actions: [{ label: 'Open Package', action: 'open_package' }],
	show_evidence_action: true,
};

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
];

const FORBIDDEN_SUMMARY_LEAKAGE = [/PLANINCL-/i, /source object/i, /target object/i];

async function expandRightPanel(page: import('@playwright/test').Page) {
	const shell = page.getByTestId('pp2-primary-workspace-shell');
	await expect(shell).toBeVisible({ timeout: 30000 });
	if ((await shell.getAttribute('data-right-panel-collapsed')) === '1') {
		await page.getByTestId('pp2-primary-right-panel-toggle').click();
		await expect(shell).toHaveAttribute('data-right-panel-collapsed', '0');
	}
}

test.describe('P5B-004 Planning selected summary panel', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('shows idle summary shell on each workbench surface when panel expanded', async ({ page }) => {
		for (const path of WORKBENCH_PATHS) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expandRightPanel(page);
			await expect(page.getByTestId('pp2-selected-summary-panel')).toHaveCount(1);
			await expect(page.getByTestId('pp2-selected-summary-idle')).toBeVisible();
			await expect(page.getByTestId('pp2-selected-summary-idle')).toContainText(
				/Select an item to view summary/i
			);
		}
	});

	test('keeps legacy next-action panel empty without stub copy on packages', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expandRightPanel(page);
		const nextAction = page.getByTestId('pp2-primary-next-action-panel');
		await expect(nextAction).toHaveCount(1);
		await expect(nextAction).toHaveText('');
		await expect(nextAction).not.toContainText(/Next action/i);
	});

	test('populates summary from fixture row selection on packages route', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expandRightPanel(page);
		await expect(page.getByTestId('pp2-primary-work-list-host')).toBeVisible({ timeout: 30000 });

		await page.evaluate((item) => {
			const workListHost = document.querySelector('[data-testid="pp2-primary-work-list-host"]');
			const summaryHost = document.querySelector('[data-testid="pp2-primary-summary-host"]');
			const wl = (
				window as unknown as {
					kentender_procurement?: {
						PlanningWorkList?: { render: (h: Element, o: object) => void };
						PlanningSelectedSummaryPanel?: {
							render: (h: Element, o: object) => void;
							summaryFromWorkItem: (i: object) => object;
						};
					};
				}
			).kentender_procurement;
			if (!workListHost || !summaryHost || !wl?.PlanningWorkList || !wl?.PlanningSelectedSummaryPanel) {
				throw new Error('Planning work list or summary panel unavailable');
			}
			wl.PlanningWorkList.render(workListHost, {
				items: [item],
				slug: 'packages',
				onSelect: (_id: string, it: object) => {
					wl.PlanningSelectedSummaryPanel!.render(summaryHost, {
						summary: wl.PlanningSelectedSummaryPanel!.summaryFromWorkItem(it),
					});
				},
			});
		}, PACKAGE_FIXTURE_ITEM);

		await page.getByTestId('pp2-work-list-row').click();

		await expect(page.getByTestId('pp2-selected-summary-title')).toHaveText(PACKAGE_FIXTURE_ITEM.title);
		await expect(page.getByTestId('pp2-selected-summary-status')).toContainText('Released');
		await expect(page.getByTestId('pp2-selected-summary-facts')).toHaveText(PACKAGE_FIXTURE_ITEM.subtitle);
		await expect(page.getByTestId('pp2-selected-summary-funding')).toContainText('Budget linked');
		await expect(page.getByTestId('pp2-selected-summary-blockers')).toContainText(/No blockers/i);
		await expect(page.getByTestId('pp2-selected-summary-next-action')).toContainText('Open Tender');
		await expect(page.getByTestId('pp2-selected-summary-primary-action')).toHaveText('Open Tender');
		await expect(page.getByTestId('pp2-view-evidence-button')).toBeVisible();
		await expect(page.getByTestId('pp2-evidence-drawer')).toHaveCount(0);

		const summaryText = await page.getByTestId('pp2-selected-summary-panel').innerText();
		for (const pattern of FORBIDDEN_SUMMARY_LEAKAGE) {
			expect(summaryText).not.toMatch(pattern);
		}
		expect(summaryText).not.toContain(PACKAGE_FIXTURE_ITEM.id);
		await expect(page).toHaveURL(/item=pkg-moh-2026-001/);
	});

	test('canonical routes contain no forbidden implementation copy', async ({ page }) => {
		for (const path of [...WORKBENCH_PATHS, '/desk/procurement-planning'] as const) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			if (path !== '/desk/procurement-planning') {
				await expandRightPanel(page);
				await expect(page.getByTestId('pp2-selected-summary-panel')).toBeVisible({ timeout: 30000 });
			}
			const bodyText = await page.locator('body').innerText();
			for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
				expect(bodyText).not.toMatch(pattern);
			}
		}
	});
});
