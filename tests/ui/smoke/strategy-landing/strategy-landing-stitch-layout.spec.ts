/**
 * Strategy Management — Stitch layout contract
 * (docs/misc/strategy_management_home_code.html).
 *
 * Main column (header → KPIs → plan cards) + right rail (Lineage Activity).
 * Fake Stitch left nav must not appear inside the hub shell.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

test.describe('Strategy Portfolio Hub — Stitch layout (misc design)', () => {
	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1440, height: 900 });
		await loginAsAdministrator(page);
	});

	test('canvas is main + aside; Create New Plan uses primary blue', async ({ page }) => {
		test.setTimeout(120_000);
		await openStrategyLanding(page);

		await expect(page.getByTestId('strategy-portfolio-hub')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('sph-canvas')).toBeVisible();
		await expect(page.getByTestId('sph-main')).toBeVisible();
		await expect(page.getByTestId('sph-aside')).toBeVisible();

		const hub = page.getByTestId('strategy-portfolio-hub');
		await expect(hub).not.toContainText('Financial Catalyst');
		await expect(hub).not.toContainText('John Doe');

		const geometry = await page.evaluate(() => {
			const canvas = document.querySelector('[data-testid="sph-canvas"]') as HTMLElement | null;
			const main = document.querySelector('[data-testid="sph-main"]') as HTMLElement | null;
			const aside = document.querySelector('[data-testid="sph-aside"]') as HTMLElement | null;
			const metrics = document.querySelector('[data-testid="sph-metrics-grid"]') as HTMLElement | null;
			const plans = document.querySelector('[data-testid="sph-plans-grid"]') as HTMLElement | null;
			const btn = document.querySelector('[data-testid="sph-create-plan-btn"]') as HTMLElement | null;
			if (!canvas || !main || !aside || !metrics || !plans || !btn) return null;
			const mainRect = main.getBoundingClientRect();
			const asideRect = aside.getBoundingClientRect();
			const style = window.getComputedStyle(btn);
			return {
				asideRightOfMain: asideRect.left >= mainRect.right - 2,
				metricsTop: Math.round(metrics.getBoundingClientRect().top),
				plansTop: Math.round(plans.getBoundingClientRect().top),
				btnBg: style.backgroundColor,
			};
		});
		expect(geometry).not.toBeNull();
		expect(geometry!.asideRightOfMain).toBe(true);
		expect(geometry!.plansTop).toBeGreaterThanOrEqual(geometry!.metricsTop);

		/* primary #00346f → rgb(0, 52, 111) */
		expect(geometry!.btnBg.replace(/\s/g, '')).toMatch(/rgb\(0,\s*52,\s*111\)/);

		await expect(page.locator('.body-sidebar .sidebar-header .header-title')).toHaveText(
			/^\s*Procurement\s*$/i,
		);
	});
});
