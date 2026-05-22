import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	submitNewNodeDialog,
} from '../../helpers/strategyBuilder';
import { openStrategyStructureTab } from '../../helpers/strategyWorkbench';

test('Can add full four-level hierarchy in workspace Structure tab', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await loginAsAdministrator(page);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyStructureTab(page);

	await page.getByTestId('structure-subtab-programs').click();
	await page.getByTestId('structure-add-program').click();
	await submitNewNodeDialog(page, { title: 'Healthcare Delivery' }, /New Program/i);

	await page.getByTestId('structure-subtab-subprograms').click();
	await page.getByTestId('structure-add-subprogram').click();
	await submitNewNodeDialog(page, { title: 'District Works' }, /New Sub-program/i);

	await page.getByTestId('structure-subtab-indicators').click();
	await page.getByTestId('structure-add-indicator').click();
	await submitNewNodeDialog(page, { title: 'Hospital readiness' }, /New Indicator/i);

	await page.getByTestId('structure-subtab-targets').click();
	await page.getByTestId('structure-add-target').click();
	await submitNewNodeDialog(
		page,
		{ title: 'Renovate hospitals', targetYear: '2026', targetValue: '1', targetUnit: 'projects' },
		/New Target/i,
	);

	await page.getByTestId('structure-subtab-overview').click();
	await expect(page.getByTestId('structure-overview')).toContainText('Healthcare Delivery');
	await expect(page.getByTestId('structure-overview')).toContainText('District Works');
});
