/**
 * Frappe Desk form helpers for Playwright — patterns codified after STD-WORKS-POC Step 12.
 * Full rationale: `.cursor/rules/frappe-desk-playwright-patterns.mdc` (bench root).
 */
import { expect, type Page } from '@playwright/test';

/** DocType field wrapper; `data-fieldname` lives here, not on `.form-grid`. */
export function frappeControl(page: Page, fieldname: string) {
	return page.locator(`.frappe-control[data-fieldname="${fieldname}"]`).first();
}

/** First input inside a control (Data, Link, etc.). Prefer over `getByRole('textbox', { name })` when Desk wiring hides labels. */
export function controlInput(page: Page, fieldname: string) {
	return frappeControl(page, fieldname).locator('input').first();
}

/**
 * Link / Dynamic Link: type to open Awesomplete, pick an option, tab out.
 * URL query prefill alone is not a persistence contract — always complete selection for saves that must stick.
 */
export async function ensureLinkFieldFromAwesomplete(
	page: Page,
	fieldname: string,
	typeText: string,
	optionRoleName: string | RegExp,
) {
	const control = frappeControl(page, fieldname);
	const linkInput = control.locator('input').first();
	await linkInput.click();
	await linkInput.fill('');
	await linkInput.fill(typeText);
	const suggestion =
		typeof optionRoleName === 'string'
			? page.getByRole('option', { name: optionRoleName, exact: true }).first()
			: page.getByRole('option', { name: optionRoleName }).first();
	await suggestion.waitFor({ state: 'visible', timeout: 30_000 });
	await suggestion.click();
	await expect(linkInput).toHaveValue(/.+/, { timeout: 30_000 });
	await linkInput.press('Tab');
}

/**
 * Save: wait for `savedocs` 200, then assert the orange "Not Saved" pill is gone.
 * Do not rely on Save disabled/enabled alone — it is version- and timing-sensitive.
 */
export async function clickSaveAndWaitForSavedocs(page: Page, options?: { timeoutMs?: number }) {
	const timeoutMs = options?.timeoutMs ?? 120_000;
	const save = page.getByRole('button', { name: 'Save', exact: true });
	const responsePromise = page.waitForResponse(
		(resp) => resp.url().includes('frappe.desk.form.save.savedocs') && resp.status() === 200,
		{ timeout: timeoutMs },
	);
	await save.click({ force: true });
	await responsePromise;
	await expect(
		page.locator('.indicator-pill.orange:visible').filter({ hasText: 'Not Saved' }),
	).toHaveCount(0, { timeout: timeoutMs });
}

/** Child table data rows only — avoids extra `.grid-row` nodes Frappe renders outside `.rows`. */
export function childTableDataRows(page: Page, fieldname: string) {
	return frappeControl(page, fieldname).locator('.rows > .grid-row');
}

/** Read-only or mixed controls: assert copy inside the field control, not page-wide `getByText`. */
export function controlTextScope(page: Page, fieldname: string) {
	return frappeControl(page, fieldname);
}
