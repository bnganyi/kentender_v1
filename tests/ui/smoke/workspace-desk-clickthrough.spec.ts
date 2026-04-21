import { test, expect } from '@playwright/test';
import { loginAsAdministrator } from '../helpers/auth';
import { openWorkspaceFromDeskLauncher } from '../helpers/routes';
import {
	budgetModule,
	budgetWorkspace,
	procurementModule,
	procurementWorkspace,
	strategyModule,
	strategyWorkspace,
} from '../helpers/selectors';

test('Strategy Management opens from module tile then sidebar (not address-bar deep link)', async ({
	page,
}) => {
	await loginAsAdministrator(page);
	await openWorkspaceFromDeskLauncher(page, strategyModule, strategyWorkspace.heading);

	await expect(page.getByText(strategyWorkspace.heading).first()).toBeVisible();
	await expect(page).toHaveURL(/\/(app|desk)\/strategy-management/);
});

test('Procurement opens from module tile then sidebar (not address-bar deep link)', async ({
	page,
}) => {
	await loginAsAdministrator(page);
	await openWorkspaceFromDeskLauncher(page, procurementModule, procurementWorkspace.heading);

	await expect(page.getByText(procurementWorkspace.heading).first()).toBeVisible();
	await expect(page).toHaveURL(/\/(app|desk)\/procurement$/);
});

test('Budget Management opens from module tile then sidebar (not address-bar deep link)', async ({
	page,
}) => {
	await loginAsAdministrator(page);
	await openWorkspaceFromDeskLauncher(page, budgetModule, budgetWorkspace.heading);

	await expect(page.getByText(budgetWorkspace.heading).first()).toBeVisible();
	await expect(page).toHaveURL(/\/(app|desk)\/budget-management/);
});