/**
 * **R7-005 / LV-R7-005-01** — Evidence timeline warns when ``stale_warning`` is truthy (**NEG-PKGREL-STALE-001** UX).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { expectProcurementJourneyPageShell } from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

const GET_JOURNEY_API =
	'**/api/method/kentender_procurement.procurement_lifecycle.api.journey_api.get_journey';

function markPkgrelStale(evidenceSummary: unknown[]): unknown[] {
	return evidenceSummary.map((raw) => {
		const evt = raw as Record<string, unknown>;
		const hc = String(evt.handoff_code || '').trim();
		if (hc === 'PKGREL-MOH-2026-001') {
			return {
				...evt,
				stale_warning: true,
				stale_reason: 'NEG-PKGREL-STALE-001 mock — procurement method drift',
			};
		}
		return evt;
	});
}

test.describe('Stale handoff evidence warning (LV-R7-005-01)', () => {
	test('PLC-LV-R7-005-01: PKGREL mocked stale shows plc-evidence-timeline-stale-warning', async ({
		page,
	}) => {
		await page.route(GET_JOURNEY_API, async (route) => {
			const res = await route.fetch();
			const wrapped = (await res.json()) as {
				message?: { evidence_summary?: unknown[] };
			};
			if (wrapped.message && Array.isArray(wrapped.message.evidence_summary)) {
				wrapped.message.evidence_summary = markPkgrelStale(wrapped.message.evidence_summary);
			}
			await route.fulfill({
				status: res.status(),
				contentType: 'application/json',
				body: JSON.stringify(wrapped),
			});
		});

		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);

		const stale = page
			.locator('[data-handoff-code="PKGREL-MOH-2026-001"]')
			.locator('[data-testid="plc-evidence-timeline-stale-warning"]');
		await expect(stale.first()).toBeVisible({ timeout: 45_000 });
		await expect(stale.first()).toContainText(/NEG-PKGREL-STALE-001 mock/i);
	});
});
