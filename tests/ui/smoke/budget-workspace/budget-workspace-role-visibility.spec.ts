import { test, expect } from '@playwright/test';

import {
	loginAsPlanningAuthority,
	loginAsRequisitioner,
	loginAsStrategyManager,
} from '../../helpers/auth';
import { desktopModuleTile, dismissOptionalDeskModals } from '../../helpers/routes';
import { budgetModule } from '../../helpers/selectors';

async function tryLogin(fn: () => Promise<void>) {
	try {
		await fn();
		return true;
	} catch (e) {
		const msg = e instanceof Error ? e.message : String(e);
		if (msg.includes('Invalid Login')) {
			return false;
		}
		throw e;
	}
}

test('Strategy Manager sees Budget module on desk home', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsStrategyManager(page));
	test.skip(!loggedIn, 'Strategy Manager test user not configured in this environment');
	await page.goto('/app');
	await page.waitForLoadState('networkidle');
	await dismissOptionalDeskModals(page);

	await expect(desktopModuleTile(page, budgetModule)).toBeVisible({
		timeout: 20_000,
	});
});

test('Planning Authority sees Budget module on desk home', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsPlanningAuthority(page));
	test.skip(!loggedIn, 'Planning Authority test user not configured in this environment');
	await page.goto('/app');
	await page.waitForLoadState('networkidle');
	await dismissOptionalDeskModals(page);

	await expect(desktopModuleTile(page, budgetModule)).toBeVisible({
		timeout: 20_000,
	});
});

test('Requisitioner does not see Budget module on desk home', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsRequisitioner(page));
	test.skip(!loggedIn, 'Requisitioner test user not configured in this environment');
	await page.goto('/app');
	await page.waitForLoadState('networkidle');
	await dismissOptionalDeskModals(page);

	await expect(desktopModuleTile(page, budgetModule)).toHaveCount(0);
});
