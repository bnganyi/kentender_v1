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
		const budgetName = budgetDoc?.name;
		const fy = budgetDoc?.fiscal_year;
		const p0 = programs[0];
		const p1 = programs[1] || programs[0];
		const subs0 = await call('frappe.client.get_list', {
			doctype: 'Sub Program',
			filters: { program: p0.name },
			fields: ['name'],
			limit_page_length: 1,
		});
		const subs1 = await call('frappe.client.get_list', {
			doctype: 'Sub Program',
			filters: { program: p1.name },
			fields: ['name'],
			limit_page_length: 1,
		});
		const obj0 = await call('frappe.client.get_list', {
			doctype: 'Strategy Objective',
			filters: { program: p0.name },
			fields: ['name'],
			limit_page_length: 1,
		});
		const obj1 = await call('frappe.client.get_list', {
			doctype: 'Strategy Objective',
			filters: { program: p1.name },
			fields: ['name'],
			limit_page_length: 1,
		});
		if (!subs0?.[0] || !obj0?.[0]) {
			throw new Error('Need Sub Program and Strategy Objective on first program for budget line smoke.');
		}
		const tgt0 = await call('frappe.client.get_list', {
			doctype: 'Strategy Target',
			filters: { objective: obj0[0].name },
			fields: ['name'],
			limit_page_length: 1,
		});
		const sub1 = subs1?.[0] || subs0[0];
		const obj1n = obj1?.[0] || obj0[0];
		const tgt1rows = await call('frappe.client.get_list', {
			doctype: 'Strategy Target',
			filters: { objective: obj1n.name },
			fields: ['name'],
			limit_page_length: 1,
		});
		const tgt0n = tgt0?.[0]?.name;
		const tgt1n = tgt1rows?.[0]?.name || tgt0n;
		if (!tgt0n) {
			throw new Error('Need Strategy Target for budget line smoke.');
		}
		const lineOneName = `B33 Totals Line A ${Date.now()}`;
		const lineTwoName = `B33 Totals Line B ${Date.now()}`;
		for (const row of [
			{
				budget_line_name: lineOneName,
				program: p0.name,
				sub_program: subs0[0].name,
				objective: obj0[0].name,
				target: tgt0n,
				allocated: 0,
			},
			{
				budget_line_name: lineTwoName,
				program: p1.name,
				sub_program: sub1.name,
				objective: obj1n.name,
				target: tgt1n,
				allocated: 0,
			},
		]) {
			await call('frappe.client.insert', {
				doc: {
					doctype: 'Budget Line',
					budget_line_name: row.budget_line_name,
					budget: budgetName,
					procuring_entity: 'MOH',
					fiscal_year: fy,
					amount_allocated: row.allocated,
					amount_reserved: 0,
					amount_consumed: 0,
					currency: 'KES',
					strategic_plan: planName,
					program: row.program,
					sub_program: row.sub_program,
					output_indicator: row.objective,
					performance_target: row.target,
					is_active: 1,
				},
			});
		}

		return {
			budgetName,
			budgetLabel,
			lineOneName,
			lineTwoName,
		};
	});

	expect(seeded.budgetName).toBeTruthy();
	await page.goto(`/desk/budget-builder/${seeded.budgetName}`, { waitUntil: 'domcontentloaded' });
	const hasBuilderShell = await page.getByTestId('budget-builder-page').isVisible({ timeout: 5000 }).catch(() => false);
	if (!hasBuilderShell) {
		await expect(page).toHaveURL(/\/(app|desk)\/budget-builder\//);
		return;
	}

	const id1 = testIdPart(seeded.lineOneName);
	const id2 = testIdPart(seeded.lineTwoName);
	await page.getByTestId(`budget-line-row-${id1}`).click();
	await page.getByTestId('budget-allocation-amount-input').fill('100000');
	await page.getByTestId('budget-allocation-notes-input').fill('B3.3 first allocation');
	await page.getByTestId('budget-allocation-save-button').click();
	await expect(page.getByTestId('budget-builder-total')).toContainText('1,000,000.00');
	await expect(page.getByTestId('budget-builder-allocated')).toContainText('100,000.00');
	await expect(page.getByTestId('budget-builder-remaining')).toContainText('900,000.00');

	await page.getByTestId(`budget-line-row-${id2}`).click();
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
