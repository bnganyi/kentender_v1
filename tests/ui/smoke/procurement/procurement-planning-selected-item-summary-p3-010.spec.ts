/**
 * P3-010 — Workbench selected item summary shows title, state, facts, blockers, next action.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';
import {
	mockActivePlan,
	mockWorkbenchItems,
	pp3Root,
	prepareWorkbenchSession,
} from '../../helpers/pp3Workbench';

const BLOCKED_FIXTURE = {
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
			primary_action: {
				label: 'Resolve Blocker',
				action: 'open_package',
				target: 'PKG-MOH-2026-001',
			},
			secondary_actions: [],
		},
	],
};

const FORBIDDEN_LEAKAGE = [/PKG-MOH-2026-001/i, /PLANINCL-/i, /technical_refs_json/i];

test.describe('P3-010 Selected item summary', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await prepareWorkbenchSession(page);
	});

	test('shows title, state, facts, blockers, and next action for selected item', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, BLOCKED_FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning?queue=blocked`, {
			waitUntil: 'domcontentloaded',
		});

		const summary = page.getByTestId('pp3-selected-work-summary');
		await expect(summary).toBeVisible({ timeout: 30000 });
		await expect(summary).toContainText('District Hospital Renovation Works Package');
		await expect(summary).toContainText('State');
		await expect(summary).toContainText('Blocked');
		await expect(summary).toContainText('Works');
		await expect(summary).toContainText('Blockers');
		await expect(summary).toContainText('Budget line not linked');
		await expect(summary).toContainText('Next');
		await expect(summary).toContainText('Resolve Blocker');

		const summaryText = await summary.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(summaryText).not.toMatch(pattern);
		}

		await page.screenshot({ path: 'artifacts/p3-010-selected-item-summary.png', fullPage: true });
	});
});
