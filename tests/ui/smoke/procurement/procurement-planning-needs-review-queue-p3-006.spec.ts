/**
 * P3-006 — Workbench Needs Review queue shows packages awaiting review.
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
	queue: 'needs_review',
	total: 1,
	start: 0,
	limit: 20,
	items: [
		{
			work_item_id: 'needs_review:PKG-MOH-2026-001',
			title: 'District Hospital Renovation Works Package',
			subtitle: 'Works · Open Tender · 98,000,000 KES',
			state_label: 'In Review',
			next_action_label: 'Review Package',
			underlying_object_type: 'procurement_package',
		},
	],
};

const EMPTY_FIXTURE = { ...FIXTURE, total: 0, items: [] };

test.describe('P3-006 Needs Review queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await prepareWorkbenchSession(page);
	});

	test('shows packages awaiting review with Review Package action', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=needs_review`, {
			waitUntil: 'domcontentloaded',
		});

		const tab = page.getByTestId('pp3-queue-needs-review');
		await expect(tab).toBeVisible({ timeout: 30000 });
		await expect(tab).toHaveClass(/is-active/);

		const row = page.getByTestId('pp3-work-item-row').first();
		await expect(row.getByTestId('pp3-work-item-next-action')).toHaveText('Review Package');
		await expect(row.getByTestId('pp3-work-item-state')).toHaveText('In Review');

		await page.screenshot({ path: 'artifacts/p3-006-needs-review-queue.png', fullPage: true });
	});

	test('shows Needs Review empty state when no packages await review', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, EMPTY_FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=needs_review`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp3-work-list')).toContainText(
			'No packages are waiting for review.',
		);
	});
});
