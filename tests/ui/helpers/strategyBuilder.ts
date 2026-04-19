import { expect, Page, TestInfo } from '@playwright/test';

import { loginAsAdministrator } from './auth';

export const TEST_PLAN_NAME = 'TEST-SP-2026';

/** Unique Strategic Plan name per Playwright worker to avoid parallel test races. */
export function isolatedPlanName(testInfo: TestInfo, base: string = TEST_PLAN_NAME): string {
	return `${base}-w${testInfo.parallelIndex}`;
}

/** Click a tree row by the visible title substring (avoids hidden form fields with same text). */
export function treeNodeButton(page: Page, titleSubstring: string | RegExp) {
	return page.getByTestId('strategy-tree-pane').getByRole('button', { name: titleSubstring }).first();
}

export async function submitNewNodeDialog(
	page: Page,
	opts: {
		title: string;
		description?: string;
		targetYear?: string;
		targetValue?: string;
		targetUnit?: string;
	},
	/** Match Strategy Builder dialog title (Program / Objective / Target). */
	expectedHeading: RegExp,
) {
	await expect(page.getByRole('heading', { level: 4, name: expectedHeading })).toBeVisible({
		timeout: 20_000,
	});
	const d = page
		.locator('.modal.show')
		.filter({ has: page.getByRole('heading', { level: 4, name: expectedHeading }) });
	await expect(d).toBeVisible();
	const titleInput = d
		.locator(
			'[data-fieldname="node_title"] input, .form-group[data-fieldname="node_title"] input, .frappe-control[data-fieldname="node_title"] input',
		)
		.first();
	await titleInput.fill(opts.title);
	if (opts.description !== undefined) {
		await d
			.locator('[data-fieldname="node_description"] textarea, .form-group[data-fieldname="node_description"] textarea')
			.fill(opts.description);
	}
	const isTargetDialog =
		opts.targetYear !== undefined || opts.targetValue !== undefined || opts.targetUnit !== undefined;
	if (isTargetDialog) {
		const mt = d.locator(
			'[data-fieldname="measurement_type"] select, .form-group[data-fieldname="measurement_type"] select',
		);
		if ((await mt.count()) > 0) {
			await mt.selectOption('Numeric');
		}
		const pt = d.locator(
			'[data-fieldname="target_period_type"] select, .form-group[data-fieldname="target_period_type"] select',
		);
		if ((await pt.count()) > 0) {
			await pt.selectOption('Annual');
		}
		const yearInput = d.locator(
			'[data-fieldname="target_year"] input, .form-group[data-fieldname="target_year"] input',
		);
		if ((await yearInput.count()) > 0) {
			await yearInput.fill(opts.targetYear ?? String(new Date().getFullYear()));
		}
	} else if (opts.targetYear !== undefined) {
		const yearInput = d.locator(
			'[data-fieldname="target_year"] input, .form-group[data-fieldname="target_year"] input',
		);
		if ((await yearInput.count()) > 0) {
			await yearInput.fill(opts.targetYear);
		}
	}
	if (opts.targetValue !== undefined) {
		await d
			.locator('[data-fieldname="target_value"] input, .form-group[data-fieldname="target_value"] input')
			.fill(opts.targetValue);
	}
	if (opts.targetUnit !== undefined) {
		await d.locator('[data-fieldname="target_unit"] input, .form-group[data-fieldname="target_unit"] input').fill(opts.targetUnit);
	}
	const primary = d.locator('.modal-footer button.btn-primary').first();
	await Promise.all([
		page.waitForResponse(
			(r) =>
				r.url().includes('kentender_strategy.api.strategy_builder.create_strategy_node') &&
				r.request().method() === 'POST' &&
				r.ok(),
			{ timeout: 60_000 },
		),
		primary.click(),
	]);
	// Wait for this dialog to close (another .modal.show may exist underneath).
	await expect(d).toBeHidden({ timeout: 30_000 });
}

