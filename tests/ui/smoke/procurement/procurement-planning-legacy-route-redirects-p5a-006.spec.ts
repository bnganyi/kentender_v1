/**
 * P5A-006 — Superseded Planning routes redirect safely to canonical destinations.
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
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
] as const;

test.describe('P5A-006 Planning legacy route redirects', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('evidence index redirects to packages without evidence surface', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/evidence`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-packages-page')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning\/packages(?:\?|$)/);
		await expect(page.getByTestId('pp2-planning-evidence-index')).toHaveCount(0);
	});

	test('evidence with package code redirects to packages query deep link', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/evidence/${PKG}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-packages-page')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(new RegExp(`package_code=${PKG}`));
		await expect(page.getByTestId('pp2-planning-evidence-index')).toHaveCount(0);
	});

	test('path-style package route normalizes to packages query deep link', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages/${PKG}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-packages-page')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(new RegExp(`/desk/procurement-planning/packages\\?package_code=${PKG}`));
	});

	test('inclusion detail redirects to approved demands', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/inclusions/${INCL}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-approved-demands-page')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning\/approved-demands(?:\?|$)/);
	});

	test('release detail redirects to releases list', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/releases/${REL}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-released-to-tender-page')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning\/releases(?:\?|$)/);
	});

	test('detail surface slug readiness redirects to packages', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/readiness`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-packages-page')).toBeVisible({ timeout: 30000 });
		await expect(page).toHaveURL(/\/desk\/procurement-planning\/packages(?:\?|$)/);
	});

	test('unknown planning slug shows not-found inside shell', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/not-a-real-route`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-route-not-found')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible();
		await expect(page.getByRole('link', { name: 'Procurement Home' }).first()).toBeVisible();
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
