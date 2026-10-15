import fs from 'node:fs';
import { expect, test, type Page } from '@playwright/test';
import { login } from '../../helpers/auth';

// CM-CHG-001 v0.8 plan Phase 12, tracker CM8-1204: a persona pass as real users. Each of the twelve people of the boards signs in on their own, finds the contract from the sidebar (or, for the supplier's two people, from
// the supplier portal), and opens every tab: each opens as a contract screen, with a status, with no refusal and no page error, and never as a Desk form (§17.12: no routine journey is a redirect to a native form).
// It reads the world of the demonstration profile in place (`make seed-cm-profile PROFILE=ACCEPTED PASSWORDS=1`); `make cm-persona-gate` builds it, walks it and cleans up.
const WORLD = process.env.CM_DEMO_WORLD || 'artifacts/cm-demo-world.json';
const world = fs.existsSync(WORLD) ? JSON.parse(fs.readFileSync(WORLD, 'utf8')) : null;
const TABS = ['Agreement', 'Deliveries', 'Invoices', 'Obligations', 'History'];
const STAFF = ['charles', 'amina', 'julia', 'peter', 'grace', 'brian', 'josphat', 'beatrice', 'naomi', 'daniel'];
const SUPPLIER = ['mary', 'david'];

async function everyTab(page: Page) {
	for (const name of TABS) {
		await page.getByTestId(`cm-tab-${name.toLowerCase()}`).click();
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-refreshing', 'false', { timeout: 30_000 });
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
		await expect(page.getByTestId('cm-status')).toBeVisible();
		await expect(page.getByTestId('cm-refusal')).toHaveCount(0);
		expect(page.url(), `${name}: never a Desk form`).not.toMatch(/\/(app|desk)\/(contract-|purchase-|payment-)/);
	}
}

test.describe(`The persona pass on the ${world?.profile ?? 'demonstration'} profile`, () => {
	test.skip(!world, 'run `make seed-cm-profile PROFILE=ACCEPTED PASSWORDS=1` first');
	test.setTimeout(240_000);

	for (const persona of STAFF) {
		test(`${persona} finds the contract in the sidebar and opens every tab`, async ({ page }) => {
			const errors: string[] = [];
			page.on('pageerror', (error) => errors.push(error.message));
			await login(page, world.people[persona], world.password);
			await page.goto('/app/home');
			await page.locator('.body-sidebar').getByText('Contract Management', { exact: true }).click();
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace', { timeout: 30_000 });
			await page.getByTestId('cm-view-1').click(); // All contracts: reading is not a task
			const search = page.getByTestId('cm-filter-search');
			await search.fill(world.contract);
			await search.press('Enter');
			await expect(page.getByTestId(`cm-row-${world.contract}`)).toBeVisible({ timeout: 15_000 });
			await page.getByTestId(`cm-row-${world.contract}`).getByRole('link', { name: world.contract }).click();
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
			await everyTab(page);
			expect(errors, `${persona}: no page error`).toEqual([]);
		});
	}

	for (const persona of SUPPLIER) {
		test(`${persona} finds the contract in the supplier portal and opens every tab`, async ({ page }) => {
			const errors: string[] = [];
			page.on('pageerror', (error) => errors.push(error.message));
			await login(page, world.people[persona], world.password);
			await page.goto('/account');
			await page.locator('[data-kt-portal-nav="contracts"]').click();
			await expect(page).toHaveURL(/\/supplier\/contracts/);
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace', { timeout: 30_000 });
			const search = page.getByTestId('cm-filter-search');
			await search.fill(world.contract);
			await search.press('Enter');
			await expect(page.getByTestId(`cm-row-${world.contract}`)).toBeVisible({ timeout: 15_000 });
			await page.getByTestId(`cm-row-${world.contract}`).getByRole('link', { name: world.contract }).click();
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
			await everyTab(page);
			expect(errors, `${persona}: no page error`).toEqual([]);
		});
	}
});
