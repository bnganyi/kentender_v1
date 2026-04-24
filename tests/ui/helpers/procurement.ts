import { expect, type Locator, type Page } from '@playwright/test';

import { openWorkspaceFromDeskLauncher } from './routes';
import { procurementModule } from './selectors';

export const procurementHomeWorkspace = {
	heading: 'Procurement Home',
	routePattern: /\/(app|desk)\/procurement-home/,
};

export const procurementPlanningWorkspace = {
	heading: 'Procurement Planning',
	routePattern: /\/(app|desk)(\/procurement-planning|\/Workspaces\/Procurement%20Planning)/,
};

export async function openProcurementWorkspaceFromModule(page: Page, workspaceLabel: string) {
	await openWorkspaceFromDeskLauncher(page, procurementModule, workspaceLabel);
}

export async function expectProcurementHomeShell(page: Page) {
	await expect(page.getByTestId('ph-landing-page')).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('ph-page-title')).toContainText(procurementHomeWorkspace.heading);
	await expect(page.getByTestId('ph-kpi-currency-context')).toBeVisible();
}

export async function expectProcurementPlanningShell(page: Page) {
	await expect(page.getByTestId('pp-page-title')).toContainText(procurementPlanningWorkspace.heading, {
		timeout: 45_000,
	});
	await expect(page.getByTestId('pp-current-plan-bar')).toBeVisible();
	await expect(page.getByTestId('pp-control-bar')).toBeVisible();
}

export async function expectSidebarProcurementHomeFirst(page: Page) {
	const home = page.getByRole('link', { name: 'Procurement Home', exact: true }).first();
	const dia = page.getByRole('link', { name: /Demand Intake/i }).first();
	const planning = page.getByRole('link', { name: 'Procurement Planning', exact: true }).first();
	await home.waitFor({ state: 'visible', timeout: 45_000 });
	await dia.waitFor({ state: 'visible', timeout: 45_000 });
	await planning.waitFor({ state: 'visible', timeout: 45_000 });
	await expect(home).toBeVisible();
	await expect(page.getByText('Settings', { exact: true }).first()).toBeVisible();

	const homeBox = await home.boundingBox();
	const diaBox = await dia.boundingBox();
	const planningBox = await planning.boundingBox();
	expect(homeBox).not.toBeNull();
	expect(diaBox).not.toBeNull();
	expect(planningBox).not.toBeNull();
	if (!homeBox || !diaBox || !planningBox) return;
	expect(homeBox.y).toBeLessThanOrEqual(diaBox.y);
	expect(homeBox.y).toBeLessThanOrEqual(planningBox.y);
}

export async function clickSidebarLink(page: Page, label: string | RegExp): Promise<Locator> {
	const link = page.getByRole('link', { name: label }).first();
	await link.waitFor({ state: 'visible', timeout: 45_000 });
	await link.click();
	await page.waitForLoadState('domcontentloaded');
	return link;
}
