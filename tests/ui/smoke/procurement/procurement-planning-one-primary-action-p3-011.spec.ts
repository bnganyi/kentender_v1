/**
 * P3-011 — Selected Workbench item shows exactly one visually primary action.
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
	queue: 'needs_planning',
	total: 1,
	start: 0,
	limit: 20,
	items: [
		{
			work_item_id: 'needs_planning:DEM-MOH-2026-001',
			title: 'District Hospital Renovation Works',
			subtitle: 'Works · 98,000,000 KES · Budget linked',
			state_label: 'Needs planning',
			next_action_label: 'Include in Plan',
			blockers: [],
			primary_action: { label: 'Include in Plan', action: 'include_in_plan', target: 'DEM-MOH-2026-001' },
			secondary_actions: [
				{ label: 'View Demand', action: 'view_demand', target: 'DEM-MOH-2026-001' },
				{ label: 'View Evidence', action: 'open_evidence', target: 'DEM-MOH-2026-001' },
			],
		},
	],
};

test.describe('P3-011 One primary action', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await prepareWorkbenchSession(page);
	});

	test('renders one primary button and non-primary secondary actions', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		const summary = page.getByTestId('pp3-selected-work-summary');
		await expect(summary).toBeVisible({ timeout: 30000 });

		const primary = summary.getByTestId('pp3-primary-action');
		await expect(primary).toHaveCount(1);
		await expect(primary).toHaveText('Include in Plan');
		await expect(primary).toHaveClass(/btn-primary/);

		const secondaryButtons = summary.getByTestId('pp3-secondary-actions').locator('button');
		await expect(secondaryButtons).toHaveCount(1);
		await expect(secondaryButtons.first()).toHaveClass(/btn-default/);
		await expect(secondaryButtons.first()).not.toHaveClass(/btn-primary/);

		await page.screenshot({ path: 'artifacts/p3-011-one-primary-action.png', fullPage: true });
	});
});
