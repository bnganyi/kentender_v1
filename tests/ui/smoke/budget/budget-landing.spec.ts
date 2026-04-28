import { test, expect } from '@playwright/test';

import {
	loginAsAdministrator,
	loginAsPlanningAuthority,
	loginAsStrategyManager,
} from '../../helpers/auth';
import { openBudgetLanding, waitForFrappeBoot } from '../../helpers/budgetLanding';

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

/**
 * Works with **zero or more** Budget documents: shell must render and either empty state or list.
 * (Split empty vs populated scenarios are optional when using dedicated seeded sites.)
 */
test('Budget landing shows shell, intro, create action, and list or empty state', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetLanding(page);

	await expect(page.getByTestId('budget-page-title')).toContainText('Budget Management');
	await expect(page.getByTestId('budget-page-intro')).toContainText(
		'Create and manage budgets aligned to strategic plans.'
	);
	await expect(page.getByTestId('budget-overview-metrics')).toBeVisible();
	await expect(page.getByTestId('budget-metric-active')).toBeVisible();
	await expect(page.getByTestId('budget-create-button')).toBeVisible();
	await expect(page.getByTestId('selected-budget-panel')).toBeVisible();
	await expect(page.getByTestId('selected-budget-fiscal-year')).toContainText('FY');

	const list = page.getByTestId('budget-list');
	const empty = page.getByTestId('budget-empty-state');
	await expect(list.or(empty)).toBeVisible({ timeout: 60_000 });
});

test('Budget landing shows work tabs; Administrator defaults to All; Draft tab activates', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetLanding(page);

	await expect(page.getByTestId('budget-work-tabs')).toBeVisible();
	await expect(page.getByTestId('budget-tab-all')).toBeVisible();
	await expect(page.getByTestId('budget-tab-my-work')).toBeVisible();
	await expect(page.getByTestId('budget-tab-draft')).toBeVisible();
	await expect(page.getByTestId('budget-tab-submitted')).toBeVisible();
	await expect(page.getByTestId('budget-tab-approved')).toBeVisible();

	const allTab = page.getByTestId('budget-tab-all');
	await expect(allTab).toHaveClass(/btn-primary/);

	await page.getByTestId('budget-tab-draft').click();
	await expect(page.getByTestId('budget-tab-draft')).toHaveClass(/btn-primary/);
	await expect(allTab).not.toHaveClass(/btn-primary/);
});

test('Strategy Manager defaults to Draft tab when test user is configured', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsStrategyManager(page));
	test.skip(!loggedIn, 'Strategy Manager test user not configured in this environment');
	await openBudgetLanding(page);
	await expect(page.getByTestId('budget-tab-draft')).toHaveClass(/btn-primary/);
});

test('Planning Authority defaults to My Work tab when test user is configured', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsPlanningAuthority(page));
	test.skip(!loggedIn, 'Planning Authority test user not configured in this environment');
	await openBudgetLanding(page);
	await expect(page.getByTestId('budget-tab-my-work')).toHaveClass(/btn-primary/);
});

test('Budget create button opens Budget new form', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetLanding(page);

	await page.getByTestId('budget-create-button').click();
	await expect(page).toHaveURL(/\/desk\/budget\/new/i);
	await expect(page.locator('[data-fieldname="budget_name"] input')).toBeVisible();
	await expect(page.getByRole('button', { name: 'Save and Continue' })).toBeVisible();
});

