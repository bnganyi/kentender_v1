/**
 * P3-008 — Workbench Blocked queue shows demand/package blockers.
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
	queue: 'blocked',
	total: 1,
	start: 0,
	limit: 20,
	items: [
		{
			work_item_id: 'blocked:PKG-MOH-2026-001',
			title: 'District Hospital Renovation Works Package',
			subtitle: 'Works · Open Tender · 98,000,000 KES',
			state_label: 'Blocked',
			next_action_label: 'Resolve Blocker',
			blockers: [{ label: 'Budget line not linked', code: 'BLOCKED' }],
			underlying_object_type: 'procurement_package',
		},
	],
};

const EMPTY_FIXTURE = { ...FIXTURE, total: 0, items: [] };

test.describe('P3-008 Blocked queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await prepareWorkbenchSession(page);
	});

	test('shows blocked items with Resolve Blocker action', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=blocked`, {
			waitUntil: 'domcontentloaded',
		});

		const tab = page.getByTestId('pp3-queue-blocked');
		await expect(tab).toBeVisible({ timeout: 30000 });
		await expect(tab).toHaveClass(/is-active/);

		const row = page.getByTestId('pp3-work-item-row').first();
		await expect(row.getByTestId('pp3-work-item-next-action')).toHaveText('Resolve Blocker');
		await expect(row.getByTestId('pp3-work-item-state')).toHaveText('Blocked');

		await page.screenshot({ path: 'artifacts/p3-008-blocked-queue.png', fullPage: true });
	});

	test('shows Blocked empty state when no blockers exist', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, EMPTY_FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=blocked`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp3-work-list')).toContainText('No planning blockers found.');
	});
});
