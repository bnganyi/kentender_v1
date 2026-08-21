import { expect, test, type Page } from '@playwright/test';

import { login } from '../../helpers/auth';

async function loginAsRequester(page: Page) {
	await login(
		page,
		process.env.UI_NDS_REQUESTER_USER || 'grace.wanjiku@moh.example.test',
		process.env.UI_NDS_REQUESTER_PASSWORD || 'admin',
	);
}

async function openCreate(page: Page) {
	await page.goto('/desk/departmental-needs-new', { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('departmental-needs-new')).toBeVisible({ timeout: 30_000 });
}

test.describe('NDS-UI-02A Create Departmental Need', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsRequester(page);
	});

	test('renders the exact static fixture and explicit exclusions', async ({ page }) => {
		await openCreate(page);
		await expect(page.getByRole('heading', { name: 'Create departmental need' })).toBeVisible();
		await expect(page.getByText('Ministry of Health').first()).toBeVisible();
		await expect(page.getByText('Directorate of Digital Health and Policy').first()).toBeVisible();
		await expect(page.getByText('1. Need Summary')).toBeVisible();
		await expect(page.getByText('2. Items Needed')).toBeVisible();
		await expect(page.getByText('3. Timing & Location')).toBeVisible();
		await expect(page.getByText('5. Supporting Documents')).toBeVisible();
		await expect(page.getByRole('button', { name: 'Cancel' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Save draft' })).toBeVisible();
		await expect(page.getByRole('button', { name: /Submit for departmental review/ })).toBeVisible();
		// Explicit exclusions (§7.1): no procurement classification, budget, Plan/Requisition/Tender references.
		for (const forbidden of [
			'Requirement type', 'Procurement category', 'Procurement method', 'Budget code',
			'Funding confirmation', 'Unit price', 'BOQ', 'Terms of Reference', 'Plan reference',
			'Requisition reference', 'Tender reference',
		]) {
			await expect(page.getByText(forbidden, { exact: false })).toHaveCount(0);
		}
	});

	test('a partial draft can be saved with only title and context, then a complete draft can be submitted', async ({ page }) => {
		await openCreate(page);
		const title = `UI smoke draft ${Date.now()}`;
		await page.locator('#kt-nds-f-title').fill(title);
		await page.getByRole('button', { name: 'Save draft' }).click();
		// frappe.set_route(name, {need}) hands the value through frappe.route_options,
		// not the URL query string — Frappe core's push_state() never appends it — so
		// the target record is confirmed by its rendered content, not the URL.
		await expect(page).toHaveURL(/\/departmental-needs-edit$/, { timeout: 15_000 });
		await expect(page.getByTestId('departmental-needs-edit')).toBeVisible({ timeout: 15_000 });
		await expect(page.getByRole('heading', { name: title })).toBeVisible();

		// Complete the rest and submit. The prior (now-hidden) create page's
		// container stays in the DOM, so scope locators to the visible edit
		// container rather than matching duplicate ids/attributes across both.
		const editRoot = page.getByTestId('departmental-needs-edit');
		await editRoot.locator('[data-field="business_justification"]').fill(
			'A complete business justification supplied by the Playwright smoke test, long enough to satisfy the fifty character minimum required for submission.',
		);
		await editRoot.locator('[data-item-field="description"]').first().fill('Smoke test item');
		await editRoot.locator('[data-item-field="indicative_quantity"]').first().fill('5');
		await editRoot.locator('[data-item-field="unit_code"]').first().selectOption('Each');
		await editRoot.locator('[data-field="required_by_date"]').fill('2027-01-15');
		await editRoot.locator('[data-field="delivery_or_use_location"]').fill('MOH headquarters');
		await editRoot.getByRole('button', { name: /Resubmit for departmental review|Submit for departmental review/ }).click();
		await expect(page).toHaveURL(/\/departmental-needs-detail$/, { timeout: 15_000 });
		await expect(page.getByTestId('departmental-needs-detail')).toBeVisible({ timeout: 15_000 });
		await expect(page.getByRole('heading', { name: title })).toBeVisible();
		await expect(page.getByText('Submitted', { exact: true }).first()).toBeVisible();
	});

	test('cancel returns to the workspace', async ({ page }) => {
		await openCreate(page);
		await page.getByRole('button', { name: 'Cancel' }).click();
		await expect(page.getByTestId('departmental-needs-workspace')).toBeVisible({ timeout: 15_000 });
	});
});