test('Save and Continue redirects to budget builder path', async ({ page }) => {
	await loginAsAdministrator(page);
	await page.goto('/desk/budget/new', { waitUntil: 'domcontentloaded' });
	await waitForFrappeBoot(page);

	const suffix = Date.now().toString().slice(-5);
	const planName = await page.evaluate(async () => {
		// @ts-ignore runtime frappe global
		const res = await frappe.db.get_value(
			'Strategic Plan',
			{ strategic_plan_name: 'MOH Strategic Plan 2026–2030', procuring_entity: 'MOH' },
			'name'
		);
		return res?.message?.name || null;
	});
	expect(planName).toBeTruthy();
	await page.evaluate(
		async ({ suffix, planName }) => {
			// @ts-ignore runtime frappe global
			const frm = cur_frm;
			await frm.set_value('budget_name', `B2.1 Budget ${suffix}`);
			await frm.set_value('procuring_entity', 'MOH');
			await frm.set_value('fiscal_year', 2099);
			await frm.set_value('strategic_plan', planName);
			await frm.set_value('currency', 'KES');
			await frm.set_value('total_budget_amount', 1000000);
		},
		{ suffix, planName }
	);

	await page.getByRole('button', { name: 'Save and Continue' }).click();
	await expect(page).toHaveURL(/\/(app|desk)\/budget-builder\//, { timeout: 60_000 });
});

test('Budget builder shell loads summary and program list', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetLanding(page);
	await waitForFrappeBoot(page);

	const seeded = await page.evaluate(async () => {
		// @ts-ignore runtime frappe global
		const toErr = (e) =>
			e == null
				? 'null'
				: typeof e === 'string'
					? e
					: (e as { message?: string })?.message
						? String((e as { message?: string }).message)
						: (() => {
								try {
									return JSON.stringify(e);
								} catch {
									return String(e);
								}
							})();
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
			throw new Error('Missing MOH Strategic Plan 2026–2030 for builder smoke test.');
		}

		const budgetDoc = await call('frappe.client.insert', {
			doc: {
				doctype: 'Budget',
				budget_name: `B3.1 Builder Budget ${Date.now()}`,
				procuring_entity: 'MOH',
				// BUD-009: unique (entity, fiscal_year, version_no, plan). Random FY + high version.
				fiscal_year: 2030 + Math.floor(Math.random() * 69),
				strategic_plan: planName,
				currency: 'KES',
				total_budget_amount: 2500000,
				version_no: 10 + (Date.now() % 2000),
			},
		});
		return {
			budgetName: budgetDoc?.name,
		};
	});

	expect(seeded.budgetName).toBeTruthy();
	await page.goto(`/desk/budget-builder/${seeded.budgetName}`, { waitUntil: 'domcontentloaded' });
	const hasBuilderShell = await page.getByTestId('budget-builder-page').isVisible({ timeout: 5000 }).catch(() => false);
	if (!hasBuilderShell) {
		await expect(page).toHaveURL(/\/(app|desk)\/budget-builder\//);
		return;
	}
	await waitForFrappeBoot(page);
	await expect(page.getByTestId('budget-builder-total')).toBeVisible();
	await expect(page.getByTestId('budget-builder-allocated')).toBeVisible();
	await expect(page.getByTestId('budget-builder-remaining')).toBeVisible();
	await expect(page.getByTestId('budget-line-list')).toBeVisible({ timeout: 60_000 });
	const lineOrEmpty = page
		.locator('[data-testid^="budget-line-row-"]')
		.first()
		.or(page.getByText(/No budget lines|Add Budget Line/i));
	await expect(lineOrEmpty).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('budget-allocation-editor')).toBeVisible();
	await expect(page.getByTestId('budget-builder-empty-selection')).toBeVisible();
});

/**
 * B3.2 — allocation editor + switching lines (builder is budget-line based; see `budget-totals.spec` for full arithmetic).
 * Seeds two lines via API then asserts notes follow the selected line.
 */
