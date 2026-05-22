import { test, expect } from '@playwright/test';

import {
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
	seedHierarchyForContract,
} from '../../helpers/strategyBuilder';

test('Structure overview shows seeded hierarchy levels', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await seedHierarchyForContract(page, plan);
	await openStrategyBuilder(page, plan);

	await page.getByTestId('structure-subtab-overview').click();
	const overview = page.getByTestId('structure-overview');
	await expect(overview).toContainText('Healthcare Delivery');
	await expect(overview).toContainText('District Works');
	await expect(overview).toContainText('Increase rural access');
	await expect(overview).toContainText('Expand district facilities');
});
