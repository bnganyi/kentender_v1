/**
 * R1-007 — Procurement Handoff Card: technical references in a collapsible Desk section
 * (rectification pack §7.5; Frappe `refresh_section_collapse` starts collapsed when no mandatory fields inside).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { frappeControl } from '../../helpers/deskForm';

test.describe('R1-007 Handoff technical refs (Desk)', () => {
	test.setTimeout(120_000);

	test('Technical Refs control is hidden until advanced section is expanded', async ({
		page,
		baseURL,
	}) => {
		const root = baseURL!;
		await loginAsAdministrator(page);
		await page.goto(`${root}/app/procurement-handoff-card/new`, {
			waitUntil: 'domcontentloaded',
		});
		await page.locator('.layout-main-section .form-layout').first().waitFor({ timeout: 90_000 });

		const section = page.locator('.form-section[data-fieldname="section_technical_refs"]');
		await expect(section).toBeVisible();
		const body = section.locator('.section-body').first();
		await expect(body).toHaveClass(/hide/);

		await expect(frappeControl(page, 'technical_refs_json')).toBeHidden();

		await section.locator('.section-head.collapsible').click();
		await expect(body).not.toHaveClass(/hide/);
		await expect(frappeControl(page, 'technical_refs_json')).toBeVisible({ timeout: 15_000 });
	});
});
