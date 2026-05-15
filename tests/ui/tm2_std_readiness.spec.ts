/**
 * Q-02 — doc 9 §21.3 items 3–4 (canonical `tm2_std_readiness.spec.ts`).
 *
 * 3. STD readiness tab shows Bundle / DSM / DOM / DEM / DCM derived rows (`tm2-std-derived-*`).
 * 4. When workbench detail exposes a DEM gap (``dem_missing_block``), the STD tab shows
 *    ``tm2-std-dem-blocker-code`` **DEM_MISSING_OR_STALE** (doc 8 / P9-10).
 *
 * Item 4 scans **Ready for Publication Review**, **STD Incomplete**, then **Draft** queues — a readiness
 * row is usually required for the blocker to render (``STD Instance Incomplete`` alone may not).
 * Skips if no tender surfaces the blocker (empty / fully-green fixture site).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from './helpers/auth';
import { dismissOptionalDeskModals } from './helpers/routes';

const DERIVED_IDS = [
	'tm2-std-derived-bundle',
	'tm2-std-derived-dsm',
	'tm2-std-derived-dom',
	'tm2-std-derived-dem',
	'tm2-std-derived-dcm',
] as const;

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

async function openFirstTenderRowFromQueues(
	page: import('@playwright/test').Page,
	shell: ReturnType<import('@playwright/test').Page['getByTestId']>,
	queueTestIds: readonly string[],
): Promise<boolean> {
	for (const qid of queueTestIds) {
		const listResp = page.waitForResponse(
			(r) =>
				r.url().includes('list_workbench_tenders') &&
				r.request().method() === 'POST' &&
				r.status() === 200,
			{ timeout: 60_000 },
		);
		await shell.getByTestId(qid).click();
		await listResp;
		if (await openFirstTenderRowIfAny(page, shell)) {
			return true;
		}
	}
	return false;
}

test.describe('TM2 STD readiness tab (Q-02 / doc 9 §21.3)', () => {
	test.setTimeout(180_000);

	const SAMPLE_QUEUE_IDS = [
		'tm2-queue-ready-review',
		'tm2-queue-std-incomplete',
		'tm2-queue-draft',
	] as const;

	test('§21.3 (3) — STD & Readiness tab lists Bundle, DSM, DOM, DEM, DCM derived rows', async ({
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

		const opened =
			(await openFirstTenderRowIfAny(page, shell)) ||
			(await openFirstTenderRowFromQueues(page, shell, SAMPLE_QUEUE_IDS));
		if (!opened) {
			test.skip(true, 'No tenders in default or sampled queues — cannot assert STD readiness derived rows.');
		}

		await shell.getByTestId('tm2-tab-std-readiness').click();
		await expect(shell.getByTestId('tm2-tab-panel-std-readiness')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-std-binding-block')).toBeVisible({ timeout: 30_000 });

		const derived = shell.getByTestId('tm2-std-derived-outputs');
		await expect(derived).toBeVisible();
		for (const tid of DERIVED_IDS) {
			await expect(derived.getByTestId(tid)).toBeVisible();
		}
	});

	test('§21.3 (4) — DEM missing posture shows blocker code DEM_MISSING_OR_STALE', async ({
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

		let sawBlocker = false;
		for (const qid of SAMPLE_QUEUE_IDS) {
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

			await shell.getByTestId('tm2-tab-std-readiness').click();
			await expect(shell.getByTestId('tm2-tab-panel-std-readiness')).toBeVisible({ timeout: 30_000 });

			const codeEl = shell.getByTestId('tm2-std-dem-blocker-code');
			if (await codeEl.isVisible().catch(() => false)) {
				await expect(codeEl).toHaveText(/DEM_MISSING_OR_STALE/);
				sawBlocker = true;
				break;
			}

			// Reset selection for next queue attempt.
			await shell.getByTestId('tm2-tab-overview').click();
		}

		if (!sawBlocker) {
			test.skip(
				true,
				'No tender in sampled queues surfaced tm2-std-dem-blocker-code (needs publication readiness + DEM gap per P9-10).',
			);
		}
	});
});
