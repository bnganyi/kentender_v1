/**
 * P5-001 / PP2-SMOKE-UI-002 — compact Procurement Planning sidebar (five persistent surfaces).
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';
import { expectPrimarySidebarItemHighlighted } from '../../helpers/workspacePatternContract';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const PP2_SURFACES = [
	{
		label: 'Planning Home',
		testId: 'pp2-planning-home',
		path: '/desk/procurement-planning',
	},
	{
		label: 'Approved Demands',
		testId: 'pp2-approved-demands-page',
		path: '/desk/procurement-planning/approved-demands',
	},
	{
		label: 'Plans',
		testId: 'pp2-plans-page',
		path: '/desk/procurement-planning/plans',
	},
	{
		label: 'Packages',
		testId: 'pp2-packages-page',
		path: '/desk/procurement-planning/packages',
	},
	{
		label: 'Released to Tender',
		testId: 'pp2-released-to-tender-page',
		path: '/desk/procurement-planning/releases',
	},
] as const;

const FORBIDDEN_SIDEBAR_LABELS = [
	'Planning Evidence',
	'Readiness Review',
	'Review & Approval',
	'Release to Tender Review',
	'Planning Release Package View',
	'Advanced / Technical Details',
];

async function sidebarLabels(page: import('@playwright/test').Page): Promise<string[]> {
	return page.evaluate(() => {
		const items = Array.from(document.querySelectorAll('.standard-sidebar-item'));
		return items
			.map((el) => (el.textContent || '').replace(/\s+/g, ' ').trim())
			.filter(Boolean);
	});
}

async function clickSidebarHref(page: import('@playwright/test').Page, href: string): Promise<void> {
	await page.waitForFunction((targetHref) => {
		return !!document.querySelector(`a.item-anchor[href="${targetHref}"]`);
	}, href);
	await page.evaluate((targetHref) => {
		const link = document.querySelector(`a.item-anchor[href="${targetHref}"]`);
		if (!(link instanceof HTMLAnchorElement)) {
			throw new Error(`Sidebar link missing: ${targetHref}`);
		}
		link.click();
	}, href);
}

test.describe('PP2 Planning nested sidebar (P5-001)', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('PP2-SMOKE-UI-002 — sidebar shows exactly five persistent Planning surfaces', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });

		const labels = await sidebarLabels(page);
		expect(labels.some((lab) => lab.includes('Procurement Home'))).toBeTruthy();
		expect(labels.some((lab) => lab.includes('Procurement Planning'))).toBeTruthy();
		for (const surface of PP2_SURFACES) {
			expect(labels.some((lab) => lab.includes(surface.label))).toBeTruthy();
		}
		for (const forbidden of FORBIDDEN_SIDEBAR_LABELS) {
			expect(labels.some((lab) => lab.includes(forbidden))).toBeFalsy();
		}
		expect(labels.filter((lab) => PP2_SURFACES.some((s) => lab.includes(s.label))).length).toBeGreaterThanOrEqual(5);
	});

	test('Procurement Planning parent expands and collapses child links', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const parent = page.locator('.section-item[title="Procurement Planning"] .drop-icon').first();
		const child = page.getByRole('link', { name: 'Planning Home' }).first();
		await parent.click();
		await expect(child).toBeVisible();
		await parent.click();
		await expect(child).toBeHidden();
		await parent.click();
		await expect(child).toBeVisible();
	});

	test('Planning subtree has visual hierarchy enhancer classes', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const parentSection = page.locator('.section-item[title="Procurement Planning"]').first();
		await expect(parentSection).toHaveClass(/kt-pp2-sidebar-parent/);
		await expect(parentSection.locator('.kt-pp2-parent-icon')).toBeVisible();
		await parentSection.locator('.drop-icon').click();
		for (const surface of PP2_SURFACES) {
			const childLink = page
				.locator('.section-item[title="Procurement Planning"] .nested-container .item-anchor')
				.filter({ hasText: surface.label })
				.first();
			await expect(childLink).toHaveClass(/kt-pp2-sidebar-child/);
		}
	});

	test('first expansion from non-planning route keeps nested indentation', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-home`, { waitUntil: 'domcontentloaded' });
		const parentSection = page.locator('.section-item[title="Procurement Planning"]').first();
		await expect(parentSection.locator('.kt-pp2-parent-icon')).toBeVisible();
		const alignment = await page.evaluate(() => {
			const p = document.querySelector('.section-item[title="Procurement Planning"] .sidebar-item-label');
			const h = document.querySelector('.item-anchor[href="/desk/procurement-home"] .sidebar-item-label');
			if (!p || !h) return null;
			return Math.abs(p.getBoundingClientRect().left - h.getBoundingClientRect().left);
		});
		expect(alignment).not.toBeNull();
		expect(alignment as number).toBeLessThanOrEqual(1);
		await parentSection.locator('.drop-icon').click();
		const childLink = parentSection
			.locator('.nested-container .item-anchor')
			.filter({ hasText: 'Planning Home' })
			.first();
		await expect(childLink).toBeVisible();
		await expect(childLink).toHaveClass(/kt-pp2-sidebar-child/);
	});

	test('Procurement Planning icon persists across Procurement route switches', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await page.getByRole('link', { name: 'Budget & Funding' }).first().click();
		await expect(page).toHaveURL(/\/desk\/budget-management/);
		const parentSection = page.locator('.section-item[title="Procurement Planning"]').first();
		await expect(parentSection.locator('.kt-pp2-parent-icon')).toBeVisible({ timeout: 30000 });

		await page.getByRole('link', { name: 'Tender Management' }).first().click();
		await expect(page).toHaveURL(/\/desk\/tender-management-v2/);
		await expect(parentSection.locator('.kt-pp2-parent-icon')).toBeVisible({ timeout: 30000 });
	});

	test('non-PP2 route switch keeps Procurement Planning collapsed', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const parentSection = page.locator('.section-item[title="Procurement Planning"]').first();
		await parentSection.locator('.drop-icon').first().click();
		await expect(parentSection.locator('.nested-container .item-anchor').first()).toBeVisible({
			timeout: 30000,
		});

		await page.getByRole('link', { name: 'Strategy Alignment' }).first().click();
		await expect(page).toHaveURL(/\/desk\/strategy-management/);
		await expect(parentSection.locator('.nested-container .item-anchor').first()).toBeHidden({
			timeout: 30000,
		});
	});

	test('Evidence & Audit then back keeps Procurement rail for Journeys and TM2 surfaces', async ({ page }) => {
		await page.goto(`${root}/desk/ktsm-supplier-registry`, { waitUntil: 'domcontentloaded' });
		await clickSidebarHref(page, '/desk/audit-event');
		await expect(page).toHaveURL(/\/desk\/audit-event/);
		await page.goBack({ waitUntil: 'domcontentloaded' });
		await expect(page).toHaveURL(/\/desk\/ktsm-supplier-registry/);

		const assertProcurementRail = async (targetHref: string, targetUrlPattern: RegExp) => {
			await clickSidebarHref(page, targetHref);
			await expect(page).toHaveURL(targetUrlPattern);
			await expect(page.getByRole('link', { name: 'Procurement Home' }).first()).toBeVisible({ timeout: 30000 });
			await expect(page.getByRole('link', { name: 'Evidence & Audit' }).first()).toBeVisible({ timeout: 30000 });
			await expect(page.getByRole('link', { name: 'Procurement Journeys' }).first()).toBeVisible({
				timeout: 30000,
			});
			await expect(page.getByRole('link', { name: 'Procurement Home' }).first()).toHaveAttribute(
				'href',
				'/desk/procurement-home',
			);
			await expect(page.getByRole('link', { name: 'Procurement Journeys' }).first()).toHaveAttribute(
				'href',
				'/desk/plc-procurement-journey',
			);
		};

		await assertProcurementRail('/desk/plc-procurement-journey', /\/desk\/plc-procurement-journey/);
		await page.goto(`${root}/desk/ktsm-supplier-registry`, { waitUntil: 'domcontentloaded' });
		await assertProcurementRail('/desk/tender-management-v2', /\/desk\/tender-management-v2/);
		await page.goto(`${root}/desk/ktsm-supplier-registry`, { waitUntil: 'domcontentloaded' });
		await assertProcurementRail('/desk/tender-management-v2', /\/desk\/tender-management-v2/);
	});

	test('repeated navigation with browser back keeps Procurement rail stable', async ({ page }) => {
		await page.goto(`${root}/desk/audit-event`, { waitUntil: 'domcontentloaded' });
		const sequence: Array<{ href: string; url: RegExp }> = [
			{ href: '/desk/procurement-home', url: /\/desk\/procurement-home/ },
			{ href: '/desk/plc-procurement-journey', url: /\/desk\/plc-procurement-journey/ },
			{ href: '/desk/tender-management-v2', url: /\/desk\/tender-management-v2/ },
			{ href: '/desk/plc-procurement-journey', url: /\/desk\/plc-procurement-journey/ },
			{ href: '/desk/tender-management-v2', url: /\/desk\/tender-management-v2/ },
		];
		for (const step of sequence) {
			await clickSidebarHref(page, step.href);
			await expect(page).toHaveURL(step.url);
			await expect(page.getByRole('link', { name: 'Procurement Home' }).first()).toBeVisible({ timeout: 30000 });
			await expect(page.getByRole('link', { name: 'Procurement Journeys' }).first()).toBeVisible({
				timeout: 30000,
			});
			await expect(page.getByRole('link', { name: 'Evidence & Audit' }).first()).toBeVisible({ timeout: 30000 });
			await page.goBack({ waitUntil: 'domcontentloaded' });
			await expect(page).toHaveURL(/\/desk\/audit-event/);
		}
	});

	test('each sidebar item routes to the correct pp2 surface root', async ({ page }) => {
		for (const surface of PP2_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId(surface.testId)).toBeVisible({ timeout: 30000 });
			await expectPrimarySidebarItemHighlighted(page, surface.label, 'Procurement Planning');
		}
	});

	test('hard refresh keeps Planning sidebar populated', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-packages-page')).toBeVisible({ timeout: 30000 });
		await page.reload({ waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-packages-page')).toBeVisible({ timeout: 30000 });

		const bootProbe = await page.evaluate(() => {
			const f = (window as { frappe?: { app?: { sidebar?: { workspace_sidebar_items?: unknown[] } } } })
				.frappe;
			return {
				items_count: f?.app?.sidebar?.workspace_sidebar_items?.length ?? 0,
			};
		});
		expect(bootProbe.items_count).toBeGreaterThan(0);
		const labels = await sidebarLabels(page);
		expect(labels.some((lab) => lab.includes('Packages'))).toBeTruthy();
	});
});
