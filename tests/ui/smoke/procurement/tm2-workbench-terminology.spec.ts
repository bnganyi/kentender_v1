/**
 * Section 11 — primary TM2 workbench surfaces use business-readable labels;
 * technical tokens stay in Legal basis / Advanced collapses.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { clickTm2TaskTab } from '../../helpers/tm2Workbench';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const SAMPLE_QUEUE_IDS = [
	'tm2-queue-ready-review',
	'tm2-queue-std-incomplete',
	'tm2-queue-draft',
] as const;

const FORBIDDEN_PRIMARY = [/Bundle current/i, /\bDSM\b/, /\bDOM\b/, /\bDEM\b/, /\bDCM\b/, /STD & Readiness/];

test.describe('TM2 workbench terminology (Section 11)', () => {
	test.setTimeout(180_000);

	test('Preparation tab shows business summary; technical checklist is collapsed', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		let opened = false;
		for (const qid of SAMPLE_QUEUE_IDS) {
			await shell.getByTestId(qid).click();
			const row = shell.getByTestId('tm2-tender-list-row').first();
			if (await row.isVisible().catch(() => false)) {
				await row.click();
				await expect(shell.getByTestId('tm2-detail-sticky')).toBeVisible({ timeout: 60_000 });
				opened = true;
				break;
			}
		}
		if (!opened) {
			test.skip(true, 'No tenders in sampled queues — cannot assert Preparation terminology.');
		}

		await clickTm2TaskTab(page, 'tm2-tab-preparation');
		const panel = shell.getByTestId('tm2-tab-panel-std-readiness');
		await expect(panel).toBeVisible({ timeout: 30_000 });

		const primaryText = await panel.evaluate((el) => {
			const clone = el.cloneNode(true) as HTMLElement;
			clone.querySelectorAll('details').forEach((node) => node.remove());
			return clone.textContent || '';
		});
		for (const pattern of FORBIDDEN_PRIMARY) {
			expect(primaryText).not.toMatch(pattern);
		}

		const legal = panel.getByTestId('tm2-preparation-legal-basis');
		await expect(legal).toBeVisible();
		await expect(legal.getByTestId('tm2-std-readiness-checklist')).toBeHidden();

		await legal.locator('summary').click();
		await expect(legal.getByTestId('tm2-std-readiness-checklist')).toBeVisible();
		await expect(legal.getByTestId('tm2-std-derived-bundle')).toBeVisible();
	});
});
