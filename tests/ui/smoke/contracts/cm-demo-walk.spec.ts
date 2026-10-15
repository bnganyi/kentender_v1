import fs from 'node:fs';
import { expect, test, type Page } from '@playwright/test';
import { login } from '../../helpers/auth';

// CM-CHG-001 v0.8 plan Phase 11, tracker CM8-1103: the demonstration walked as real people, one browser session each, from the three ways a person finds their work: the sidebar and the contract list, the Home page's
// My work, and the bell. Each profile (`make seed-cm-profile`) names who has a step on its contract and what it says; this spec looks for that step the three ways and opens it, and for a stage that leaves nobody a step it
// checks the contract is there and reads as the stage says. `make cm-demo-gate` builds each profile, walks it and cleans up. Run with `CM_DEMO_WORLD` to read another world file.
const WORLD = process.env.CM_DEMO_WORLD || 'artifacts/cm-demo-world.json';
const world = fs.existsSync(WORLD) ? JSON.parse(fs.readFileSync(WORLD, 'utf8')) : null;
const STATUS: Record<string, string> = { RECEIVED: 'Preparing', SIGNING: 'Awaiting signatures', CLOSED: 'Closed' };

async function inAs(page: Page, email: string) {
	await login(page, email, world.password);
}

async function openFromList(page: Page, everything = false) {
	await page.goto('/app/home');
	await page.locator('.body-sidebar').getByText('Contract Management', { exact: true }).click();
	await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace', { timeout: 30_000 });
	if (everything) await page.getByTestId('cm-view-1').click(); // the list opens on My work: a stage that leaves the person nothing to do is in All contracts
	const search = page.getByTestId('cm-filter-search');
	await search.fill(world.contract);
	await search.press('Enter');
	await expect(page.getByTestId(`cm-row-${world.contract}`)).toBeVisible({ timeout: 15_000 });
}

async function arrivedOnTheContract(page: Page, headline: string) {
	await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board', { timeout: 30_000 });
	await expect(page.getByTestId('cm-next-step')).toContainText(headline);
	expect(page.url(), 'a contract screen, never a Desk form').not.toMatch(/\/(app|desk)\/contract-case/);
}

test.describe(`The ${world?.profile ?? 'demonstration'} profile`, () => {
	test.skip(!world, 'run `make seed-cm-profile PROFILE=<name> PASSWORDS=1` first');
	test.setTimeout(240_000);

	for (const step of world?.steps ?? []) {
		test(`${step.persona} finds "${step.headline}" from the sidebar, from My work and from the bell`, async ({ page }) => {
			await inAs(page, step.email);

			// the sidebar and the contract list: the contract is in their list with the step as its next action
			await openFromList(page);
			await expect(page.getByTestId(`cm-row-${world.contract}`)).toContainText(step.headline);
			await page.getByTestId(`cm-row-${world.contract}`).getByRole('link', { name: world.contract }).click();
			await arrivedOnTheContract(page, step.headline);

			// the Home page's My work: one row for the contract, and Continue opens the step
			await page.goto('/app/home');
			const mine = page.getByTestId('kt-home-row').filter({ hasText: world.contract }).filter({ hasText: step.headline });
			await expect(mine).toHaveCount(1, { timeout: 30_000 });
			await expect(mine.getByText('Contracts', { exact: true })).toBeVisible();
			await mine.getByTestId('kt-home-continue').first().click();
			await arrivedOnTheContract(page, step.headline);

			// the bell: the alert for this step opens the contract on the step's own tab
			await page.goto('/app/home');
			await page.getByText('Notification', { exact: true }).first().click();
			await page.getByText(step.headline, { exact: true }).first().click();
			await expect(page).toHaveURL(new RegExp(`/contracts/${world.contract}/`));
			await arrivedOnTheContract(page, step.headline);
		});
	}

	test('the contract is in the head of procurement\'s list and reads as the stage says', async ({ page }) => {
		await inAs(page, 'charles.mutiso@moh.example.test');
		await openFromList(page, true);
		const row = page.getByTestId(`cm-row-${world.contract}`);
		if (STATUS[world.profile]) await expect(row).toContainText(STATUS[world.profile]);
		await row.getByRole('link', { name: world.contract }).click();
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board', { timeout: 30_000 });
		if (STATUS[world.profile]) await expect(page.getByTestId('cm-status')).toHaveText(STATUS[world.profile]);
	});

	test('what a person did is recently completed on their Home page', async ({ page }) => {
		const acts: Record<string, [string, string]> = { SIGNING: ['mary.wanjiku@afyadigital.example', ''], CLOSED: ['amina.hassan@moh.example.test', 'closed the contract'] };
		test.skip(!acts[world.profile] || !acts[world.profile][1], 'this stage records no act worth listing for a Home reader');
		await inAs(page, acts[world.profile][0]);
		await page.goto('/app/home');
		const done = page.getByTestId('kt-home-region-completed');
		await expect(done).toContainText(acts[world.profile][1], { timeout: 30_000 });
		await expect(done).toContainText('IT equipment delivery');
	});
});
