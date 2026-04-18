import { Page } from '@playwright/test';

export async function login(page: Page, username: string, password: string) {
	await page.goto('/login', { waitUntil: 'domcontentloaded' });
	// Frappe login uses sr-only labels; prefer stable ids (see frappe/www/login.html).
	const email = page.locator('#login_email');
	try {
		await email.waitFor({ state: 'visible', timeout: 30_000 });
	} catch {
		// Stale session can land on Desk without the login form; reset cookies and retry.
		await page.context().clearCookies();
		await page.goto('/login', { waitUntil: 'domcontentloaded' });
		await email.waitFor({ state: 'visible', timeout: 30_000 });
	}
	await email.fill(username);
	await page.locator('#login_password').fill(password);
	// Exact "Login" — avoid matching Frappe's "Invalid Login. Try again." button (/login/i would match).
	await page.getByRole('button', { name: 'Login', exact: true }).click();

	const outcome = await Promise.race([
		page.getByText(/Invalid Login/i).waitFor({ state: 'visible', timeout: 60_000 }).then(() => 'invalid' as const),
		page
			.getByRole('heading', { name: /Login to Frappe/i })
			.waitFor({ state: 'hidden', timeout: 60_000 })
			.then(() => 'ok' as const),
	]);

	if (outcome === 'invalid') {
		throw new Error(
			'Login failed (Invalid Login). Set UI_ADMIN_USER / UI_ADMIN_PASSWORD in apps/kentender_v1/.env.ui to match the target site.',
		);
	}

	await page.waitForLoadState('domcontentloaded');
}

/** Wave 0 smoke: use a user that exists on the target site (see `.env.ui`). */
export async function loginAsAdministrator(page: Page) {
	await login(
		page,
		process.env.UI_ADMIN_USER || 'Administrator',
		process.env.UI_ADMIN_PASSWORD || 'Sn00per56*',
	);
}

export async function loginAsStrategyManager(page: Page) {
	await login(
		page,
		process.env.UI_STRATEGY_USER || '',
		process.env.UI_STRATEGY_PASSWORD || '',
	);
}

export async function loginAsPlanningAuthority(page: Page) {
  await login(
    page,
    process.env.UI_PLANNING_USER || '',
    process.env.UI_PLANNING_PASSWORD || '',
  );
}
