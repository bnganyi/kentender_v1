import { expect, test, type Page } from '@playwright/test';
import { execSync } from 'node:child_process';
import path from 'node:path';

import { login } from '../../helpers/auth';

async function loginAsReviewer(page: Page) {
	await login(
		page,
		process.env.UI_NDS_REVIEWER_USER || 'peter.kimani@moh.example.test',
		process.env.UI_NDS_REVIEWER_PASSWORD || 'admin',
	);
}

async function loginAsRequester(page: Page) {
	await login(
		page,
		process.env.UI_NDS_REQUESTER_USER || 'grace.wanjiku@moh.example.test',
		process.env.UI_NDS_REQUESTER_PASSWORD || 'admin',
	);
}

// Path segment (route[1]), not a query string — matches frappe.set_route's
// actual URL shape (a string arg lands in the path; see routeNeed() in
// departmental_needs_review_page.js).
const SUBMITTED_ROUTE = '/desk/departmental-needs-review/NDS-MOH-2027-002';
// Unscoped (no financial_year filter) so a freshly created throwaway Need —
// which lands in whatever fiscal year is actually open today, not the
// 2027/28 fixture year — is still listed.
const WORKSPACE_ALL_YEARS_ROUTE = '/desk/departmental-needs?procuring_entity=PE-MOH&organisation_unit=MOH-DIR-DHP';
const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');
const SITE = process.env.UI_SITE || 'kentender.midas.com';

test.describe('NDS-UI-02C Departmental review', () => {
	test.describe.configure({ mode: 'serial' });

	// NDS-MOH-2027-002 is a read-only fixture in this file (only the first test
	// below reads it) — reseed defensively so this file is self-healing
	// regardless of what a previous run left behind.
	test.beforeAll(() => {
		execSync(
			`cd "${BENCH_ROOT}" && bench --site ${SITE} execute kentender_procurement.departmental_needs.seeds.kentender_mvp_r1.upsert_departmental_needs`,
			{ stdio: 'pipe', timeout: 120_000 },
		);
	});

	test.beforeEach(async ({ page }) => {
		await loginAsReviewer(page);
	});

	test('renders the exact read-only fixture and decision actions', async ({ page }) => {
		await page.goto(SUBMITTED_ROUTE, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('departmental-needs-review')).toBeVisible({ timeout: 30_000 });
		await expect(page.getByRole('heading', { name: 'Review departmental need' })).toBeVisible();
		await expect(page.getByText('Submitted by:')).toBeVisible();
		await expect(page.getByText('Grace Wanjiku')).toBeVisible();
		await expect(page.getByText('12 May 2027 at 14:20')).toBeVisible();
		await expect(page.getByText('Digital health technical staff certification programme').first()).toBeVisible();
		await expect(page.locator('.kt-nds-items-table').getByText('120')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Return for correction' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Do not take forward' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Accept for planning' })).toBeVisible();
		// §7.3's explicit exclusion: no reason field visible on the base screen.
		await expect(page.getByRole('textbox')).toHaveCount(0);
	});

	// Uses a freshly created, disposable Need rather than the shared -002
	// fixture: recording a decision transitions it out of "Submitted", and
	// -002 is depended on by departmental-needs-workspace.spec.ts's summary
	// counts (workers run spec files concurrently, so mutating a shared
	// fixture here would race that file). Creating through the real UI as
	// REQUESTER also lands the throwaway Need in whichever fiscal year is
	// actually open today, sidestepping -002's future-dated 2027/28 fixture.
	test('return for correction requires a reason via the dialog and records the decision', async ({ page }) => {
		// Two personas, a create+submit round trip, and a decision round trip
		// legitimately exceed the default 60s test timeout under load.
		test.setTimeout(120_000);
		await loginAsRequester(page);
		const title = `UI smoke review target ${Date.now()}`;
		await page.goto('/desk/departmental-needs-new', { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('departmental-needs-new')).toBeVisible({ timeout: 30_000 });
		await page.locator('#kt-nds-f-title').fill(title);
		await page.locator('[data-field="business_justification"]').fill(
			'A complete business justification supplied by the Playwright smoke test, long enough to satisfy the fifty character minimum required for submission.',
		);
		await page.locator('[data-item-field="description"]').first().fill('Smoke test item');
		await page.locator('[data-item-field="indicative_quantity"]').first().fill('5');
		await page.locator('[data-item-field="unit_code"]').first().selectOption('Each');
		await page.locator('[data-field="required_by_date"]').fill('2027-01-15');
		await page.locator('[data-field="delivery_or_use_location"]').fill('MOH headquarters');
		await page.getByRole('button', { name: /Submit for departmental review/ }).click();
		await expect(page).toHaveURL(/\/departmental-needs-detail\/[^/?#]+$/, { timeout: 15_000 });

		await loginAsReviewer(page);
		await page.goto(WORKSPACE_ALL_YEARS_ROUTE, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('departmental-needs-workspace')).toBeVisible({ timeout: 30_000 });
		const row = page.locator('tr', { hasText: title }).first();
		await row.getByRole('button', { name: /Review/ }).click();
		const reviewRoot = page.getByTestId('departmental-needs-review');
		await expect(reviewRoot).toBeVisible({ timeout: 30_000 });
		// The Need's own title renders as a value paragraph under "Need Title",
		// not an ARIA heading (only the static "Review departmental need" is one).
		// The prior (now-hidden) workspace page's container stays in the DOM, so
		// scope to the visible review container rather than matching page-wide.
		await expect(reviewRoot.getByText(title, { exact: true })).toBeVisible();

		await reviewRoot.getByRole('button', { name: 'Return for correction' }).click();
		const dialog = reviewRoot.locator('[data-reason-dialog]');
		await expect(dialog).toBeVisible();
		await dialog.getByRole('button', { name: 'Confirm' }).click();
		// Too-short reason is rejected client-side; dialog stays open.
		await expect(dialog).toBeVisible();
		await dialog.locator('[data-reason-text]').fill('Playwright smoke test return reason, well over twenty characters.');
		await dialog.getByRole('button', { name: 'Confirm' }).click();
		await expect(page).toHaveURL(/departmental-needs$/, { timeout: 15_000 });
	});
});
