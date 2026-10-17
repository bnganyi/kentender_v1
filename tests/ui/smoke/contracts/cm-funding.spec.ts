import { execSync } from 'node:child_process';
import path from 'node:path';
import { expect, test } from '@playwright/test';
import { as, board, nextStep, press, tab, world } from './helpers';

// CM-CHG-001 v0.10 section 10.9 and CM-AC-94 (BUD-CHG-001 v1.16, BUD25-AC-009): how an independently registered contract is funded, walked as the real people from the menu, with the real Budget owner
// receiving the request. The head of procurement records the route and the year share; Finance preparation prepares the year's basis; a different Finance approval holder confirms it; the head raises
// the request and Contract Management says Funding entry pending; Budget's Officer finds the request in Budget, allocates it and submits it; the Budget Approver who confirmed the year's basis is refused; the second Budget Approver, who confirmed nothing, approves it; the contract then shows the year funded. Run after `cm-existing-contract.spec.ts` in the same world (`make cm-ui-world` first): it
// uses the contract that spec registered and started. Test site only.
const BENCH_ROOT = path.resolve(__dirname, '../../../../../..');

const slug = (label: string) => label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');

function registered(): string {
	const out = execSync(
		`cd "${BENCH_ROOT}" && bench --site kentender-test.local execute frappe.client.get_value --kwargs '{"doctype": "Contract Case", "filters": {"source_kind": "External record", "lifecycle": "Active"}, "fieldname": "name"}'`,
		{ stdio: 'pipe', encoding: 'utf8', timeout: 120_000 },
	);
	const found = out.split('\n').find((line) => line.includes('"name"')) || '';
	return (JSON.parse(found).name as string) || '';
}

