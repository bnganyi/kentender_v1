import { Page } from '@playwright/test';
import { workspaceAppPath } from './routes';

export const ktsmSupplierRegistryWorkspace = {
	/** Frappe desk route for Workspace "KTSM Supplier Registry" */
	route: workspaceAppPath('KTSM Supplier Registry'),
} as const;

export async function openKtsmSupplierRegistry(page: Page) {
	await page.goto(ktsmSupplierRegistryWorkspace.route, { waitUntil: 'domcontentloaded' });
}