/** Remove all typed strategy rows for a plan (Target → Objective → Program). */
export async function clearStrategyNodes(page: Page, planName: string = TEST_PLAN_NAME) {
	await page.evaluate(async (plan: string) => {
		function toErr(e: unknown): Error {
			if (e instanceof Error) {
				return e;
			}
			if (e && typeof e === 'object') {
				const x = e as { message?: unknown; exc?: unknown };
				if (x.message != null) {
					return new Error(String(x.message));
				}
				if (x.exc != null) {
					return new Error(String(x.exc));
				}
			}
			try {
				return new Error(JSON.stringify(e));
			} catch {
				return new Error(String(e));
			}
		}

		const call = (method: string, args: Record<string, unknown>) =>
			new Promise<unknown>((resolve, reject) => {
				// @ts-expect-error desk global
				frappe.call({
					method,
					args,
					callback: (r: { exc?: unknown; message?: unknown }) => {
						if (r.exc) {
							reject(toErr(r.exc));
						} else {
							resolve(r.message);
						}
					},
					error: (err: unknown) => reject(toErr(err)),
				});
			});

		const delNode = (name: string) =>
			call('kentender_strategy.api.strategy_builder.delete_strategy_node', { node_name: name });

		try {
			const targets = (await call('frappe.client.get_list', {
				doctype: 'Strategy Target',
				filters: [['strategic_plan', '=', plan]],
				fields: ['name'],
				limit_page_length: 500,
			})) as { name: string }[];
			for (const t of targets) {
				await delNode(t.name);
			}
			const objectives = (await call('frappe.client.get_list', {
				doctype: 'Strategy Objective',
				filters: [['strategic_plan', '=', plan]],
				fields: ['name'],
				limit_page_length: 500,
			})) as { name: string }[];
			for (const o of objectives) {
				await delNode(o.name);
			}
			const programs = (await call('frappe.client.get_list', {
				doctype: 'Strategy Program',
				filters: [['strategic_plan', '=', plan]],
				fields: ['name'],
				limit_page_length: 500,
			})) as { name: string }[];
			for (const p of programs) {
				await delNode(p.name);
			}
		} catch (e: unknown) {
			const msg = e instanceof Error ? e.message : String(e);
			throw new Error(`clearStrategyNodes: ${msg}`);
		}
	}, planName);
}

/**
 * Opens the Strategy Builder Desk page for a Strategic Plan `name` (document id).
 * Uses `/app/...` (same route shape as `/desk/...` after Frappe strips the prefix).
 *
 * Smoke tests log in as Administrator (System Manager). The Strategy Builder Page must grant
 * the same roles as real strategy users (e.g. Planning Authority); otherwise getpage can deny
 * the page script and the main area stays blank while the shell sidebar still renders.
 */
export async function openStrategyBuilder(page: Page, planName: string) {
	await page.goto(`/app/strategy-builder/${planName}`, { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 30_000 });
	// Shell can load while the page script fails permission or boot races; require the tree UI.
	await expect(page.getByTestId('strategy-tree-pane')).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('add-program-button')).toBeVisible({ timeout: 30_000 });
}

/**
 * Ensures a Strategic Plan with the given document name exists (insert + rename).
 * Safe to call multiple times.
 */
