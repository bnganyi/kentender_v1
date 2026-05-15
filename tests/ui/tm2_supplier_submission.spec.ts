/**
 * Q-05 — doc 9 §21.3 items 8–9 (canonical `tm2_supplier_submission.spec.ts`).
 *
 * 8. **Submit bid** stays disabled when mandatory **addendum acknowledgement** is missing
 *    (`data-submit-disabled-by-addendum` on ``tm2-supplier-action-submit-bid``; modal
 *    ``tm2-supplier-submit-bid-submit`` disabled).
 * 9. **Late submission** messaging shows **official server time** (``tm2-supplier-late-official-server-time-line``
 *    or modal late banner).
 *
 * Requires ``UI_SUPPLIER_PORTAL_USER`` (+ ``UI_SUPPLIER_PORTAL_PASSWORD`` if not default seed).
 *
 * Optional tender codes (see ``.env.ui`` comments):
 * - ``UI_SUPPLIER_PORTAL_ADDENDUM_ACK_TENDER`` — published tender with **issued** addendum requiring ack (P10-07).
 * - ``UI_SUPPLIER_PORTAL_LATE_SUBMISSION_TENDER`` — tender whose submission deadline is **past** (P10-08).
 */
import { expect, test } from '@playwright/test';

import { loginAsSupplierPortalUser } from './helpers/auth';

async function openSupplierTenderDetail(
	page: import('@playwright/test').Page,
	baseURL: string | undefined,
	tcode: string,
): Promise<void> {
	const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
	await loginAsSupplierPortalUser(page);
	await page.goto(`${root}/supplier/tenders/${encodeURIComponent(tcode)}`, { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('tm2-supplier-tender-detail')).toBeVisible({ timeout: 60_000 });
	const denied = page.getByRole('alert');
	const okHeader = page.getByTestId('tm2-supplier-server-time');
	await expect(denied.or(okHeader).first()).toBeVisible({ timeout: 60_000 });
	if (await denied.isVisible().catch(() => false)) {
		test.skip(true, 'Supplier portal denied or tender not accessible for this user.');
	}
}

test.describe('TM2 supplier submission (Q-05 / doc 9 §21.3)', () => {
	test.setTimeout(120_000);

	test.beforeEach(() => {
		if (!(process.env.UI_SUPPLIER_PORTAL_USER || '').trim()) {
			test.skip(true, 'Set UI_SUPPLIER_PORTAL_USER (and password if needed).');
		}
	});

	test('§21.3 (8) — submit bid disabled when addendum acknowledgement is missing', async ({
		page,
		baseURL,
	}) => {
		const tcode = (process.env.UI_SUPPLIER_PORTAL_ADDENDUM_ACK_TENDER || '').trim();
		if (!tcode) {
			test.skip(
				true,
				'Set UI_SUPPLIER_PORTAL_ADDENDUM_ACK_TENDER (published tender + issued addendum requiring ack; see P10-07).',
			);
		}
		await openSupplierTenderDetail(page, baseURL, tcode);

		const root = page.getByTestId('tm2-supplier-action-submit-bid');
		await expect(root).toBeVisible({ timeout: 30_000 });
		await expect(root).toHaveAttribute('data-submit-disabled-by-addendum', '1');

		await expect(page.getByTestId('tm2-supplier-submit-bid-addendum-blocked-msg')).toBeVisible();

		await page.getByTestId('tm2-supplier-submit-bid-open').click();
		const modal = page.locator('#tm2SupplierSubmitBidModal');
		await expect(modal).toBeVisible({ timeout: 15_000 });
		await expect(modal.getByTestId('tm2-supplier-submit-modal-addendum-line')).toContainText(/Incomplete/i);
		await expect(modal.getByTestId('tm2-supplier-submit-bid-submit')).toBeDisabled();
	});

	test('§21.3 (9) — late submission message shows official server time', async ({ page, baseURL }) => {
		const tcode = (process.env.UI_SUPPLIER_PORTAL_LATE_SUBMISSION_TENDER || '').trim();
		if (!tcode) {
			test.skip(
				true,
				'Set UI_SUPPLIER_PORTAL_LATE_SUBMISSION_TENDER (deadline passed; see P10-08).',
			);
		}
		await openSupplierTenderDetail(page, baseURL, tcode);

		const late = page.getByTestId('tm2-supplier-late-submission-message');
		await expect(late).toBeVisible({ timeout: 30_000 });
		const timeLine = page.getByTestId('tm2-supplier-late-official-server-time-line');
		await expect(timeLine).toBeVisible();
		await expect(timeLine).toContainText(/Official server time/i);
		await expect(timeLine).toHaveText(/\d/);

		await page.getByTestId('tm2-supplier-submit-bid-open').click();
		const modal = page.locator('#tm2SupplierSubmitBidModal');
		await expect(modal).toBeVisible({ timeout: 15_000 });
		const banner = modal.getByTestId('tm2-supplier-submit-modal-late-banner');
		await expect(banner).toBeVisible();
		await expect(banner).toContainText(/Official server time/i);
	});
});
