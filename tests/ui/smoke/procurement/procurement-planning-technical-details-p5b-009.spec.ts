/**
 * P5B-009 — Permission-aware Technical Details toggle inside Evidence Drawer.
 */
import { expect, test } from '@playwright/test';
import {
	loginAsAdministrator,
	loginAsPlanningAuthority,
	loginAsProcurementPlanner,
} from '../../helpers/auth';

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

const TECHNICAL_CODES = [
	'PLANINCL-MOH-2026-001',
	'PKGREL-MOH-2026-001',
	'PKGCONSUME-MOH-2026-001',
	'PKG-MOH-2026-001',
	'TND-MOH-2026-001',
] as const;

const TECHNICAL_FIELD_KEYS = [
	'source_object_code',
	'target_object_code',
	'locked_summary_json',
	'passed_forward_summary_json',
	'technical_refs_json',
	'audit_event_ref',
] as const;

const FORBIDDEN_LEAKAGE = [
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/locked_summary_json/i,
	/passed_forward_summary_json/i,
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
	const title = String(item.title || '');
	for (let attempt = 0; attempt < 3; attempt += 1) {
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
		const row = page.getByTestId('pp2-work-list-row').first();
		await expect(row).toBeVisible({ timeout: 15000 });
		try {
			await row.click({ timeout: 10000 });
			await expect(page.getByTestId('pp2-selected-summary-title')).toHaveText(title, { timeout: 15000 });
			return;
		} catch {
			if (attempt === 2) {
				throw new Error(`Failed to select fixture row after ${attempt + 1} attempts`);
			}
		}
	}
}

async function openEvidenceDrawer(page: import('@playwright/test').Page) {
	await renderFixtureAndSelect(page, PACKAGE_FIXTURE_ITEM);
	await page.getByTestId('pp2-view-evidence-button').click();
	await expect(page.getByTestId('pp2-evidence-drawer')).toBeVisible();
}

test.describe('P5B-009 Technical Details toggle (authorized)', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expandRightPanel(page);
		await expect(page.getByTestId('pp2-primary-work-list-host')).toBeVisible({ timeout: 30000 });
	});

	test('shows technical details toggle for authorized user', async ({ page }) => {
		await openEvidenceDrawer(page);
		await expect(page.getByTestId('pp2-technical-details-toggle')).toBeVisible();
	});

	test('keeps technical details panel collapsed by default', async ({ page }) => {
		await openEvidenceDrawer(page);
		await expect(page.getByTestId('pp2-technical-details-panel')).toBeHidden();
		const drawerText = await page.getByTestId('pp2-evidence-drawer').innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(drawerText).not.toMatch(pattern);
		}
	});

	test('reveals WORKS technical refs after explicit expansion', async ({ page }) => {
		await openEvidenceDrawer(page);
		await page.getByTestId('pp2-technical-details-toggle').click();
		const panel = page.getByTestId('pp2-technical-details-panel');
		await expect(panel).toBeVisible();
		for (const code of TECHNICAL_CODES) {
			await expect(panel).toContainText(code);
		}
		for (const key of TECHNICAL_FIELD_KEYS) {
			await expect(panel).toContainText(key);
		}
	});
});

test.describe('P5B-009 Technical Details toggle (Planning Authority)', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsPlanningAuthority(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expandRightPanel(page);
		await expect(page.getByTestId('pp2-primary-work-list-host')).toBeVisible({ timeout: 30000 });
	});

	test('Planning Authority user resolves may_view_technical from boot roles', async ({ page }) => {
		const mayView = await page.evaluate(() => {
			const drawer = (
				window as unknown as {
					kentender_procurement?: {
						PlanningEvidenceDrawer?: {
							resolveMayViewTechnical: (o: object) => boolean;
						};
					};
				}
			).kentender_procurement?.PlanningEvidenceDrawer;
			if (!drawer) {
				throw new Error('PlanningEvidenceDrawer unavailable');
			}
			return drawer.resolveMayViewTechnical({});
		});
		expect(mayView).toBe(true);
	});
});

test.describe('P5B-009 Technical Details toggle (unauthorized)', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsProcurementPlanner(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expandRightPanel(page);
		await expect(page.getByTestId('pp2-primary-work-list-host')).toBeVisible({ timeout: 30000 });
	});

	test('hides technical details toggle for Procurement Planner', async ({ page }) => {
		await openEvidenceDrawer(page);
		await expect(page.getByTestId('pp2-technical-details-toggle')).toHaveCount(0);
		await expect(page.getByTestId('pp2-technical-details-panel')).toHaveCount(0);
		const drawerText = await page.getByTestId('pp2-evidence-drawer').innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(drawerText).not.toMatch(pattern);
		}
	});
});