export async function ensureTestStrategicPlan(page: Page, planName: string = TEST_PLAN_NAME) {
	await loginAsAdministrator(page);
	await page.goto('/app');
	await page.waitForLoadState('domcontentloaded');

	await page.evaluate(async (name: string) => {
		function toErr(e: unknown): Error {
			if (e instanceof Error) {
				return e;
			}
			if (e && typeof e === 'object') {
				const x = e as { message?: unknown; exc?: unknown };
				if (x.message != null) {
					return new Error(String(x.message));
				}
				if (x.exc != null) {
					return new Error(String(x.exc));
				}
			}
			try {
				return new Error(JSON.stringify(e));
			} catch {
				return new Error(String(e));
			}
		}

		const getList = (filters: unknown[]) =>
			new Promise<unknown>((resolve, reject) => {
				// @ts-expect-error desk global
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Strategic Plan',
						filters,
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: unknown; exc?: unknown }) => {
						if (r.exc) {
							reject(toErr(r.exc));
						} else {
							resolve(r.message);
						}
					},
					error: (err: unknown) => reject(toErr(err)),
				});
			});

		const lst = await getList([['name', '=', name]]);
		const rows = Array.isArray(lst) ? lst : [];
		if (rows.length) {
			return;
		}

		const company =
			(await new Promise<string | null>((resolve, reject) => {
				// @ts-expect-error desk global
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Company',
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: { name?: string }[]; exc?: unknown }) => {
						if (r.exc) {
							reject(toErr(r.exc));
						} else {
							resolve(r.message?.[0]?.name ?? null);
						}
					},
					error: (err: unknown) => reject(toErr(err)),
				});
			})) || null;
		if (!company) {
			throw new Error('No Company found — create a Company before UI tests.');
		}

		const ins = await new Promise<{ message?: { name?: string }; docs?: { name: string }[] }>(
			(resolve, reject) => {
				// @ts-expect-error desk global
				frappe.call({
					method: 'frappe.client.insert',
					args: {
						doc: {
							doctype: 'Strategic Plan',
							strategic_plan_name: 'Test Strategic Plan 2026–2030',
							procuring_entity: company,
							start_year: 2026,
							end_year: 2030,
							status: 'Draft',
							version_no: 1,
							is_current_version: 1,
							description: 'Playwright seed',
						},
					},
					callback: (r: { message?: { name?: string }; docs?: { name: string }[]; exc?: unknown }) => {
						if (r.exc) {
							reject(toErr(r.exc));
						} else {
							resolve(r);
						}
					},
					error: (err: unknown) => reject(toErr(err)),
				});
			},
		);
		const oldName = ins.docs?.[0]?.name ?? (ins.message as { name?: string })?.name;
		if (!oldName) {
			throw new Error('insert Strategic Plan failed');
		}
		await new Promise<void>((resolve, reject) => {
			// @ts-expect-error desk global
			frappe.call({
				method: 'frappe.client.rename_doc',
				args: {
					doctype: 'Strategic Plan',
					old_name: oldName,
					new_name: name,
				},
				callback: (r: { exc?: unknown }) => {
					if (r.exc) {
						reject(toErr(r.exc));
					} else {
						resolve();
					}
				},
				error: (err: unknown) => reject(toErr(err)),
			});
		});
	}, planName);
}

/**
 * Creates a Strategic Plan with a specific visible `strategic_plan_name` (for workspace list tests).
 * Renames the document to `docName` after insert. Caller must already be logged in on Desk.
 */
export async function ensureStrategicPlanForWorkspace(
	page: Page,
	opts: { docName: string; strategic_plan_name: string },
) {
	await page.goto('/app');
	await page.waitForLoadState('domcontentloaded');

	await page.evaluate(async (o: { docName: string; strategic_plan_name: string }) => {
		function toErr(e: unknown): Error {
			if (e instanceof Error) {
				return e;
			}
			if (e && typeof e === 'object') {
				const x = e as { message?: unknown; exc?: unknown };
				if (x.message != null) {
					return new Error(String(x.message));
				}
				if (x.exc != null) {
					return new Error(String(x.exc));
				}
			}
			try {
				return new Error(JSON.stringify(e));
			} catch {
				return new Error(String(e));
			}
		}

		const getList = (filters: unknown[]) =>
			new Promise<unknown>((resolve, reject) => {
				// @ts-expect-error desk global
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Strategic Plan',
						filters,
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: unknown; exc?: unknown }) => {
						if (r.exc) {
							reject(toErr(r.exc));
						} else {
							resolve(r.message);
						}
					},
					error: (err: unknown) => reject(toErr(err)),
				});
			});

		const lst = await getList([['name', '=', o.docName]]);
		const rows = Array.isArray(lst) ? lst : [];
		if (rows.length) {
			const cur = await new Promise<string | null>((resolve, reject) => {
				// @ts-expect-error desk global
				frappe.call({
					method: 'frappe.client.get_value',
					args: {
						doctype: 'Strategic Plan',
						fieldname: 'strategic_plan_name',
						filters: { name: o.docName },
					},
					callback: (r: { message?: { strategic_plan_name?: string }; exc?: unknown }) => {
						if (r.exc) {
							reject(toErr(r.exc));
						} else {
							resolve(r.message?.strategic_plan_name ?? null);
						}
					},
					error: (err: unknown) => reject(toErr(err)),
				});
			});
			if (cur !== o.strategic_plan_name) {
				await new Promise<void>((resolve, reject) => {
					// @ts-expect-error desk global
					frappe.call({
						method: 'frappe.client.set_value',
						args: {
							doctype: 'Strategic Plan',
							name: o.docName,
							fieldname: 'strategic_plan_name',
							value: o.strategic_plan_name,
						},
						callback: (r: { exc?: unknown }) => {
							if (r.exc) {
								reject(toErr(r.exc));
							} else {
								resolve();
							}
						},
						error: (err: unknown) => reject(toErr(err)),
					});
				});
			}
			return;
		}

		const company =
			(await new Promise<string | null>((resolve, reject) => {
				// @ts-expect-error desk global
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Company',
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: { name?: string }[]; exc?: unknown }) => {
						if (r.exc) {
							reject(toErr(r.exc));
						} else {
							resolve(r.message?.[0]?.name ?? null);
						}
					},
					error: (err: unknown) => reject(toErr(err)),
				});
			})) || null;
		if (!company) {
			throw new Error('No Company found — create a Company before UI tests.');
		}

		const ins = await new Promise<{ message?: { name?: string }; docs?: { name: string }[] }>(
			(resolve, reject) => {
				// @ts-expect-error desk global
				frappe.call({
					method: 'frappe.client.insert',
					args: {
						doc: {
							doctype: 'Strategic Plan',
							strategic_plan_name: o.strategic_plan_name,
							procuring_entity: company,
							start_year: 2026,
							end_year: 2030,
							status: 'Draft',
							version_no: 1,
							is_current_version: 1,
							description: 'Playwright workspace seed',
						},
					},
					callback: (r: { message?: { name?: string }; docs?: { name: string }[]; exc?: unknown }) => {
						if (r.exc) {
							reject(toErr(r.exc));
						} else {
							resolve(r);
						}
					},
					error: (err: unknown) => reject(toErr(err)),
				});
			},
		);
		const oldName = ins.docs?.[0]?.name ?? (ins.message as { name?: string })?.name;
		if (!oldName) {
			throw new Error('insert Strategic Plan failed');
		}
		await new Promise<void>((resolve, reject) => {
			// @ts-expect-error desk global
			frappe.call({
				method: 'frappe.client.rename_doc',
				args: {
					doctype: 'Strategic Plan',
					old_name: oldName,
					new_name: o.docName,
				},
				callback: (r: { exc?: unknown }) => {
					if (r.exc) {
						reject(toErr(r.exc));
					} else {
						resolve();
					}
				},
				error: (err: unknown) => reject(toErr(err)),
			});
		});
	}, opts);
}

