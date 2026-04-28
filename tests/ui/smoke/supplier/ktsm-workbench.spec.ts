import { test, expect } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';
import { openKtsmSupplierRegistry } from '../../helpers/ktsm';

test.describe('Supplier Management workbench (G + J2)', () => {
	test('Supplier Registry workspace renders KPI / landing testids', async ({ page }) => {
		await loginAsAdministrator(page);
		await openKtsmSupplierRegistry(page);
		const landing = page.getByTestId('ktsm-landing');
		await expect(landing).toBeVisible({ timeout: 60_000 });
		await expect(landing).toContainText('Supplier Management');
		await expect(page.getByTestId('ktsm-kpi-registered')).toBeVisible();
	});

	test('Workbench canonical controls are present', async ({ page }) => {
		await loginAsAdministrator(page);
		await openKtsmSupplierRegistry(page);
		await expect(page.getByTestId('ktsm-header')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId('ktsm-kpi-row')).toBeVisible();
		await expect(page.getByTestId('ktsm-queue-row-ownership')).toBeVisible();
		await expect(page.getByTestId('ktsm-queue-row-state')).toBeVisible();
		await expect(page.getByTestId('ktsm-search-input')).toBeVisible();
		await expect(page.getByTestId('ktsm-list-panel')).toBeVisible();
		await expect(page.getByTestId('ktsm-detail-panel')).toBeVisible();
	});

	test('Pending Review KPI applies list filter', async ({ page }) => {
		await loginAsAdministrator(page);
		await openKtsmSupplierRegistry(page);
		await page.getByTestId('ktsm-kpi-pending').click();
		await expect(page.getByTestId('ktsm-active-kpi')).toContainText('pending_review');
	});

	test('Reviewer sees full detail sections and deep-link actions', async ({ page }) => {
		await loginAsAdministrator(page);
		await openKtsmSupplierRegistry(page);
		const firstRow = page.locator('[data-supplier-code]').first();
		await expect(firstRow).toBeVisible({ timeout: 30_000 });
		await firstRow.click();
		await expect(page.getByTestId('ktsm-detail-profile')).toBeVisible();
		await expect(page.getByTestId('ktsm-detail-documents')).toBeVisible();
		await expect(page.getByTestId('ktsm-detail-category')).toBeVisible();
		await expect(page.getByTestId('ktsm-detail-compliance')).toBeVisible();
		await expect(page.getByTestId('ktsm-detail-risk')).toBeVisible();
		await expect(page.getByTestId('ktsm-detail-history')).toBeVisible();
		await expect(page.getByTestId('ktsm-open-profile')).toBeVisible();
		await expect(page.getByTestId('ktsm-open-documents')).toBeVisible();
		await expect(page.getByTestId('ktsm-documents-table')).toBeVisible();
	});

	test('Open Full Profile navigates to supplier form route', async ({ page }) => {
		await loginAsAdministrator(page);
		await openKtsmSupplierRegistry(page);
		const firstRow = page.locator('[data-supplier-code]').first();
		await expect(firstRow).toBeVisible({ timeout: 30_000 });
		await firstRow.click();
		await page.getByTestId('ktsm-open-profile').click();
		await expect(page).toHaveURL(/(\/app\/ktsm-supplier-profile\/[^/?#]+$|\/desk\/Form\/KTSM%20Supplier%20Profile\/[^/?#]+$|\/desk#Form\/KTSM%20Supplier%20Profile\/[^/?#]+$|\/desk\/ktsm-supplier-profile\/[^/?#]+$)/);
		await expect(page.getByText(/Page ktsm-supplier-profile not found/i)).toHaveCount(0);
		await expect(page.getByText('ERPNext Supplier').first()).toBeVisible({ timeout: 30_000 });
	});

	test('Open Documents opens KTSM documents register filtered by profile', async ({ page }) => {
		await loginAsAdministrator(page);
		await openKtsmSupplierRegistry(page);
		const firstRow = page.locator('[data-supplier-code]').first();
		await expect(firstRow).toBeVisible({ timeout: 30_000 });
		await firstRow.click();
		await expect(page.getByTestId('ktsm-doc-hint')).toContainText('KTSM Supplier Document');
		await page.getByTestId('ktsm-open-documents').click();
		await expect(page).toHaveURL(/(\/app\/ktsm-supplier-document\/view\/list(\?.*)?$|\/desk\/List\/KTSM%20Supplier%20Document\/List(\?.*)?$|\/desk#List\/KTSM%20Supplier%20Document\/List$|\/desk\/ktsm-supplier-document\/view\/list(\?.*)?$)/);
		await expect(page.getByText(/Page ktsm-supplier-document not found/i)).toHaveCount(0);
		await expect(page.getByText('KTSM Supplier Document').first()).toBeVisible({ timeout: 30_000 });
		await expect(page.getByText('Supplier Profile').first()).toBeVisible({ timeout: 30_000 });
	});

	test('New Supplier opens KTSM builder flow (not ERP quick-entry)', async ({ page }) => {
		await loginAsAdministrator(page);
		await openKtsmSupplierRegistry(page);
		await page.getByRole('button', { name: 'New Supplier' }).click();
		const activeModal = page.locator('.modal.show').last();
		await expect(activeModal).toBeVisible();
		await activeModal.locator('input[data-fieldname="supplier_name"]').fill(`Smoke Builder ${Date.now()}`);
		await activeModal.getByRole('button', { name: 'Create' }).click();
		await expect(page).toHaveURL(/(\/app\/ktsm-supplier-profile\/[^/?#]+$|\/desk\/Form\/KTSM%20Supplier%20Profile\/[^/?#]+$|\/desk#Form\/KTSM%20Supplier%20Profile\/[^/?#]+$|\/desk\/ktsm-supplier-profile\/[^/?#]+$)/, {
			timeout: 30_000,
		});
		await expect(page.getByText('Back to Supplier Workbench').first()).toBeVisible({ timeout: 30_000 });
		await expect(page.getByText('ERPNext Supplier').first()).toBeVisible({ timeout: 30_000 });
	});

	test('Procurement sidebar exposes Supplier Management workspace', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/app/procurement-home');
		const supplierNav = page.getByRole('link', { name: 'Supplier Management' });
		await expect(supplierNav).toBeVisible({ timeout: 30_000 });
		await supplierNav.click();
		await expect(page.getByTestId('ktsm-landing')).toBeVisible({ timeout: 60_000 });
	});
});
