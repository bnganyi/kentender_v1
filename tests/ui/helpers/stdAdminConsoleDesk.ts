/**
 * Shared Desk selectors for STD Administration Console POC (Steps 3–9).
 * Button labels match `__("…")` in std_template.js / procurement_tender.js (English Desk).
 */

import { expect, type Page } from '@playwright/test';

export const STD_ADMIN_TEMPLATE_CODE = 'KE-PPRA-WORKS-BLDG-2022-04-POC';

const enc = (s: string) => encodeURIComponent(s);

export async function expectStdAdminGroupVisible(page: Page) {
	await expect(
		page.locator(`.inner-group-button[data-label="${enc('STD Admin')}"]`).first(),
	).toBeVisible({ timeout: 120_000 });
}

/** STD Template custom actions under "STD Admin". */
export async function clickStdAdminAction(page: Page, label: string) {
	const group = page.locator(`.inner-group-button[data-label="${enc('STD Admin')}"]`).first();
	await expect(group).toBeVisible({ timeout: 120_000 });
	await group.locator('button').first().click();
	const item = group.locator(`.dropdown-menu.show a.dropdown-item[data-label="${enc(label)}"]`);
	await expect(item).toBeVisible({ timeout: 15_000 });
	await item.click();
}

/** Procurement Tender demo workspace actions under "STD Demo". */
export async function clickStdDemoAction(page: Page, label: string) {
	const group = page.locator(`.inner-group-button[data-label="${enc('STD Demo')}"]`).first();
	await expect(group).toBeVisible({ timeout: 120_000 });
	await group.locator('button').first().click();
	const item = group.locator(`.dropdown-menu.show a.dropdown-item[data-label="${enc(label)}"]`);
	await expect(item).toBeVisible({ timeout: 15_000 });
	await item.click();
}

/** Doc 5 §24 — Works Hardening actions on Procurement Tender (WH-012). */
export async function clickWorksHardeningAction(page: Page, label: string) {
	const group = page
		.locator(`.inner-group-button[data-label="${encodeURIComponent('Works Hardening')}"]`)
		.first();
	await expect(group).toBeVisible({ timeout: 120_000 });
	await group.locator('button').first().click();
	const item = group.locator(`.dropdown-menu.show a.dropdown-item[data-label="${encodeURIComponent(label)}"]`);
	await expect(item).toBeVisible({ timeout: 15_000 });
	await item.click();
}

/** Procurement Tender STD POC engine actions under "STD POC". */
export async function clickStdPocAction(page: Page, label: string) {
	const group = page.locator(`.inner-group-button[data-label="${enc('STD POC')}"]`).first();
	await expect(group).toBeVisible({ timeout: 120_000 });
	await group.locator('button').first().click();
	const item = group.locator(`.dropdown-menu.show a.dropdown-item[data-label="${enc(label)}"]`);
	await expect(item).toBeVisible({ timeout: 15_000 });
	await item.click();
}

/** Procurement Officer Tender Configuration POC actions under "Officer Tender Configuration". */
export async function clickOfficerTenderConfigurationAction(page: Page, label: string) {
	const group = page
		.locator(`.inner-group-button[data-label="${enc('Officer Tender Configuration')}"]`)
		.first();
	await expect(group).toBeVisible({ timeout: 120_000 });
	await group.locator('button').first().click();
	const item = group.locator(`.dropdown-menu.show a.dropdown-item[data-label="${enc(label)}"]`);
	await expect(item).toBeVisible({ timeout: 15_000 });
	await item.click();
}

/**
 * `std_admin_prompt_string` dialogs: single Data field `value`, primary "Run".
 */
export async function submitFrappePromptString(page: Page, value: string) {
	const modal = page.locator('.modal-dialog:visible').first();
	await expect(modal).toBeVisible({ timeout: 60_000 });
	const input = modal
		.locator('.frappe-control[data-fieldname="value"] input')
		.or(modal.locator('input[type="text"]'))
		.first();
	await expect(input).toBeVisible({ timeout: 30_000 });
	await input.fill(value);
	await modal.getByRole('button', { name: 'Run', exact: true }).click();
}

/**
 * `frappe.prompt` with Select field (e.g. variant picker). Primary button is usually "Create" or "Apply".
 */
export async function submitFrappePromptSelect(
	page: Page,
	fieldname: string,
	optionValue: string,
	primaryButton: 'Create' | 'Apply',
) {
	const modal = page.locator('.modal-dialog:visible').first();
	await expect(modal).toBeVisible({ timeout: 60_000 });
	const sel = modal.locator(`select[data-fieldname="${fieldname}"]`);
	await expect(sel).toBeVisible({ timeout: 30_000 });
	await sel.selectOption(optionValue);
	await modal.getByRole('button', { name: primaryButton, exact: true }).click();
}

/** Extra-large HTML result dialogs from std_admin_html_dialog / std_poc_demo_html_dialog. */
export async function closeVisibleHtmlModal(page: Page) {
	const modal = page.locator('.modal-dialog:visible').first();
	await expect(modal).toBeVisible({ timeout: 120_000 });
	await modal.getByRole('button', { name: 'Close', exact: true }).click();
	await expect(modal).toBeHidden({ timeout: 30_000 });
}

/** Dismiss `frappe.msgprint` / alert-style modal if present (best-effort). */
export async function dismissFrappeMessageIfPresent(page: Page) {
	const shell = page.locator('.modal.fade.show').first();
	if (!(await shell.isVisible().catch(() => false))) {
		return;
	}
	const dlg = shell.locator('.modal-dialog').first();
	const ok = dlg.getByRole('button', { name: 'OK', exact: true });
	if (await ok.isVisible().catch(() => false)) {
		await ok.click();
	} else if (await dlg.getByRole('heading', { name: 'Action could not complete' }).isVisible().catch(() => false)) {
		const x = dlg.locator('.modal-header a.close, .modal-header button.close').first();
		if (await x.isVisible().catch(() => false)) {
			await x.click();
		} else {
			await dlg.locator('.modal-header button').first().click();
		}
	} else {
		const closeBtn = dlg.locator('button.close, button[data-dismiss="modal"]').first();
		if (await closeBtn.isVisible().catch(() => false)) {
			await closeBtn.click();
		} else {
			await page.keyboard.press('Escape');
		}
	}
	await expect(shell).toBeHidden({ timeout: 20_000 }).catch(() => undefined);
}

/** Hide Frappe's current dialog via `cur_dialog` (msgprint / confirm). */
export async function hideFrappeCurDialog(page: Page) {
	await page
		.evaluate(() => {
			const w = window as unknown as { cur_dialog?: { hide?: () => void } };
			w.cur_dialog?.hide?.();
		})
		.catch(() => undefined);
	await page.locator('.modal.fade.show').waitFor({ state: 'hidden', timeout: 15_000 }).catch(() => undefined);
}