/** Seed Program → Objective → Target for selection / navigation tests (clears existing nodes first). */
export async function seedHierarchyForContract(page: Page, planName: string = TEST_PLAN_NAME) {
	await clearStrategyNodes(page, planName);
	await page.evaluate(async (plan: string) => {
		function toErr(e: unknown): Error {
			if (e instanceof Error) {
				return e;
			}
			if (e && typeof e === 'object') {
				const x = e as { message?: unknown; exc?: unknown };
				if (x.message != null) {
					return new Error(String(x.message));
				}
				if (x.exc != null) {
					return new Error(String(x.exc));
				}
			}
			try {
				return new Error(JSON.stringify(e));
			} catch {
				return new Error(String(e));
			}
		}

		const callMethod = (method: string, args: Record<string, unknown>) =>
			new Promise<unknown>((resolve, reject) => {
				// @ts-expect-error desk global
				frappe.call({
					method,
					args,
					callback: (r: { exc?: unknown; message?: unknown }) => {
						if (r.exc) {
							reject(toErr(r.exc));
						} else {
							resolve(r.message);
						}
					},
					error: (err: unknown) => reject(toErr(err)),
				});
			});

		const pr = (await callMethod('kentender_strategy.api.strategy_builder.create_strategy_node', {
			plan_name: plan,
			parent_name: null,
			node_type: 'Program',
			initial_data: {
				node_title: 'Healthcare Delivery',
				node_description: 'Top-level program',
			},
		})) as { name: string };

		const ob = (await callMethod('kentender_strategy.api.strategy_builder.create_strategy_node', {
			plan_name: plan,
			parent_name: pr.name,
			node_type: 'Objective',
			initial_data: {
				node_title: 'Increase rural access',
				node_description: 'Improve services in rural areas',
			},
		})) as { name: string };

		await callMethod('kentender_strategy.api.strategy_builder.create_strategy_node', {
			plan_name: plan,
			parent_name: ob.name,
			node_type: 'Target',
			initial_data: {
				node_title: 'Expand district facilities',
				node_description: '',
				measurement_type: 'Numeric',
				target_period_type: 'Annual',
				target_year: 2026,
				target_value: 25,
				target_unit: 'Facilities',
			},
		});
	}, planName);
}
