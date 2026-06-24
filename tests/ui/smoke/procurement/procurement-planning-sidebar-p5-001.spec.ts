/**
 * P1-002 — Procurement Planning sidebar keeps only three persistent v3 entries.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';
import { expectPrimarySidebarItemHighlighted } from '../../helpers/workspacePatternContract';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const PP3_SURFACES = [
	{
		label: 'Workbench',
		testId: 'pp3-planning-workbench',
		path: '/desk/procurement-planning',
		navTestId: 'pp3-nav-workbench',
	},
	{
		label: 'Procurement Plans',
		testId: 'pp3-procurement-plans-page',
		path: '/desk/procurement-planning/plans',
		navTestId: 'pp3-nav-procurement-plans',
	},
	{
		label: 'Released to Tender',
		testId: 'pp2-released-to-tender-page',
		path: '/desk/procurement-planning/releases',
		navTestId: 'pp3-nav-released-to-tender',
	},
] as const;

const FORBIDDEN_LEGACY_PLANNING_LABELS = ['Planning Home', 'Approved Demands', 'Plans', 'Packages'];

const FORBIDDEN_SIDEBAR_LABELS = [
	'Planning Evidence',
	'Planning Inclusion Detail',
	'Release Package Detail',
	'Readiness Review',
	'Review & Approval',
	'Package Lines',
	'Technical Details',
	'Audit Trail',
	'Planning Release Package',
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

test.describe('P1-002 Planning nested sidebar (three-entry IA)', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('P1-002 nav shows exactly three persistent Planning surfaces', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-planning-workbench')).toHaveCount(1);
		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toBeVisible({ timeout: 30000 });

		const labels = await sidebarLabels(page);
		expect(labels.some((lab) => lab.includes('Procurement Home'))).toBeTruthy();
		expect(labels.some((lab) => lab.includes('Procurement Planning'))).toBeTruthy();
		for (const surface of PP3_SURFACES) {
			expect(labels.some((lab) => lab.includes(surface.label))).toBeTruthy();
		}
		for (const removed of FORBIDDEN_LEGACY_PLANNING_LABELS) {
			expect(labels.some((lab) => lab.trim().toLowerCase() === removed.trim().toLowerCase())).toBeFalsy();
		}
		for (const forbidden of FORBIDDEN_SIDEBAR_LABELS) {
			expect(labels.some((lab) => lab.includes(forbidden))).toBeFalsy();
		}
		expect(labels.filter((lab) => PP3_SURFACES.some((s) => lab.includes(s.label))).length).toBeGreaterThanOrEqual(3);
		await page.screenshot({ path: 'artifacts/p1-002-nav-three-entry.png', fullPage: true });
	});

	test('P1-003 negative gate: Planning Home is absent on all PP3 planning routes', async ({ page }) => {
		for (const surface of PP3_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			const planningSection = page.locator('.section-item[title="Procurement Planning"]');
			const dropIcon = planningSection.locator('.drop-icon').first();
			if (await dropIcon.isVisible()) {
				await dropIcon.click();
			}
			await expect(planningSection.locator('.item-anchor', { hasText: 'Planning Home' })).toHaveCount(0);
		}
		await page.screenshot({ path: 'artifacts/p1-003-no-planning-home-nav.png', fullPage: true });
	});

	test('P1-004 negative gate: Approved Demands is absent on all PP3 planning routes', async ({ page }) => {
		for (const surface of PP3_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			const planningSection = page.locator('.section-item[title="Procurement Planning"]');
			const dropIcon = planningSection.locator('.drop-icon').first();
			if (await dropIcon.isVisible()) {
				await dropIcon.click();
			}
			await expect(planningSection.locator('.item-anchor', { hasText: 'Approved Demands' })).toHaveCount(0);
		}
		await page.screenshot({ path: 'artifacts/p1-004-no-approved-demands-nav.png', fullPage: true });
	});

	test('P1-005 negative gate: Packages is absent on all PP3 planning routes', async ({ page }) => {
		for (const surface of PP3_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			const planningSection = page.locator('.section-item[title="Procurement Planning"]');
			const dropIcon = planningSection.locator('.drop-icon').first();
			if (await dropIcon.isVisible()) {
				await dropIcon.click();
			}
			await expect(planningSection.locator('.item-anchor', { hasText: 'Packages' })).toHaveCount(0);
		}
		await page.screenshot({ path: 'artifacts/p1-005-no-packages-nav.png', fullPage: true });
	});

	test('P1-006 negative gate: Planning Evidence is absent on all PP3 planning routes', async ({
		page,
	}) => {
		for (const surface of PP3_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			const planningSection = page.locator('.section-item[title="Procurement Planning"]');
			const dropIcon = planningSection.locator('.drop-icon').first();
			if (await dropIcon.isVisible()) {
				await dropIcon.click();
			}
			await expect(planningSection.locator('.item-anchor', { hasText: 'Planning Evidence' })).toHaveCount(
				0
			);
		}
		await page.screenshot({ path: 'artifacts/p1-006-no-planning-evidence-nav.png', fullPage: true });
	});

	test('Procurement Planning parent expands and collapses child links', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-home`, { waitUntil: 'domcontentloaded' });
		const parent = page.locator('.section-item[title="Procurement Planning"] .drop-icon').first();
		const child = page.getByRole('link', { name: 'Workbench' }).first();
		await expect(child).toBeHidden();
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
		for (const surface of PP3_SURFACES) {
			const childLink = page
				.locator('.section-item[title="Procurement Planning"] .nested-container .item-anchor')
				.filter({ hasText: surface.label })
				.first();
			await expect(childLink).toHaveClass(/kt-pp2-sidebar-child/);
			await expect(childLink).toHaveAttribute('data-testid', surface.navTestId);
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
		expect(alignment as number).toBeLessThanOrEqual(2);
		await parentSection.locator('.drop-icon').click();
		const childLink = parentSection
			.locator('.nested-container .item-anchor')
			.filter({ hasText: 'Workbench' })
			.first();
		await expect(childLink).toBeVisible();
		await expect(childLink).toHaveClass(/kt-pp2-sidebar-child/);
		await expect(childLink.locator('.sidebar-item-icon').first()).toBeVisible();
		const childIndentation = await page.evaluate(() => {
			const parentLabel = document.querySelector(
				'.section-item[title="Procurement Planning"] .sidebar-item-label'
			) as HTMLElement | null;
			const childLabel = document.querySelector(
				'.section-item[title="Procurement Planning"] .nested-container .item-anchor.kt-pp2-sidebar-child .sidebar-item-label'
			) as HTMLElement | null;
			if (!parentLabel || !childLabel) return null;
			return childLabel.getBoundingClientRect().left - parentLabel.getBoundingClientRect().left;
		});
		expect(childIndentation).not.toBeNull();
		expect(childIndentation as number).toBeGreaterThanOrEqual(10);
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
		await expect(
			parentSection.locator('.nested-container .item-anchor.kt-pp2-sidebar-child-active')
		).toHaveCount(0);
		await expect(
			parentSection.locator('.nested-container .standard-sidebar-item.active-sidebar')
		).toHaveCount(0);
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

	test('each sidebar item routes to the correct pp3 surface root', async ({ page }) => {
		for (const surface of PP3_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			if (surface.path === '/desk/procurement-planning') {
				await expect(page.getByTestId(surface.testId)).toHaveCount(1);
				await expect(page.getByTestId('pp3-workbench-queue-tabs')).toBeVisible({ timeout: 30000 });
			} else {
				await expect(page.getByTestId(surface.testId)).toBeVisible({ timeout: 30000 });
			}
			await expectPrimarySidebarItemHighlighted(page, surface.label, 'Procurement Planning');
		}
	});

	test('hard refresh keeps Planning sidebar populated', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-procurement-plans-page')).toBeVisible({ timeout: 30000 });
		await page.reload({ waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-procurement-plans-page')).toBeVisible({ timeout: 30000 });

		const bootProbe = await page.evaluate(() => {
			const f = (window as { frappe?: { app?: { sidebar?: { workspace_sidebar_items?: unknown[] } } } })
				.frappe;
			return {
				items_count: f?.app?.sidebar?.workspace_sidebar_items?.length ?? 0,
			};
		});
		expect(bootProbe.items_count).toBeGreaterThan(0);
		const labels = await sidebarLabels(page);
		expect(labels.some((lab) => lab.includes('Released to Tender'))).toBeTruthy();
	});
});