test.describe('Funding an independently registered contract', () => {
	test.skip(!world, 'run `make cm-ui-world` and the existing-contract spec first');
	test.setTimeout(600_000);
	test.describe.configure({ mode: 'serial' });
	let contract = '';
	let year = '';

	// The request lives in the canonical Budget, which the Contract Management world's clean-up does not reach: take away what this contract left there, so the shared Budget keeps no work item for a contract that no longer exists.
	test.afterAll(() => {
		if (!contract) return;
		execSync(
			`cd "${BENCH_ROOT}" && bench --site kentender-test.local execute kentender_budget.seeds.funding_ui_fixtures.remove_contract_requests --kwargs '{"contract": "${contract}"}'`,
			{ stdio: 'pipe', encoding: 'utf8', timeout: 120_000 },
		);
	});

	const openFunding = async (page: import('@playwright/test').Page) => {
		await page.goto('/app/home');
		await page.locator('.body-sidebar').getByText('Contract Management', { exact: true }).click();
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace', { timeout: 30_000 });
		await page.getByTestId('cm-view-1').click(); // All contracts
		const search = page.getByTestId('cm-filter-search');
		await search.fill(contract);
		await search.press('Enter');
		await page.getByTestId(`cm-row-${contract}`).getByRole('link', { name: contract }).click();
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
		await tab(page, 'Agreement');
		await page.getByTestId('cm-secondary-open-funding-review').click();
		await expect(board(page, 'D21-F')).toBeVisible();
	};

	test('the head records the route and the year share; before it the contract says it is not linked to Budget', async ({ browser }) => {
		contract = registered();
		expect(contract, 'the existing-contract spec registered and started a contract').toBeTruthy();
		await as(browser, 'charles', async (page) => {
			await openFunding(page);
			await expect(page.getByTestId('cm-root')).toContainText('Not yet recorded');
			await page.getByTestId('cm-secondary-record-funding-route').click();
			await expect(page.getByTestId('cm-dialog')).toBeVisible();
			const years = await page.getByTestId('cm-input-schedule.1.year').locator('option').allInnerTexts();
			expect(years.length, 'the dialog offers financial years before any is recorded').toBeGreaterThan(1);
			year = years[1];
			await page.getByTestId('cm-input-route').selectOption('KenTender Budget');
			await page.getByTestId('cm-input-authority').fill('Ministry Accounting Officer');
			await page.getByTestId('cm-input-approved_amount').fill('400000');
			await page.getByTestId('cm-input-evidence').fill('Funding authority letter 1');
			await page.getByTestId('cm-input-schedule.1.year').selectOption(year);
			await page.getByTestId('cm-input-schedule.1.amount').fill('400000');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await expect(page.getByTestId('cm-root')).toContainText('KenTender Budget');
			await expect(page.getByTestId('cm-root')).toContainText(year);
			await expect(page.getByTestId('cm-root')).toContainText('Year allocation required');
			await page.reload(); // the contract's agreement carries the funding section, and the way into the funding view stays one press away
			await expect(page.getByTestId('cm-root')).toContainText('Year allocation required');
			await page.getByTestId('cm-secondary-open-funding-review').click();
			await expect(board(page, 'D21-F')).toBeVisible();
		});
	});

	test('Finance preparation prepares the year\'s basis and cannot confirm it; a different Finance approval holder confirms it', async ({ browser }) => {
		await as(browser, 'josphat', async (page) => {
			await openFunding(page);
			await expect(page.getByTestId('cm-root')).toContainText('Year allocation required');
			await expect(page.getByTestId('cm-primary')).toHaveCount(0); // preparing is not confirming
			await page.getByTestId(`cm-secondary-${slug(`Prepare the funding basis for ${year}`)}`).click();
			await page.getByTestId('cm-input-charge').fill('400000');
			await page.getByTestId('cm-input-explanation').fill('Prior activity and the current-year obligation reconciled to the signed terms');
			await page.getByTestId('cm-input-evidence').fill('Signed contract 1\nOpening reconciliation 1\nYear allocation evidence 1');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
		});
		await as(browser, 'beatrice', async (page) => {
			await openFunding(page);
			await expect(page.getByTestId('cm-primary')).toContainText('Confirm the funding basis for');
			await press(page); // confirm
			await expect(page.getByTestId('cm-root')).toContainText('Funding entry pending' /* once requested */).catch(() => undefined);
			await page.reload();
			await expect(page.getByTestId('cm-root')).toContainText('KES 400,000');
		});
	});

	test('the head raises the one request for the year; Contract Management says Funding entry pending and Budget\'s Officer finds it', async ({ browser }) => {
		await as(browser, 'charles', async (page) => {
			await openFunding(page);
			await press(page, `cm-secondary-${slug(`Request funding for ${year}`)}`);
			await page.reload();
			await page.getByTestId('cm-secondary-open-funding-review').click();
			await expect(board(page, 'D21-F')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Funding entry pending');
			await expect(page.getByTestId(`cm-secondary-${slug(`Request funding for ${year}`)}`)).toHaveCount(0); // one request per year, never a second
			await expect(page.getByTestId(`cm-secondary-${slug(`Withdraw the request for ${year}`)}`)).toBeVisible(); // until Budget has funded it, the head may withdraw it
		});
		await as(browser, 'josphat', async (page) => {
			await page.goto('/app/budget-funding');
			await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute('data-screen', 'workspace', { timeout: 30_000 });
			await page.getByTestId('budget-fy-filter').selectOption(year); // Budget never picks a year for the reader: the Officer chooses the year the request is for
			const work = page.getByTestId('budget-funding-work').first();
			await expect(work).toContainText('Fund existing contract', { timeout: 30_000 });
			await expect(page.getByTestId('budget-funding-work-status').first()).toHaveText('Ready to prepare');
			await page.getByTestId('budget-funding-work-open').first().click();
			await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute('data-screen', 'funding', { timeout: 30_000 });
			await expect(page.getByTestId('bud-funding-required')).toHaveText('KES 400,000');
			await expect(page.getByTestId('bud-funding-next')).toContainText('Your turn — Allocate KES 400,000 to budget lines');
		});
		await as(browser, 'beatrice', async (page) => {
			// Beatrice confirmed the year's basis in Contract Management, so she may not approve the entry in Budget: the Budget screen says so and offers her no decision
			await page.goto('/app/budget-funding');
			await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute('data-screen', 'workspace', { timeout: 30_000 });
			await page.getByTestId('budget-fy-filter').selectOption(year);
			await expect(page.getByTestId('bud-ws-skeleton')).toHaveCount(0, { timeout: 30_000 });
			await expect(page.getByTestId('budget-funding-work')).toHaveCount(0); // nothing is awaiting her approval yet
		});
	});

	test('the Officer allocates and submits; the Approver who confirmed the year is refused in Budget; the second Approver approves; the contract shows the year funded', async ({ browser }) => {
		const workspace = async (page: import('@playwright/test').Page) => {
			await page.goto('/app/budget-funding');
			await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute('data-screen', 'workspace', { timeout: 30_000 });
			await page.getByTestId('budget-fy-filter').selectOption(year);
			await expect(page.getByTestId('bud-ws-skeleton')).toHaveCount(0, { timeout: 30_000 });
		};
		await as(browser, 'josphat', async (page) => {
			await workspace(page);
			await page.getByTestId('budget-funding-work-open').first().click();
			await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute('data-screen', 'funding', { timeout: 30_000 });
			await page.getByTestId('bud-funding-add').click();
			await page.getByTestId('bud-funding-line').nth(0).selectOption({ label: 'Digital health workforce development' }); // an Entity-wide line of the canonical Budget with room for the amount
			await page.getByTestId('bud-funding-amount').nth(0).fill('400000');
			await page.getByTestId('bud-funding-recon').fill("The year's charge is funded from the line it belongs to.");
			await expect(page.getByTestId('bud-funding-remaining')).toContainText('KES 0');
			await page.getByTestId('bud-funding-submit').click();
			await expect(page.getByTestId('bud-funding-entry-state')).toHaveText('Awaiting approval', { timeout: 30_000 });
		});
		await as(browser, 'beatrice', async (page) => {
			// she confirmed the year's basis in Contract Management, so the Budget screen says another Approver must decide, and offers her no approval
			await workspace(page);
			await page.getByTestId('budget-funding-work-open').first().click();
			await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute('data-screen', 'funding', { timeout: 30_000 });
			await expect(page.getByTestId('bud-funding-same-person')).toContainText('Another Budget Approver must decide', { timeout: 30_000 });
			await expect(page.getByTestId('bud-funding-next')).toContainText('Waiting on another Budget Approver');
			const approve = page.getByTestId('bud-funding-approve');
			if (await approve.count()) await expect(approve).toBeDisabled();
		});
		await as(browser, 'hellen', async (page) => {
			await workspace(page);
			await expect(page.getByTestId('budget-funding-work').first()).toContainText('Review contract funding');
			await page.getByTestId('budget-funding-work-open').first().click();
			await expect(page.locator('[data-testid="bud-shell"]')).toHaveAttribute('data-screen', 'funding', { timeout: 30_000 });
			await expect(page.getByTestId('bud-funding-header')).toContainText('Review contract funding');
			await expect(page.getByTestId('bud-funding-next')).toContainText('Your turn — Review the funding entry');
			await expect(page.getByTestId('bud-funding-same-person')).toHaveCount(0);
			await page.getByTestId('bud-funding-approve').click();
			const dialog = page.getByTestId('kt-confirm-dialog');
			await expect(dialog).toContainText('KES 400,000');
			await expect(dialog).toContainText('Approve funding entry');
			await page.getByTestId('kt-confirm-ok').click();
			await expect(page.getByTestId('bud-funding-approved')).toContainText('Funding entry approved', { timeout: 30_000 });
			await page.reload({ waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('bud-funding-approved')).toBeVisible({ timeout: 30_000 });
		});
		await as(browser, 'charles', async (page) => {
			await openFunding(page);
			await expect(page.getByTestId('cm-root')).toContainText('Funding entry approved');
			await expect(page.getByTestId(`cm-secondary-${slug(`Withdraw the request for ${year}`)}`)).toHaveCount(0); // funded: nothing left to withdraw
			await expect(page.getByTestId(`cm-secondary-${slug(`Request funding for ${year}`)}`)).toHaveCount(0); // and no second request
		});
	});
});
