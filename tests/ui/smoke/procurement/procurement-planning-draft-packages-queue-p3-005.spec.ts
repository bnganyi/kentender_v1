/**
 * P3-005 — Workbench Draft Packages queue shows draft packages.
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
	queue: 'draft_packages',
	total: 1,
	start: 0,
	limit: 20,
	items: [
		{
			work_item_id: 'draft_packages:PKG-MOH-2026-001',
			title: 'District Hospital Renovation Works Package',
			subtitle: 'Works · Open Tender · 98,000,000 KES',
			state_label: 'Draft package',
			next_action_label: 'Open Package',
			underlying_object_type: 'procurement_package',
		},
	],
};

const EMPTY_FIXTURE = { ...FIXTURE, total: 0, items: [] };

test.describe('P3-005 Draft Packages queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await prepareWorkbenchSession(page);
	});

	test('shows draft package rows with Open Package when tab selected', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=draft_packages`, {
			waitUntil: 'domcontentloaded',
		});

		const tab = page.getByTestId('pp3-queue-draft-packages');
		await expect(tab).toBeVisible({ timeout: 30000 });
		await expect(tab).toHaveClass(/is-active/);

		const row = page.getByTestId('pp3-work-item-row').first();
		await expect(row.getByTestId('pp3-work-item-title')).toHaveText(
			'District Hospital Renovation Works Package',
		);
		await expect(row.getByTestId('pp3-work-item-state')).toHaveText('Draft package');
		await expect(row.getByTestId('pp3-work-item-next-action')).toHaveText('Open Package');
		expect(await row.innerText()).not.toContain('PKG-MOH-2026-001');

		await page.screenshot({ path: 'artifacts/p3-005-draft-packages-queue.png', fullPage: true });
	});

	test('shows Draft Packages empty state when no drafts are waiting', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, EMPTY_FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=draft_packages`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp3-work-list')).toContainText('No draft packages are waiting.');
	});
});
