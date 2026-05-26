import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root = process.env.UI_BASE_URL || 'http://127.0.0.1:8000';
const seedPackageCode = 'PKG-MOH-2026-001';

const PACKAGE_STATUSES = [
	'Draft',
	'In Review',
	'Returned for Correction',
	'Approved',
	'Ready for Release',
	'Released to Tender',
	'Consumed by Tender Management',
	'Superseded',
	'Cancelled',
] as const;

const PACKAGE_STATUS_CLASSES: Record<(typeof PACKAGE_STATUSES)[number], string> = {
	Draft: 'is-draft',
	'In Review': 'is-in-review',
	'Returned for Correction': 'is-returned-for-correction',
	Approved: 'is-approved',
	'Ready for Release': 'is-ready-for-release',
	'Released to Tender': 'is-released-to-tender',
	'Consumed by Tender Management': 'is-consumed-by-tm',
	Superseded: 'is-superseded',
	Cancelled: 'is-cancelled',
};

const LIST_ABBREVIATIONS: Partial<Record<(typeof PACKAGE_STATUSES)[number], string>> = {
	'Consumed by Tender Management': 'Consumed',
	'Released to Tender': 'Released',
	'Returned for Correction': 'Returned',
};

test.describe('P5-004 PlanningStatusBadge', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('does not mount package status strip by default on packages route', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages?package_code=${seedPackageCode}`, {
			waitUntil: 'domcontentloaded',
		});

		await expect(page.getByTestId('pp2-primary-context-host')).toHaveCount(1);
		await expect(page.getByTestId('pp2-module-journey-context-header')).toHaveCount(0);
		await expect(page.getByTestId('pp2-package-status-strip')).toHaveCount(0);
		await expect(page.getByTestId('pp2-planning-status-badge')).toHaveCount(0);
	});

	test('PlanningStatusBadge maps all package lifecycle statuses', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-context-host')).toHaveCount(1);

		const mapping = await page.evaluate((statuses) => {
			const Badge = (window as any).kentender_procurement?.PlanningStatusBadge;
			if (!Badge || typeof Badge.html !== 'function') {
				return { ok: false, reason: 'PlanningStatusBadge unavailable' };
			}
			const header: Record<string, string> = {};
			const list: Record<string, string> = {};
			const classes: Record<string, string> = {};
			for (const status of statuses) {
				const headerHtml = Badge.html(status, { context: 'package', scope: 'header' });
				const listHtml = Badge.html(status, { context: 'package', scope: 'list' });
				const div = document.createElement('div');
				div.innerHTML = headerHtml;
				const el = div.querySelector('[data-testid="pp2-planning-status-badge"]');
				header[status] = (el?.textContent || '').trim();
				classes[status] = Array.from(el?.classList || [])
					.find((c) => c.startsWith('is-')) || '';
				div.innerHTML = listHtml;
				const listEl = div.querySelector('[data-testid="pp2-planning-status-badge"]');
				list[status] = (listEl?.textContent || '').trim();
			}
			return { ok: true, header, list, classes };
		}, PACKAGE_STATUSES as unknown as string[]);

		expect(mapping.ok, mapping.reason || 'mapping contract').toBe(true);
		if (!mapping.ok) return;

		for (const status of PACKAGE_STATUSES) {
			expect(mapping.header![status]).toBe(status);
			expect(mapping.classes![status]).toBe(PACKAGE_STATUS_CLASSES[status]);
		}

		expect(mapping.list!['Consumed by Tender Management']).toBe('Consumed');
		expect(mapping.list!['Released to Tender']).toBe('Released');
		expect(mapping.list!['In Review']).toBe('In Review');
		expect(mapping.list!['Ready for Release']).toBe('Ready for Release');
	});

	test('PlanningStatusBadge unknown status uses is-unknown class', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-context-host')).toHaveCount(1);

		const result = await page.evaluate(() => {
			const Badge = (window as any).kentender_procurement?.PlanningStatusBadge;
			const html = Badge.html('Not A Real Status', { context: 'package', scope: 'header' });
			const div = document.createElement('div');
			div.innerHTML = html;
			const el = div.querySelector('[data-testid="pp2-planning-status-badge"]');
			return {
				text: (el?.textContent || '').trim(),
				className: el?.className || '',
				statusKey: el?.getAttribute('data-status-key') || '',
			};
		});

		expect(result.text).toBe('Not A Real Status');
		expect(result.className).toContain('is-unknown');
		expect(result.statusKey).toBe('not a real status');
	});
});
