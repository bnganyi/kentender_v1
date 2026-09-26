import { expect, Page } from '@playwright/test';

import { login } from './auth';

/**
 * BDS-CHG-001 v0.8 plan OD-B — helpers for the public supplier portal
 * (kentender_core/www/kt_portal). The portal is a Website page, not Desk:
 * there is no frappe.router, no Desk chrome and no Frappe message dialog.
 */

/** Sign in through Frappe's /login, then open `returnTo` on the portal. */
export async function loginToPortal(page: Page, user: string, password: string, returnTo = '/tenders'): Promise<void> {
	await login(page, user, password);
	await page.goto(returnTo, { waitUntil: 'domcontentloaded' });
	await waitForPortal(page);
}

/** The surface app has replaced the server placeholder. */
export async function waitForPortal(page: Page): Promise<void> {
	await expect(page.locator('#kt-portal-app .kt-portal-loading')).toHaveCount(0, { timeout: 30_000 });
}

/** User-correctable and failure states render inline; Frappe's dialog never opens. */
export async function expectNoFrappeDialog(page: Page): Promise<void> {
	await expect(page.locator('.modal.show, .msgprint, .modal-dialog:visible')).toHaveCount(0);
}

/** BDS §10.1: nothing is reached by horizontal scrolling. */
export async function expectNoHorizontalOverflow(page: Page): Promise<void> {
	const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
	expect(overflow, 'horizontal overflow in px').toBeLessThanOrEqual(0);
}

/** WCAG 1.4.4 — render at 200% zoom (CSS zoom on the root) for a reflow check. */
export async function atZoom200(page: Page): Promise<void> {
	await page.evaluate(() => {
		document.documentElement.style.zoom = '2';
	});
}

/** Page-specific console errors (favicon and socket noise excluded). */
export function collectPortalConsoleErrors(page: Page): string[] {
	const errors: string[] = [];
	page.on('console', (message) => {
		const text = message.text();
		if (text.includes('socket.io') || text.includes('ERR_CONNECTION_REFUSED')) return;
		// An expected 404 (Not found state) is asserted by status, not by console.
		if (text.includes('Failed to load resource')) return;
		if (message.type() === 'error') errors.push(text);
	});
	page.on('pageerror', (error) => errors.push(String(error)));
	return errors;
}
