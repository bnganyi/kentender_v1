import { expect, test, type Page } from '@playwright/test';
import { execSync } from 'node:child_process';
import path from 'node:path';

import { login } from '../../helpers/auth';

async function loginAsRequester(page: Page) {
	await login(
		page,
		process.env.UI_NDS_REQUESTER_USER || 'grace.wanjiku@moh.example.test',
		process.env.UI_NDS_REQUESTER_PASSWORD || 'admin',
	);
}

const RETURNED_ROUTE = '/desk/departmental-needs-edit?need=NDS-MOH-2027-003';
const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');
const SITE = process.env.UI_SITE || 'kentender.midas.com';

test.describe('NDS-UI-02B Returned Need correction', () => {
	test.describe.configure({ mode: 'serial' });

	// The second test below resubmits the shared seed fixture (Returned ->
	// Submitted); reseed first so this file is self-healing regardless of what
	// a previous run left behind — same convention as
	// budget-funding-line-strategy-xmod-str-001.spec.ts.
	test.beforeAll(() => {
		execSync(
			`cd "${BENCH_ROOT}" && bench --site ${SITE} execute kentender_procurement.departmental_needs.seeds.kentender_mvp_r1.upsert_departmental_needs`,
			{ stdio: 'pipe', timeout: 120_000 },
		);
	});

	test.beforeEach(async ({ page }) => {
		await loginAsRequester(page);
	});

	test('renders the exact return notice and editable content fixture', async ({ page }) => {
		await page.goto(RETURNED_ROUTE, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('departmental-needs-edit')).toBeVisible({ timeout: 30_000 });
		await expect(page.getByRole('heading', { name: 'Regional health-facility connectivity equipment' })).toBeVisible();
		await expect(page.getByText('Returned', { exact: true })).toBeVisible();
		await expect(page.getByText('Returned for correction')).toBeVisible();
		await expect(
			page.getByText('Clarify whether the 120 sets cover all regional referral facilities and attach the facilities distribution list.'),
		).toBeVisible();
		await expect(page.getByText('Returned by Dr Peter Kimani on 14 May 2027 at 10:35')).toBeVisible();
		await expect(page.locator('#kt-nds-f-title')).toHaveValue('Regional health-facility connectivity equipment');
		await expect(page.getByRole('button', { name: 'Withdraw need' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Save changes' })).toBeVisible();
		await expect(page.getByRole('button', { name: /Resubmit for departmental review/ })).toBeVisible();
		// §7.2's own explicit exclusion: no workflow history panel or approval stepper beyond the one notice block.
		await expect(page.getByText('Workflow history', { exact: false })).toHaveCount(0);
	});

	// NDS-MOH-2027-003's target financial year (2027/28) is a fixed fixture value
	// required by §7.2's exact-content spec, but genuinely lies in the future on
	// the real calendar — submit_need()'s intake-window check (NDS_INTAKE_WINDOW_NOT_CONFIGURED)
	// would reject a live resubmit against it until that year actually opens.
	// "Save changes" (update_need) carries no such date gate, so it is the live
	// interaction this fixture can exercise end-to-end; resubmit's own validation
	// and state transition are covered against a current fiscal year by
	// departmental-needs-create.spec.ts's live submit flow and by the Python
	// suite (test_departmental_needs_submission_validation.py).
	test('editing and saving a corrected Returned Need persists the change', async ({ page }) => {
		await page.goto(RETURNED_ROUTE, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('departmental-needs-edit')).toBeVisible({ timeout: 30_000 });
		const updated = 'Updated justification from the Playwright smoke test, long enough to satisfy the fifty character minimum required for resubmission.';
		await page.locator('[data-field="business_justification"]').fill(updated);
		await page.getByRole('button', { name: 'Save changes' }).click();
		await expect(page.getByText('Draft saved')).toBeVisible({ timeout: 15_000 });
		await page.reload({ waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('departmental-needs-edit')).toBeVisible({ timeout: 30_000 });
		await expect(page.locator('[data-field="business_justification"]')).toHaveValue(updated);
	});
});
