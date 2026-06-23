/**
 * P3-009 — Workbench Recently Released queue shows released/tender-created items.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';
import {
	mockActivePlan,
	mockWorkbenchItems,
	pp3Root,
	prepareWorkbenchSession,
} from '../../helpers/pp3Workbench';

const FIXTURE = {
	ok: true,
	queue: 'recently_released',
	total: 1,
	start: 0,
	limit: 20,
	items: [
		{
			work_item_id: 'recently_released:PKG-MOH-2026-001',
			title: 'District Hospital Renovation Works Package',
			subtitle: 'Released to Tender Management',
			state_label: 'Released',
			next_action_label: 'Open Tender',
			underlying_object_type: 'procurement_package',
		},
	],
};

const EMPTY_FIXTURE = { ...FIXTURE, total: 0, items: [] };

test.describe('P3-009 Recently Released queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await prepareWorkbenchSession(page);
	});

	test('shows recently released items with Open Tender action', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=recently_released`, {
			waitUntil: 'domcontentloaded',
		});

		const tab = page.getByTestId('pp3-queue-recently-released');
		await expect(tab).toBeVisible({ timeout: 30000 });
		await expect(tab).toHaveClass(/is-active/);

		const row = page.getByTestId('pp3-work-item-row').first();
		await expect(row.getByTestId('pp3-work-item-next-action')).toHaveText('Open Tender');
		await expect(row.getByTestId('pp3-work-item-state')).toHaveText('Released');
		await expect(row).toContainText('Released to Tender Management');

		await page.screenshot({ path: 'artifacts/p3-009-recently-released-queue.png', fullPage: true });
	});

	test('shows Recently Released empty state when nothing was released recently', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, EMPTY_FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=recently_released`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp3-work-list')).toContainText(
			'No packages have been released recently.',
		);
	});
});
