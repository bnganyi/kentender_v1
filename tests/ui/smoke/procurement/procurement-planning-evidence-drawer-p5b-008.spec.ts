/**
 * P5B-008 — Shared Planning evidence drawer (on-demand shell).
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

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

const TIMELINE_LABELS = [
	'Demand approved',
	'Demand included in procurement plan',
	'Package prepared',
	'Readiness passed',
	'Package released to Tender Management',
	'Tender Management consumed package',
] as const;

const RECORD_LABELS = [
	'Demand Approval Certificate',
	'Planning Inclusion Record',
	'Planning Release Package',
	'Tender Consumption Record',
	'Readiness Result',
	'Review Decision',
] as const;

const FORBIDDEN_LEAKAGE = [
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/locked_summary_json/i,
	/passed_forward_summary_json/i,
];

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
	/feature content deferred/i,
	/stub content/i,
];

async function expandRightPanel(page: import('@playwright/test').Page) {
	const shell = page.getByTestId('pp2-primary-workspace-shell');
	await expect(shell).toBeVisible({ timeout: 30000 });
	if ((await shell.getAttribute('data-right-panel-collapsed')) === '1') {
		await page.getByTestId('pp2-primary-right-panel-toggle').click();
		await expect(shell).toHaveAttribute('data-right-panel-collapsed', '0');
	}
}

async function renderFixtureAndSelect(
	page: import('@playwright/test').Page,
	item: Record<string, unknown>
) {
	await page.evaluate((fixtureItem) => {
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
			items: [fixtureItem],
			slug: 'packages',
			onSelect: (_id: string, it: object) => {
				wl.PlanningSelectedSummaryPanel!.render(summaryHost, {
					summary: wl.PlanningSelectedSummaryPanel!.summaryFromWorkItem(it),
				});
			},
		});
	}, item);
	await page.getByTestId('pp2-work-list-row').click();
}

test.describe('P5B-008 Planning evidence drawer', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expandRightPanel(page);
		await expect(page.getByTestId('pp2-primary-work-list-host')).toBeVisible({ timeout: 30000 });
	});

	test('keeps evidence drawer closed by default after row selection', async ({ page }) => {
		await renderFixtureAndSelect(page, PACKAGE_FIXTURE_ITEM);
		await expect(page.getByTestId('pp2-view-evidence-button')).toBeVisible();
		await expect(page.getByTestId('pp2-evidence-drawer')).toHaveCount(0);
	});

	test('does not auto-open evidence drawer on row select only', async ({ page }) => {
		await renderFixtureAndSelect(page, PACKAGE_FIXTURE_ITEM);
		await expect(page.getByTestId('pp2-selected-summary-title')).toHaveText(PACKAGE_FIXTURE_ITEM.title);
		await expect(page.getByTestId('pp2-evidence-drawer')).toHaveCount(0);
	});

	test('opens evidence drawer when View Evidence is clicked', async ({ page }) => {
		await renderFixtureAndSelect(page, PACKAGE_FIXTURE_ITEM);
		await page.getByTestId('pp2-view-evidence-button').click();
		await expect(page.getByTestId('pp2-evidence-drawer')).toHaveCount(1);
		await expect(page.getByTestId('pp2-evidence-drawer')).toBeVisible();
	});

	test('shows business timeline and record labels in drawer', async ({ page }) => {
		await renderFixtureAndSelect(page, PACKAGE_FIXTURE_ITEM);
		await page.getByTestId('pp2-view-evidence-button').click();
		await expect(page.getByTestId('pp2-evidence-title')).toHaveText(PACKAGE_FIXTURE_ITEM.title);
		const timeline = page.getByTestId('pp2-evidence-timeline');
		await expect(timeline).toBeVisible();
		for (const label of TIMELINE_LABELS) {
			await expect(timeline).toContainText(label);
		}
		const records = page.getByTestId('pp2-evidence-record-list');
		await expect(records).toBeVisible();
		for (const label of RECORD_LABELS) {
			await expect(records.getByText(label, { exact: true })).toBeVisible();
		}
	});

	test('closes evidence drawer via close button and Escape', async ({ page }) => {
		await renderFixtureAndSelect(page, PACKAGE_FIXTURE_ITEM);
		await page.getByTestId('pp2-view-evidence-button').click();
		await expect(page.getByTestId('pp2-evidence-drawer')).toBeVisible();
		await page.getByTestId('pp2-evidence-drawer-close').click();
		await expect(page.getByTestId('pp2-evidence-drawer')).toHaveCount(0);

		await page.getByTestId('pp2-view-evidence-button').click();
		await expect(page.getByTestId('pp2-evidence-drawer')).toBeVisible();
		await page.keyboard.press('Escape');
		await expect(page.getByTestId('pp2-evidence-drawer')).toHaveCount(0);
	});

	test('drawer content contains no technical leakage', async ({ page }) => {
		await renderFixtureAndSelect(page, PACKAGE_FIXTURE_ITEM);
		await page.getByTestId('pp2-view-evidence-button').click();
		const drawerText = await page.getByTestId('pp2-evidence-drawer').innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(drawerText).not.toMatch(pattern);
		}
	});

	test('packages route contains no forbidden implementation copy with drawer open', async ({ page }) => {
		await renderFixtureAndSelect(page, PACKAGE_FIXTURE_ITEM);
		await page.getByTestId('pp2-view-evidence-button').click();
		const bodyText = await page.locator('body').innerText();
		for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
			expect(bodyText).not.toMatch(pattern);
		}
	});
});
