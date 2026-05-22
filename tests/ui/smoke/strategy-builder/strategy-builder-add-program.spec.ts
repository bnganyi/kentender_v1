import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
	submitNewNodeDialog,
} from '../../helpers/strategyBuilder';
import { clickStructureSubtab } from '../../helpers/strategyWorkbench';

test('Can add Program node in workspace Structure tab', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await clickStructureSubtab(page, 'structure-subtab-programs', 'structure-add-program');
	await page.getByTestId('structure-add-program').click();
	await submitNewNodeDialog(
		page,
		{
			title: 'Healthcare Delivery',
		},
		/New Program/i,
	);

	await page.getByTestId('structure-subtab-overview').click();
	await expect(page.getByTestId('structure-overview')).toContainText('Healthcare Delivery');
	await expect(page).toHaveURL(/strategy-management/);
});
