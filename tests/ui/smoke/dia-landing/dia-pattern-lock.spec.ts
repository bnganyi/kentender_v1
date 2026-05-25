import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';
import {
	expectDetailTabCycleNoLoadingFlash,
	expectNoLoadingFlash,
	expectPrimaryTabsUseHierarchyContract,
	expectRowSwitchKeepsDetailShell,
	expectStatusFiltersUseHierarchyContract,
} from '../../helpers/workspacePatternContract';

test.describe('DIA workspace pattern lock', () => {
	test('list rail keeps header separated from scrollable list', async ({ page }) => {
		await loginAsAdministrator(page);
		await openDIALanding(page);

		await expect(page.getByTestId('dia-list-head')).toBeVisible();
		const list = page.getByTestId('dia-list');
		const listVisible = await list.isVisible().catch(() => false);
		if (listVisible) {
			await expect(list).toHaveCSS('overflow-y', 'scroll');
			const isScrollable = await list.evaluate((el) => el.scrollHeight > el.clientHeight);
			if (isScrollable) {
				await list.evaluate((el) => {
					el.scrollTop = 120;
				});
				await expect.poll(async () => list.evaluate((el) => el.scrollTop)).toBeGreaterThan(0);
			}
		}
	});

	test('detail pane uses hero and status chips without KPI row', async ({ page }) => {
		await loginAsAdministrator(page);
		await openDIALanding(page);

		await expect(page.getByTestId('dia-status-chips')).toBeVisible();
		await expect(page.getByTestId('dia-kpi-row')).toHaveCount(0);
		await expect(page.getByTestId('dia-work-tabs')).toHaveCount(0);

		const panel = page.getByTestId('selected-demand-panel');
		if (await panel.isVisible().catch(() => false)) {
			await expect(page.getByTestId('selected-demand-title')).toBeVisible();
			await expect(page.getByTestId('dia-next-step')).toBeVisible();
		}
	});

	test('detail tabs do not flash loading placeholders when switching', async ({ page }) => {
		await loginAsAdministrator(page);
		await openDIALanding(page);

		const list = page.getByTestId('dia-list');
		if (!(await list.isVisible().catch(() => false))) {
			test.skip(true, 'Requires seeded demand rows in list.');
		}

		const firstRow = page.locator('[data-testid^="dia-row-"]').first();
		await firstRow.click();
		await expect(page.getByTestId('selected-demand-panel')).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId('dia-landing-page')).toHaveAttribute(
			'data-dia-workbench-build',
			'20260523-flicker4',
		);

		await list.evaluate((el) => {
			el.scrollTop = el.scrollHeight;
		});
		const before = await list.evaluate((el) => el.scrollTop);

		const detailTabs = [
			{ tabTestId: 'dia-tab-overview', panelTestId: 'dia-tab-panel-overview' },
			{ tabTestId: 'dia-tab-items', panelTestId: 'dia-tab-panel-items' },
			{ tabTestId: 'dia-tab-review', panelTestId: 'dia-tab-panel-review' },
			{ tabTestId: 'dia-tab-planning', panelTestId: 'dia-tab-panel-planning' },
			{ tabTestId: 'dia-tab-audit', panelTestId: 'dia-tab-panel-audit' },
		];
		const loadingTestIds = [
			'dia-review-loading',
			'dia-audit-loading',
			'dia-detail-planning-handoff-loading',
			'dia-detail-loading',
		];

		// Warm each tab once (first visit may load async data).
		for (const tab of detailTabs) {
			await page.getByTestId(tab.tabTestId).click();
			await expect(page.getByTestId(tab.panelTestId)).toBeVisible({ timeout: 30_000 });
			if (tab.tabTestId === 'dia-tab-review') {
				await expect(page.getByTestId('dia-review-panel')).toBeVisible({ timeout: 30_000 });
			}
			if (tab.tabTestId === 'dia-tab-planning') {
				await expect(page.getByTestId('dia-planning-panel')).toBeVisible({ timeout: 30_000 });
			}
			if (tab.tabTestId === 'dia-tab-audit') {
				await expect(page.getByTestId('dia-audit-panel')).toBeVisible({ timeout: 30_000 });
			}
		}

		// Second pass: switching must not re-show loading placeholders.
		await expectDetailTabCycleNoLoadingFlash(page, detailTabs, loadingTestIds);

		const after = await list.evaluate((el) => el.scrollTop);
		if (before > 0) {
			expect(Math.abs(after - before)).toBeLessThanOrEqual(2);
		}

		const auditPanel = page.getByTestId('dia-tab-panel-audit');
		await page.getByTestId('dia-tab-audit').click();
		await expectNoLoadingFlash(auditPanel, page.getByText('Loading audit'));

		await expectRowSwitchKeepsDetailShell(page, {
			rowSelector: '[data-testid^="dia-row-"]',
			detailRootSelector: '#kt-dia-detail-root',
			detailPanelSelector: '[data-testid="selected-demand-panel"]',
			stableNodeSelector: '.kt-dia-tab-panel-wrap',
			loadingSelectors: ['[data-testid="dia-detail-loading"]'],
		});
	});

	test('status filters and primary tabs respect hierarchy contracts', async ({ page }) => {
		await loginAsAdministrator(page);
		await openDIALanding(page);

		await expectStatusFiltersUseHierarchyContract(page.getByTestId('dia-status-chips'), {
			allTestId: 'dia-tab-all',
			sampleZeroTestId: 'dia-tab-draft',
		});

		const firstRow = page.locator('[data-testid^="dia-row-"]').first();
		if ((await firstRow.count()) === 0) {
			test.skip(true, 'Requires seeded demand rows for detail tabs.');
		}
		await firstRow.click();
		await expect(page.getByTestId('selected-demand-panel')).toBeVisible({ timeout: 30_000 });
		await page.getByTestId('dia-tab-overview').click();
		await expectPrimaryTabsUseHierarchyContract(page, { tabPrefix: 'dia-tab-' });
	});

	test('edit drawer suppresses sidebar chrome and keeps justification fields compact', async ({ page }) => {
		await loginAsAdministrator(page);
		await openDIALanding(page);

		await page.getByTestId('dia-tab-draft').click();
		const rows = page.locator('[data-testid^="dia-row-"]');
		const rowCount = await rows.count();
		expect(rowCount).toBeGreaterThan(0);

		let openedDrawer = false;
		for (let i = 0; i < Math.min(rowCount, 8); i++) {
			await rows.nth(i).click();
			await expect(page.getByTestId('selected-demand-panel')).toBeVisible({ timeout: 30_000 });
			const editBtn = page.getByTestId('dia-action-edit').first();
			if ((await editBtn.count()) === 0) {
				continue;
			}
			const label = ((await editBtn.textContent()) || '').toLowerCase();
			if (!label.includes('edit')) {
				continue;
			}
			await editBtn.click();
			openedDrawer = true;
			break;
		}
		expect(openedDrawer).toBeTruthy();

		const frameLocator = page.getByTestId('dia-demand-drawer-frame');
		await expect(frameLocator).toBeVisible({ timeout: 30_000 });
		const frameHandle = await frameLocator.elementHandle();
		const frame = frameHandle ? await frameHandle.contentFrame() : null;
		expect(frame).toBeTruthy();
		if (!frame) {
			return;
		}
		await frame.waitForSelector('body.kt-dia-embedded-drawer-form', { timeout: 30_000 });
		await frame.waitForSelector('[data-testid="dia-builder-step-justification"]', { timeout: 30_000 });
		await frame.click('[data-testid="dia-builder-step-justification"]');
		await frame.waitForSelector('[data-fieldname="beneficiary_summary"] textarea', {
			timeout: 30_000,
			state: 'attached',
		});
		await frame.waitForSelector('[data-fieldname="specification_summary"] textarea', {
			timeout: 30_000,
			state: 'attached',
		});

		const state = await frame.evaluate(() => {
			const sidebar = document.querySelector('.desk-sidebar, .layout-side-section, .form-sidebar');
			const just =
				document.querySelector('[data-testid="dia-field-justification"] textarea') ||
				document.querySelector('[data-fieldname="beneficiary_summary"] textarea');
			const spec =
				document.querySelector('[data-testid="dia-field-specification-summary"] textarea') ||
				document.querySelector('[data-fieldname="specification_summary"] textarea');
			const justCss = just ? getComputedStyle(just) : null;
			const specCss = spec ? getComputedStyle(spec) : null;
			const justRect = just ? just.getBoundingClientRect() : null;
			const specRect = spec ? spec.getBoundingClientRect() : null;
			return {
				sidebarHidden: sidebar
					? getComputedStyle(sidebar).display === 'none' || getComputedStyle(sidebar).visibility === 'hidden'
					: true,
				hasJustification: !!just,
				hasSpecification: !!spec,
				justMin: justCss ? parseFloat(justCss.minHeight || '0') : 0,
				specMin: specCss ? parseFloat(specCss.minHeight || '0') : 0,
				justMax: justCss ? parseFloat(justCss.maxHeight || '0') : 0,
				specMax: specCss ? parseFloat(specCss.maxHeight || '0') : 0,
				justHeight: justRect ? justRect.height : 0,
				specHeight: specRect ? specRect.height : 0,
			};
		});

		expect(state.sidebarHidden).toBeTruthy();
		expect(state.hasJustification).toBeTruthy();
		expect(state.hasSpecification).toBeTruthy();
		// compact defaults: about 4.5rem min and 8rem max (allowing small theme variance)
		if (state.justMin > 0 && state.specMin > 0) {
			expect(state.justMin).toBeGreaterThanOrEqual(64);
			expect(state.specMin).toBeGreaterThanOrEqual(64);
			expect(state.justMax).toBeLessThanOrEqual(132);
			expect(state.specMax).toBeLessThanOrEqual(132);
		} else if (state.justHeight > 0 && state.specHeight > 0) {
			expect(state.justHeight).toBeLessThanOrEqual(220);
			expect(state.specHeight).toBeLessThanOrEqual(260);
		} else {
			test.skip(true, 'Justification textarea metrics unavailable in current form render mode.');
		}
	});
});
