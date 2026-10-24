import { expect, test } from '@playwright/test';
import { pickRecord } from '../../helpers/picker';
import { as, world } from './helpers';

// The Contracts list draws the design's five filters (the Project Owner, 17 October 2026: "Do not deviate from the design"; the design then put them all in one row): Search, Status, Source, Responsible
// person and Managing unit in the one bar. A person or a unit chosen from a list that can grow is the shared record picker, and it offers only the people and units of contracts the reader may read.
// Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
test.describe('The contracts list filters', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(300_000);

	test('The five filters share one row, and Responsible person and Managing unit are the shared picker and narrow the list', async ({ browser }) => {
		await as(browser, 'charles', async (page) => {
			await page.goto('/app/home');
			await page.locator('.body-sidebar').getByText('Contract Management', { exact: true }).click();
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace', { timeout: 30_000 });
			await page.getByTestId('cm-view-1').click(); // All contracts
			const rows = page.locator('[data-testid^="cm-row-"]');
			await expect(rows.first()).toBeVisible({ timeout: 15_000 });

			// the design: all five filters in the one bar, Search wide, and no "Filters" disclosure
			const bar = ['cm-filter-search', 'cm-filter-status', 'cm-filter-source', '#cm-filter-responsible', '#cm-filter-unit'];
			for (const f of bar) await expect(f.startsWith('#') ? page.locator(f) : page.getByTestId(f)).toBeVisible();
			await expect(page.getByText('Filters', { exact: true })).toHaveCount(0);
			const tops = await page.locator('.kt-filter-bar').first().locator('.field').evaluateAll((els) => els.map((e) => Math.round(e.getBoundingClientRect().top)));
			expect(tops, 'Search, Status, Source, Responsible person and Managing unit').toHaveLength(5);
			expect(new Set(tops).size, 'the five filters share one row').toBe(1);

			// a person: the list narrows to the contracts whose next action they hold
			const all = await rows.count();
			const person = await pickRecord(page, '#cm-filter-responsible', 'Charles');
			expect(person).toContain('Charles');
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-refreshing', 'false');
			const mine = await rows.count();
			expect(mine, 'at least one contract is theirs, and not necessarily all').toBeGreaterThan(0);
			expect(mine).toBeLessThanOrEqual(all);

			// the pickers start on "All people" and "All units", as the design's selects do; a unit narrows the list again, and "All units" lifts it
			await expect(page.locator('#cm-filter-unit')).toHaveValue('All units');
			const clear = (id: string) => page.locator('.field', { has: page.locator(id) }).getByTestId('kt-picker-clear');
			const list = page.locator('[data-testid="kt-picker-list"]');
			await clear('#cm-filter-unit').click(); // a field with a choice reopens its list through Clear; the list then offers "All units" first
			await expect(list).toHaveAttribute('aria-busy', 'false', { timeout: 30_000 });
			await list.locator('[role="option"][aria-disabled="false"]').filter({ hasNotText: 'All units' }).first().click();
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-refreshing', 'false');
			expect(await rows.count()).toBeGreaterThan(0);
			// Clear on a chosen unit or person goes back to "All units" or "All people", and the list widens again
			await clear('#cm-filter-unit').click();
			await expect(page.locator('#cm-filter-unit')).toHaveValue('All units');
			await clear('#cm-filter-responsible').click();
			await expect(page.locator('#cm-filter-responsible')).toHaveValue('All people');
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-refreshing', 'false');
			await expect.poll(async () => rows.count(), { timeout: 15_000 }).toBe(all);
		});
	});
});
