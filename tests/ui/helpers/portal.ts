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
	// Polled: right after a resize that crosses the narrow breakpoint the page
	// is still swapping cards for tables (a re-render on the next tick); a
	// settled page that overflows still fails.
	try {
		await expect
			.poll(() => page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth), { message: 'horizontal overflow in px', timeout: 5_000 })
			.toBeLessThanOrEqual(0);
	} catch (error) {
		// name what sticks out, so the failure is actionable
		const offenders = await page.evaluate(() => {
			const width = window.innerWidth;
			return [...document.querySelectorAll('body *')]
				.map((el) => ({ el, r: el.getBoundingClientRect() }))
				.filter(({ r }) => r.width > 0 && r.right > width + 1)
				.slice(0, 8)
				.map(({ el, r }) => `${el.tagName.toLowerCase()}${el.getAttribute('data-testid') ? `[${el.getAttribute('data-testid')}]` : ''}.${String((el as HTMLElement).className || '').split(' ').slice(0, 2).join('.')} right=${Math.round(r.right)}`);
		});
		throw new Error(`${(error as Error).message}\noverflowing: ${offenders.join(' | ')}`);
	}
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
