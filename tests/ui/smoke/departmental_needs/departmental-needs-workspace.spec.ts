import { expect, test, type Page } from '@playwright/test';

import { login } from '../../helpers/auth';

const route =
	'/desk/departmental-needs?procuring_entity=PE-MOH&organisation_unit=MOH-DIR-DHP&financial_year=2027%2F28';

async function loginAsDepartmentalReviewer(page: Page) {
	await login(
		page,
		process.env.UI_NDS_REVIEWER_USER || 'peter.kimani@moh.example.test',
		process.env.UI_NDS_REVIEWER_PASSWORD || 'admin',
	);
}

async function openWorkspace(page: Page) {
	await page.goto(route, { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('departmental-needs-workspace')).toBeVisible({ timeout: 30_000 });
}

async function expectNoPageOverflow(page: Page) {
	const dimensions = await page.evaluate(() => ({
		clientWidth: document.documentElement.clientWidth,
		scrollWidth: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
	}));
	expect(dimensions.scrollWidth).toBeLessThanOrEqual(dimensions.clientWidth + 1);
}

test.describe('NDS-UI-01 Departmental Needs workspace', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsDepartmentalReviewer(page);
	});

	test('renders the exact scoped fixture and authorized review action', async ({ page }) => {
		await openWorkspace(page);
		await expect(page.getByRole('heading', { name: 'Departmental Needs', level: 1 })).toBeVisible();
		await expect(page.getByText('Ministry of Health')).toBeVisible();
		await expect(page.getByText('Directorate of Digital Health and Policy')).toBeVisible();
		await expect(page.getByText('2027/28')).toBeVisible();
		await expect(page.getByTestId('nds-summary-total')).toContainText('3');
		await expect(page.getByTestId('nds-summary-waiting')).toContainText('1');
		await expect(page.getByTestId('nds-summary-accepted')).toContainText('1');
		await expect(page.getByTestId('nds-summary-included')).toContainText('1');
		await expect(page.getByText('NDS-MOH-2027-002')).toBeVisible();
		await expect(page.getByRole('button', { name: /Review/ }).first()).toBeVisible();
		await expect(page.getByRole('button', { name: /Create need/ })).toHaveCount(0);
	});

	for (const viewport of [
		{ name: 'desktop', width: 1440, height: 900 },
		{ name: 'tablet', width: 1024, height: 768 },
		{ name: 'mobile', width: 390, height: 844 },
	]) {
		test(`${viewport.name} layout keeps overflow inside table regions`, async ({ page }) => {
			await page.setViewportSize(viewport);
			await openWorkspace(page);
			await expectNoPageOverflow(page);
		});
	}

	test('workspace controls are keyboard focusable', async ({ page }) => {
		await openWorkspace(page);
		const review = page.getByRole('button', { name: /Review/ }).first();
		await review.focus();
		await expect(review).toBeFocused();
		await expect(page.getByRole('navigation', { name: 'Breadcrumb' })).toBeVisible();
	});
});
