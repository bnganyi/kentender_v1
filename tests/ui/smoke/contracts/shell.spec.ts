import { expect, test } from '@playwright/test';
import { login, loginAsAdministrator } from '../../helpers/auth';

// CM-CHG-001 v0.8 plan Phase 3, tracker CM8-315 / gate CM-G03: /app/contracts renders the empty shell with the rail from the app's own sidebar;
// a user with no part in contracts gets the shared denial (D-DENIED) as an answer, not an error; a failed read is D-ERR and Retry only reloads.
// Verifies first paint and an interactive re-render, and direct load, reload and back/forward (AGENTS.md section 6.4).
const ROUTE = '/app/contracts';
const READ = '**/api/method/kentender_contracts.api.workspace.get_contract_workspace*';

test.describe('Contracts shell', () => {
	test('opens an empty workspace under the rail, and reload and back/forward keep it', async ({ page }) => {
		const problems: string[] = [];
		page.on('pageerror', (error) => problems.push(error.message));
		await loginAsAdministrator(page);

		await page.goto(ROUTE);
		const root = page.getByTestId('cm-root');
		await expect(root).toHaveAttribute('data-screen', 'workspace');
		await expect(page.getByTestId('cm-empty')).toContainText('There are no contracts to show yet.');
		await expect(page.locator('.kt-rail-mount')).toContainText('Contracts');
		await expect(page.locator('.body-sidebar')).toContainText('Contracts');

		await page.reload();
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace');
		await expect(page.getByTestId('cm-empty')).toBeVisible();

		// The rail is not rebuilt, and keeps this app's own sidebar, across one-, two- and three-segment routes below the page: the Page names the real module
		// "Contract Management", and Frappe resolves a deeper route through the Page's module (the collision Departmental Needs hit on 30 Aug 2026).
		await page.evaluate(() => {
			(window as any).__railRemoved = 0;
			new MutationObserver((records) => {
				for (const r of records) for (const n of Array.from(r.removedNodes)) if (n instanceof Element && (n.matches('.body-sidebar') || n.querySelector('.body-sidebar'))) (window as any).__railRemoved++;
			}).observe(document.querySelector('.body-sidebar-container') || document.body, { childList: true, subtree: true });
		});
		for (const route of [['contracts', 'CM-DEMO-1'], ['contracts', 'CM-DEMO-1', 'tab'], ['contracts']]) {
			await page.evaluate((r) => (window as any).frappe.set_route(...r), route);
			await page.waitForTimeout(800);
			await expect(page.locator('.body-sidebar')).toContainText('Kentender Contracts');
		}
		expect(await page.evaluate(() => (window as any).__railRemoved)).toBe(0);

		await page.goto('/app/home');
		await expect(page).toHaveURL(/\/(app|desk)\/home/);
		await page.goBack();
		await expect(page).toHaveURL(/\/(app|desk)\/contracts/);
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace');
		await page.goForward();
		await expect(page).toHaveURL(/\/(app|desk)\/home/);
		expect(problems).toEqual([]);
	});

	test('a user with no part in contracts sees the shared denial, not an error', async ({ page, request }) => {
		// A throwaway desk user who holds no responsibility at all, created and removed through the API so no test data is left behind.
		const email = `cm.shell.nobody.${Date.now()}@test.example.test`;
		const password = `Cm-${Math.random().toString(36).slice(2)}-Aa1!`;
		const admin = await request.post('/api/method/login', { form: { usr: process.env.UI_ADMIN_USER || 'Administrator', pwd: process.env.UI_ADMIN_PASSWORD || '' } });
		expect(admin.ok()).toBeTruthy();
		const created = await request.post('/api/resource/User', { data: { email, first_name: 'CM Shell Nobody', enabled: 1, send_welcome_email: 0, new_password: password, roles: [{ role: 'Desk User' }] } });
		expect(created.ok()).toBeTruthy();
		try {
			await login(page, email, password);
			await page.goto(ROUTE);
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace-forbidden');
			await expect(page.getByTestId('kt-access-denied')).toContainText('You do not have access to Contracts');
			await expect(page.getByTestId('cm-empty')).toHaveCount(0);
		} finally {
			await request.delete(`/api/resource/User/${encodeURIComponent(email)}`);
		}
	});

	test('a failed read is the load error with Retry and Back, Retry reloads, and no business action is offered', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.route(READ, (route) => route.fulfill({ status: 500, contentType: 'application/json', body: '{"exc_type":"ServerError"}' }));
		await page.goto(ROUTE);
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'error');
		const state = page.getByTestId('cm-load-error');
		await expect(state).toContainText('This record could not be loaded.');
		await expect(state.getByRole('button')).toHaveText(['Retry', 'Back to contracts']);
		await page.unroute(READ);
		await state.getByRole('button', { name: 'Retry' }).click();
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace');
		await expect(page.getByTestId('cm-empty')).toBeVisible();
	});
});
