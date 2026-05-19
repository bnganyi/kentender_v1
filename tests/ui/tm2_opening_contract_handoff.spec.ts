/**
 * Q-06 — doc 9 §21.3 item 10 (canonical `tm2_opening_contract_handoff.spec.ts`).
 *
 * **Contract handoff tab shows corrected evaluated price 96,754,000 KES** (alpha corrected
 * total per doc 8 smoke contract + doc 9 §21.3). Backend contract: ``test_p9_18_after_create_contract_handoff_reference``
 * (``final_evaluated_price`` 96_754_000).
 *
 * Set ``UI_TM2_CONTRACT_HANDOFF_TENDER`` to a ``tender_code`` whose **TM2 Contract Handoff Reference**
 * carries that evaluated total (same fixture path as **P9-18**). Without it, the test **skips**
 * so empty dev sites do not fail CI.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from './helpers/auth';
import { clickTm2LegacyTab } from './helpers/tm2Workbench';
import { dismissOptionalDeskModals } from './helpers/routes';

function digitsOnly(s: string): string {
	return s.replace(/\D/g, '');
}

test.describe('TM2 opening / contract handoff (Q-06 / doc 9 §21.3)', () => {
	test.setTimeout(180_000);

	test('§21.3 (10) — Contract Handoff tab shows corrected evaluated price 96,754,000 KES', async ({
		page,
		baseURL,
	}) => {
		const tenderCode = (process.env.UI_TM2_CONTRACT_HANDOFF_TENDER || '').trim();
		test.skip(
			!tenderCode,
			'Set UI_TM2_CONTRACT_HANDOFF_TENDER to a tender with CHR + final_evaluated_price 96,754,000 KES (P9-18 fixture).',
		);

		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const search = shell.getByTestId('tm2-search-input');
		await search.fill('');
		const listResp = page.waitForResponse(
			(r) =>
				r.url().includes('list_workbench_tenders') &&
				r.request().method() === 'POST' &&
				r.status() === 200,
			{ timeout: 60_000 },
		);
		await search.fill(tenderCode);
		await listResp;
		await page.waitForTimeout(450);

		const row = shell.locator(`[data-testid="tm2-tender-list-row"][data-tm2-tender-code="${tenderCode}"]`).first();
		await expect(row).toBeVisible({ timeout: 60_000 });
		await row.click();
		await expect(shell.getByTestId('tm2-detail-sticky')).toBeVisible({ timeout: 60_000 });

		const legacyTab = 'tm2-tab-contract-handoff';
		const tab = shell.getByTestId('tm2-tab-handoff');
		await expect(tab).toBeVisible();
		await expect(tab).toBeEnabled();
		await clickTm2LegacyTab(page, 'tm2-tab-contract-handoff');

		await expect(shell.getByTestId('tm2-tab-panel-contract-handoff')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-ch-readonly-notice')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-ch-dcm-readonly-notice')).toBeVisible();
		await expect(shell.getByTestId('tm2-ch-dcm-ref')).toBeVisible();

		const priceEl = shell.getByTestId('tm2-ch-final-price');
		await expect(priceEl).toBeVisible();
		const priceText = (await priceEl.innerText()).trim();
		expect(priceText.length).toBeGreaterThan(0);
		expect(digitsOnly(priceText)).toContain('96754000');
	});
});
