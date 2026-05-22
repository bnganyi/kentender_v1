import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
	submitNewNodeDialog,
} from '../../helpers/strategyBuilder';
import { clickStructureSubtab } from '../../helpers/strategyWorkbench';

test('Structure editing uses dialogs and stays on workspace', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await clickStructureSubtab(page, 'structure-subtab-programs', 'structure-add-program');
	await page.getByTestId('structure-add-program').click();
	await submitNewNodeDialog(page, { title: 'Healthcare Delivery' }, /New Program/i);

	await expect(page).toHaveURL(/strategy-management/);
	await expect(page.url()).not.toMatch(/strategy-node/);
	await expect(page.getByTestId('strategy-structure-panel')).toBeVisible();
});