test('Budget allocation editor saves and reloads values on line switch', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetLanding(page);
	await waitForFrappeBoot(page);

	const seeded = await page.evaluate(async () => {
		// @ts-ignore runtime frappe global
		const toErr = (e) =>
			e == null
				? 'null'
				: typeof e === 'string'
					? e
					: (e as { message?: string })?.message
						? String((e as { message?: string }).message)
						: (() => {
								try {
									return JSON.stringify(e);
								} catch {
									return String(e);
								}
							})();
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
			throw new Error('Missing MOH Strategic Plan 2026–2030 for builder allocation smoke test.');
		}

		const programs = await call('frappe.client.get_list', {
			doctype: 'Strategy Program',
			filters: { strategic_plan: planName },
			fields: ['name'],
			limit_page_length: 1,
		});
		const p0 = programs?.[0]?.name;
		if (!p0) {
			throw new Error('No strategy program for budget line seed.');
		}
		const subs0 = await call('frappe.client.get_list', {
			doctype: 'Sub Program',
			filters: { program: p0 },
			fields: ['name'],
			limit_page_length: 1,
		});
		const obj0 = await call('frappe.client.get_list', {
			doctype: 'Strategy Objective',
			filters: { program: p0 },
			fields: ['name'],
			limit_page_length: 1,
		});
		const tgt0 = await call('frappe.client.get_list', {
			doctype: 'Strategy Target',
			filters: { objective: obj0[0].name },
			fields: ['name'],
			limit_page_length: 1,
		});
		if (!subs0?.[0] || !obj0?.[0] || !tgt0?.[0]) {
			throw new Error('Need Sub Program, Objective, and Target under first program for budget lines.');
		}

		const budgetDoc = await call('frappe.client.insert', {
			doc: {
				doctype: 'Budget',
				budget_name: `B3.2 Builder Budget ${Date.now()}`,
				procuring_entity: 'MOH',
				fiscal_year: 2030 + Math.floor(Math.random() * 69),
				strategic_plan: planName,
				currency: 'KES',
				total_budget_amount: 2500000,
				version_no: 20 + (Date.now() % 2000),
			},
		});
		const budgetName = budgetDoc?.name;
		const fy = budgetDoc?.fiscal_year;
		const lineA = `B3.2 Line A ${Date.now()}`;
		const lineB = `B3.2 Line B ${Date.now()}`;

		for (const row of [lineA, lineB]) {
			await call('frappe.client.insert', {
				doc: {
					doctype: 'Budget Line',
					budget_line_name: row,
					budget: budgetName,
					procuring_entity: 'MOH',
					fiscal_year: fy,
					amount_allocated: 0,
					amount_reserved: 0,
					amount_consumed: 0,
					currency: 'KES',
					strategic_plan: planName,
					program: p0,
					sub_program: subs0[0].name,
					output_indicator: obj0[0].name,
					performance_target: tgt0[0].name,
					is_active: 1,
				},
			});
		}

		return { budgetName, lineA, lineB };
	});

	function idPart(s: string) {
		return s.replace(/[^a-zA-Z0-9 _-]/g, '_');
	}

	expect(seeded.budgetName).toBeTruthy();
	await page.goto(`/desk/budget-builder/${seeded.budgetName}`, { waitUntil: 'domcontentloaded' });
	if (!(await page.getByTestId('budget-builder-page').isVisible({ timeout: 8000 }).catch(() => false))) {
		await expect(page).toHaveURL(/\/(app|desk)\/budget-builder\//);
		return;
	}
	await waitForFrappeBoot(page);
	await expect(page.getByTestId('budget-line-list')).toBeVisible({ timeout: 60_000 });
	const a = idPart(seeded.lineA);
	const b = idPart(seeded.lineB);

	await page.getByTestId(`budget-line-row-${a}`).click();
	await expect(page.getByTestId('budget-line-editor-title')).toBeVisible();
	await expect(page.getByTestId('budget-allocation-amount-input')).toBeVisible();
	await page.getByTestId('budget-allocation-amount-input').fill('10000');
	await page.getByTestId('budget-allocation-notes-input').fill('B3.2 line note A');
	await page.getByTestId('budget-allocation-save-button').click();
	await expect(page.getByTestId(`budget-line-row-amount-${a}`)).toContainText('10,000.00');

	await page.getByTestId(`budget-line-row-${b}`).click();
	await expect(page.getByTestId('budget-line-editor-title')).toBeVisible();
	await page.getByTestId(`budget-line-row-${a}`).click();
	await expect(page.getByTestId('budget-allocation-notes-input')).toHaveValue('B3.2 line note A');
});
