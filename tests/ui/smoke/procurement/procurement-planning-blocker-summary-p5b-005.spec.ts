/**
 * P5B-005 — Shared blocker summary in PP2 selected summary panel.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const BASE_FIXTURE = {
	id: 'pkg-moh-2026-001',
	title: 'District Hospital Renovation Works',
	subtitle: 'Works · Open Tender · 98,000,000 KES',
	status_label: 'In Preparation',
	funding_label: 'Budget linked',
	next_action_label: 'Complete package',
	primary_action: { label: 'Open Package', action: 'open_package' },
	show_evidence_action: true,
};

const FORBIDDEN_LEAKAGE = [/PLANINCL-/i, /source object/i, /target object/i, /DocType/i];

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

test.describe('P5B-005 Planning blocker summary', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expandRightPanel(page);
		await expect(page.getByTestId('pp2-primary-work-list-host')).toBeVisible({ timeout: 30000 });
	});

	test('shows no blockers state', async ({ page }) => {
		await renderFixtureAndSelect(page, {
			...BASE_FIXTURE,
			blocker_count: 0,
			blockers: [],
		});

		const blockerSummary = page.getByTestId('pp2-selected-summary-blockers').getByTestId('pp2-blocker-summary');
		await expect(blockerSummary).toBeVisible();
		await expect(blockerSummary).toHaveAttribute('data-blocker-state', 'none');
		await expect(page.getByTestId('pp2-blocker-summary-empty')).toBeVisible();
		await expect(page.getByTestId('pp2-blocker-summary-empty')).toContainText(/No blockers/i);
		await expect(page.getByTestId('pp2-blocker-summary-item')).toHaveCount(0);
	});

	test('shows single blocker state with explanatory label', async ({ page }) => {
		await renderFixtureAndSelect(page, {
			...BASE_FIXTURE,
			blocker_count: 1,
			blockers: [{ label: 'Budget not linked' }],
		});

		const blockerSummary = page.getByTestId('pp2-blocker-summary');
		await expect(blockerSummary).toHaveAttribute('data-blocker-state', 'single');
		await expect(page.getByTestId('pp2-blocker-summary-item')).toHaveCount(1);
		await expect(page.getByTestId('pp2-blocker-summary-item')).toHaveText('Budget not linked');
		await expect(page.getByTestId('pp2-blocker-summary-empty')).toHaveCount(0);

		const text = await page.getByTestId('pp2-selected-summary-panel').innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(text).not.toMatch(pattern);
		}
	});

	test('shows multiple blockers as concise list', async ({ page }) => {
		await renderFixtureAndSelect(page, {
			...BASE_FIXTURE,
			blocker_count: 2,
			blockers: [
				{ label: 'Budget not linked' },
				{ label: 'Readiness checks incomplete' },
			],
		});

		const blockerSummary = page.getByTestId('pp2-blocker-summary');
		await expect(blockerSummary).toHaveAttribute('data-blocker-state', 'multiple');
		await expect(page.getByTestId('pp2-blocker-summary-item')).toHaveCount(2);
		await expect(page.getByTestId('pp2-blocker-summary-item').nth(0)).toHaveText('Budget not linked');
		await expect(page.getByTestId('pp2-blocker-summary-item').nth(1)).toHaveText(
			'Readiness checks incomplete'
		);

		const text = await page.getByTestId('pp2-selected-summary-panel').innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(text).not.toMatch(pattern);
		}
	});

	test('nests blocker summary under selected summary blockers host', async ({ page }) => {
		await renderFixtureAndSelect(page, {
			...BASE_FIXTURE,
			blocker_count: 1,
			blockers: [{ label: 'Method not selected' }],
		});

		const host = page.getByTestId('pp2-selected-summary-blockers');
		await expect(host).toBeVisible();
		await expect(host.getByTestId('pp2-blocker-summary')).toHaveCount(1);
		await expect(host).toContainText(/Blockers/i);
	});
});
