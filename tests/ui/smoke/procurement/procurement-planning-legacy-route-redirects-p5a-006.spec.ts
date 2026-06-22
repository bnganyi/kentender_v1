/**
 * P1-007 — Legacy Planning routes are retired safely.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const PKG = 'PKG-MOH-2026-001';
const INCL = 'PLANINCL-MOH-2026-001';
const REL = 'PKGREL-MOH-2026-001';

const CANONICAL_ROUTES = [
	'/desk/procurement-planning',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/releases',
] as const;

test.describe('P1-007 Planning route retirement', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('retired approved-demands route redirects to workbench', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
		await expect(page.getByTestId('pp2-approved-demands-page')).toHaveCount(0);
		await page.screenshot({ path: 'artifacts/p1-007-approved-demands-redirect.png', fullPage: true });
	});

	test('retired packages list route redirects to workbench', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
		await expect(page.getByTestId('pp2-packages-page')).toHaveCount(0);
	});

	test('evidence index redirects to workbench without evidence surface', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/evidence`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
		await expect(page.getByTestId('pp2-planning-evidence-index')).toHaveCount(0);
	});

	test('evidence with package code redirects to workbench query deep link', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/evidence/${PKG}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(new RegExp(`package_code=${PKG}`));
		await expect(page.getByTestId('pp2-planning-evidence-index')).toHaveCount(0);
	});

	test('path-style package route keeps contextual package deep link', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages/${PKG}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(new RegExp(`/desk/procurement-planning\\?package_code=${PKG}`));
	});

	test('inclusion detail redirects to workbench', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/inclusions/${INCL}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
	});

	test('release detail redirects to releases list', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/releases/${REL}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-released-to-tender-page')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning\/releases(?:\?|$)/);
	});

	test('detail surface slug readiness redirects to workbench', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/readiness`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
	});

	test('release-package and technical-details aliases redirect safely', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/release-package`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);

		await page.goto(`${root}/desk/procurement-planning/technical-details`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
	});

	test('unknown planning slug shows not-found inside shell', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/not-a-real-route`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-route-not-found')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-route-not-found')).toContainText(
			/You do not have access to this planning information\./i,
		);
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible();
		await expect(page.getByRole('link', { name: 'Procurement Home' }).first()).toBeVisible();
		await page.screenshot({ path: 'artifacts/p1-007-legacy-route-not-found.png', fullPage: true });
	});

	test('unauthorized role receives permission-aware not-found on internal legacy route', async ({ page }) => {
		await page.addInitScript(() => {
			(globalThis as unknown as { __kt_pp2_test_roles?: string[] }).__kt_pp2_test_roles = ['Supplier'];
		});
		await page.goto(`${root}/desk/procurement-planning/evidence`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-route-not-found')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-route-not-found')).toContainText(
			/You do not have access to this planning information\./i,
		);
	});

	test('canonical planning routes remain unchanged', async ({ page }) => {
		for (const path of CANONICAL_ROUTES) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
			await expect(page.getByTestId('pp2-route-not-found')).toHaveCount(0);
			expect(page.url()).toContain(path);
		}
	});
});
