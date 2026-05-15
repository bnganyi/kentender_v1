/**
 * Q-03 — doc 9 §21.3 item 5 (canonical `tm2_addenda.spec.ts`).
 *
 * **Addendum tab shows V1 → V2 output refs:** impact cards render ``arrow_display`` as ``prev → rev``
 * in cells ``data-testid^="tm2-ad-transition-"`` (see ``_addendum_output_transitions`` in
 * ``tm2_workbench_tender_detail.py``).
 *
 * Tries the **Addenda** queue first, then other queues where fixture tenders may carry
 * **TM2 Addendum Impact Record** transitions. Skips if no tender exposes transition rows (empty site).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from './helpers/auth';
import { dismissOptionalDeskModals } from './helpers/routes';

async function openFirstTenderRowIfAny(
	_page: import('@playwright/test').Page,
	shell: ReturnType<import('@playwright/test').Page['getByTestId']>,
): Promise<boolean> {
	const row = shell.getByTestId('tm2-tender-list-row').first();
	if (!(await row.isVisible().catch(() => false))) {
		return false;
	}
	await row.click();
	await expect(shell.getByTestId('tm2-overview-tender-summary')).toBeVisible({ timeout: 60_000 });
	return true;
}

async function tryAssertAddendaTransitions(
	shell: ReturnType<import('@playwright/test').Page['getByTestId']>,
): Promise<boolean> {
	await shell.getByTestId('tm2-tab-addenda').click();
	const panel = shell.getByTestId('tm2-tab-panel-addenda');
	await expect(panel).toBeVisible({ timeout: 30_000 });
	await expect(shell.getByTestId('tm2-ad-readonly-notice')).toBeVisible({ timeout: 30_000 });
	await expect(shell.getByTestId('tm2-ad-list-wrap')).toBeVisible({ timeout: 30_000 });

	const cells = panel.locator('[data-testid^="tm2-ad-transition-"]');
	const n = await cells.count();
	if (n === 0) {
		return false;
	}
	await expect(cells.first()).toContainText('→');
	return true;
}

test.describe('TM2 Addenda tab (Q-03 / doc 9 §21.3)', () => {
	test.setTimeout(180_000);

	const QUEUES = [
		'tm2-queue-addenda',
		'tm2-queue-published',
		'tm2-queue-ready-review',
		'tm2-queue-draft',
	] as const;

	test('§21.3 (5) — Addenda tab shows V1 → V2 output refs on impact transitions', async ({
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

		if (await openFirstTenderRowIfAny(page, shell)) {
			if (await tryAssertAddendaTransitions(shell)) {
				return;
			}
			await shell.getByTestId('tm2-tab-overview').click();
		}

		for (const qid of QUEUES) {
			const listResp = page.waitForResponse(
				(r) =>
					r.url().includes('list_workbench_tenders') &&
					r.request().method() === 'POST' &&
					r.status() === 200,
				{ timeout: 60_000 },
			);
			await shell.getByTestId(qid).click();
			await listResp;

			if (!(await openFirstTenderRowIfAny(page, shell))) {
				continue;
			}
			if (await tryAssertAddendaTransitions(shell)) {
				return;
			}
			await shell.getByTestId('tm2-tab-overview').click();
		}

		test.skip(
			true,
			'No tender with addendum impact output transitions (prev → rev) in sampled queues — seed P9-14 fixture data.',
		);
	});
});
