import { test, expect } from '@playwright/test';

import { loginAsAdministrator, loginAsProcurementPlanner } from '../../helpers/auth';

/**
 * Planning Hub wiring smoke — PP4 live data layer.
 * Requires WORKS master seed (PLAN-MOH-2026) on kentender.midas.com.
 */

async function openPlanningHub(page: Parameters<typeof test>[1] extends never ? never : Parameters<Parameters<typeof test>[1]>[0]['page']) {
	await page.goto('/app/planning-hub', { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('kt-pph-hub')).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('kt-pph-active-plan-title')).not.toHaveText('', { timeout: 20_000 });
}

test('Planning Hub mounts and loads live hero title', async ({ page }) => {
	await loginAsAdministrator(page);
	await openPlanningHub(page);

	await expect(page.getByTestId('kt-pph-toolbar-title')).toHaveText('Plan Management');
	await expect(page.getByTestId('kt-pph-page-title')).toHaveText('Procurement Planning Hub');
	const heroTitle = page.getByTestId('kt-pph-active-plan-title');
	await expect(heroTitle).not.toHaveText('Ministry of Health Procurement Plan');
	const titleText = (await heroTitle.textContent())?.trim() || '';
	expect(titleText.length).toBeGreaterThan(0);
});

test('Planning Hub ledger shows plan code badge rows', async ({ page }) => {
	await loginAsAdministrator(page);
	await openPlanningHub(page);

	const rows = page.getByTestId('kt-pph-row');
	await expect(rows.first()).toBeVisible({ timeout: 20_000 });
	const ref = rows.first().locator('.kt-pph-plan__ref');
	await expect(ref).toBeVisible();
	const refText = (await ref.textContent())?.trim() || '';
	expect(refText.startsWith('PLAN-')).toBeTruthy();
});

test('Planning Hub Open Workbench navigates to procurement planning', async ({ page }) => {
	await loginAsAdministrator(page);
	await openPlanningHub(page);

	const openBtn = page.getByTestId('kt-pph-open-workbench');
	await expect(openBtn).toBeVisible({ timeout: 10_000 });
	await openBtn.click();
	await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/, { timeout: 30_000 });
	await expect(page.getByTestId('pp4-workbench')).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('kt-pph-hub')).toHaveCount(0);
});

test('Planning Hub hides Close Plan for procurement planner', async ({ page }) => {
	await loginAsProcurementPlanner(page);
	await openPlanningHub(page);
	await expect(page.getByTestId('kt-pph-close-plan')).toHaveCount(0);
});
