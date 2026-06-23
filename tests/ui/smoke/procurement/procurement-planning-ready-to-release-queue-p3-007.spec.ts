/**
 * P3-007 — Workbench Ready to Release queue shows packages ready to release.
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
	queue: 'ready_release',
	total: 1,
	start: 0,
	limit: 20,
	items: [
		{
			work_item_id: 'ready_release:PKG-MOH-2026-001',
			title: 'District Hospital Renovation Works Package',
			subtitle: 'Works · Open Tender · 98,000,000 KES',
			state_label: 'Ready for Release',
			next_action_label: 'Release to Tender',
			underlying_object_type: 'procurement_package',
		},
	],
};

const EMPTY_FIXTURE = { ...FIXTURE, total: 0, items: [] };

test.describe('P3-007 Ready to Release queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await prepareWorkbenchSession(page);
	});

	test('shows releasable packages with Release to Tender action', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=ready_to_release`, {
			waitUntil: 'domcontentloaded',
		});

		const tab = page.getByTestId('pp3-queue-ready-release');
		await expect(tab).toBeVisible({ timeout: 30000 });
		await expect(tab).toHaveClass(/is-active/);

		const row = page.getByTestId('pp3-work-item-row').first();
		await expect(row.getByTestId('pp3-work-item-next-action')).toHaveText('Release to Tender');
		await expect(row.getByTestId('pp3-work-item-state')).toHaveText('Ready for Release');

		await page.screenshot({ path: 'artifacts/p3-007-ready-to-release-queue.png', fullPage: true });
	});

	test('shows Ready to Release empty state when nothing is releasable', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, EMPTY_FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=ready_to_release`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp3-work-list')).toContainText('No packages are ready for release.');
	});
});
