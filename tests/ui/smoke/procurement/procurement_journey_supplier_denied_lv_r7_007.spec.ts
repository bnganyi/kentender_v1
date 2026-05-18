/**
 * R7-007 / **LV-R7-007-01** — Supplier must not consume internal Procurement Journey payloads
 * from the Desk page client call path (NEG-SUP-EVIDENCE-ACCESS-001 UI mirror).
 */
import { expect, test } from '@playwright/test';

import { loginAsSupplierPortalUser } from '../../helpers/auth';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('Procurement Journey supplier confidentiality (LV-R7-007-01)', () => {
	test('PLC-LV-R7-007-01: supplier session shows journey load error — no timeline events', async ({
		page,
	}) => {
		if (!(process.env.UI_SUPPLIER_PORTAL_USER || '').trim()) {
			test.skip(true, 'Set UI_SUPPLIER_PORTAL_USER (apps/kentender_v1/.env.ui).');
		}

		await loginAsSupplierPortalUser(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});

		await expect(page.getByTestId('plc-journey-header-error')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('plc-evidence-timeline-event')).toHaveCount(0);
	});
});
