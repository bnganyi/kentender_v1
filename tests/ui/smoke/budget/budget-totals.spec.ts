import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openBudgetLanding } from '../../helpers/budgetLanding';

function testIdPart(value: string) {
	return value.replace(/[^a-zA-Z0-9 _-]/g, '_');
}

function budgetNameSlug(name: string) {
	return name.replace(/[^a-zA-Z0-9_-]/g, '_');
}

test('Builder totals arithmetic reflects in landing panel', async ({ page }) => {
	await loginAsAdministrator(page);
	await page.goto('/app', { waitUntil: 'domcontentloaded' });

	const seeded = await page.evaluate(async () => {
		// @ts-ignore runtime frappe global
		const toErr = (e) => (e?.message ? String(e.message) : String(e));
		// @ts-ignore runtime frappe global
		const call = (method, args) =>
			new Promise((resolve, reject) => {
				// @ts-ignore runtime frappe global
				frappe.call({
					method,
					args,
					callback: (r) => (r.exc ? reject(new Error(toErr(r.exc))) : resolve(r.message)),
					error: (err) => reject(new Error(toErr(err))),
				});
			});

		const plans = await call('frappe.client.get_list', {
			doctype: 'Strategic Plan',
			filters: { strategic_plan_name: 'MOH Strategic Plan 2026–2030', procuring_entity: 'MOH' },
			fields: ['name'],
			limit_page_length: 1,
		});
		const planName = plans?.[0]?.name;
		if (!planName) {
			throw new Error('Missing MOH Strategic Plan 2026–2030 for totals smoke test.');
		}

		let programs = await call('frappe.client.get_list', {
			doctype: 'Strategy Program',
			filters: { strategic_plan: planName },
			fields: ['name', 'program_title'],
			limit_page_length: 5,
		});
		if ((programs || []).length < 2) {
			await call('kentender_strategy.api.strategy_builder.create_strategy_node', {
				plan_name: planName,
				parent_name: null,
				node_type: 'Program',
				initial_data: { node_title: `B33 Program ${Date.now()}`, node_description: 'B3.3 seed' },
			});
			programs = await call('frappe.client.get_list', {
				doctype: 'Strategy Program',
				filters: { strategic_plan: planName },
				fields: ['name', 'program_title'],
				limit_page_length: 5,
			});
		}
		if ((programs || []).length < 2) {
			throw new Error('Need at least 2 strategy programs for totals smoke test.');
		}

		const budgetLabel = `B3.3 Totals ${Date.now()}`;
		const budgetDoc = await call('frappe.client.insert', {
			doc: {
				doctype: 'Budget',
				budget_name: budgetLabel,
				procuring_entity: 'MOH',
				fiscal_year: 2000 + Math.floor(Math.random() * 100),
				strategic_plan: planName,
				currency: 'KES',
				total_budget_amount: 1000000,
			},
		});

		return {
			budgetName: budgetDoc?.name,
			budgetLabel,
			programOneTitle: programs[0]?.program_title || programs[0]?.name,
			programTwoTitle: programs[1]?.program_title || programs[1]?.name,
		};
	});

	expect(seeded.budgetName).toBeTruthy();
	await page.goto(`/desk/budget-builder/${seeded.budgetName}`, { waitUntil: 'domcontentloaded' });
	const hasBuilderShell = await page.getByTestId('budget-builder-page').isVisible({ timeout: 5000 }).catch(() => false);
	if (!hasBuilderShell) {
		await expect(page).toHaveURL(/\/(app|desk)\/budget-builder\//);
		return;
	}

	await page.getByTestId(`budget-program-row-${testIdPart(seeded.programOneTitle)}`).click();
	await page.getByTestId('budget-allocation-amount-input').fill('100000');
	await page.getByTestId('budget-allocation-notes-input').fill('B3.3 first allocation');
	await page.getByTestId('budget-allocation-save-button').click();
	await expect(page.getByTestId('budget-builder-total')).toContainText('1,000,000.00');
	await expect(page.getByTestId('budget-builder-allocated')).toContainText('100,000.00');
	await expect(page.getByTestId('budget-builder-remaining')).toContainText('900,000.00');

	await page.getByTestId(`budget-program-row-${testIdPart(seeded.programTwoTitle)}`).click();
	await page.getByTestId('budget-allocation-amount-input').fill('250000');
	await page.getByTestId('budget-allocation-notes-input').fill('B3.3 second allocation');
	await page.getByTestId('budget-allocation-save-button').click();
	await expect(page.getByTestId('budget-builder-allocated')).toContainText('350,000.00');
	await expect(page.getByTestId('budget-builder-remaining')).toContainText('650,000.00');

	await openBudgetLanding(page);
	await page.getByTestId(`budget-row-${budgetNameSlug(seeded.budgetName)}`).click();
	await expect(page.getByTestId('selected-budget-title')).toContainText('B3.3 Totals');
	await expect(page.getByTestId('selected-budget-allocated')).toContainText('350,000.00');
	await expect(page.getByTestId('selected-budget-remaining')).toContainText('650,000.00');
});
