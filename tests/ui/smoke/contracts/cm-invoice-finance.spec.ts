import { expect, test } from '@playwright/test';
import { as, board, nextStep, openAsSupplier, openContract, press, tab, today, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 7, tracker CM8-707: the supplier's claim in a real browser. The contract is staged by the services: eight units accepted, a first claim of three, and a second claim with the same
// invoice number that was held for Finance as an apparent duplicate. Finance sets the repeat aside; procurement certifies the first; the supplier claims more than the contract supports, procurement asks for a
// correction and the supplier corrects it. Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
test.describe('The supplier claim', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(600_000);
	test.describe.configure({ mode: 'serial' });
	const contract = () => world.claims_contract;

	test('Finance sets an apparent duplicate aside with a reason and it keeps no entitlement', async ({ browser }) => {
		await as(browser, 'josphat', async (page) => {
			await openContract(page, contract(), 'My work');
			await expect(board(page, 'D08-D')).toBeVisible();
			await expect(nextStep(page)).toContainText('appears to repeat another');
			await expect(page.getByTestId('cm-root')).toContainText('This appears to repeat invoice DUP-1.');
			await page.getByTestId('cm-primary').click(); // Set aside as duplicate
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toContainText('Enter why.'); // a decision without a reason is not recorded
			await page.getByTestId('cm-input-reason').fill('The same supplier invoice was sent twice.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await page.reload();
			await expect(board(page, 'D08-D')).toHaveCount(0); // it is no longer waiting for Finance
		});
	});

	test('the supplier claims more than is supported, procurement asks for a correction and the supplier corrects it', async ({ browser }) => {
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract(), 'My work');
			await expect(board(page, 'D08-C')).toBeVisible(); // the first claim, matched: certified before anything else
			await press(page); // Sign certification
		});
		await as(browser, 'david', async (page) => {
			await openAsSupplier(page, contract());
			await tab(page, 'Invoices');
			await page.getByTestId('cm-primary').click(); // Submit invoice
			await expect(board(page, 'D18')).toBeVisible();
			await expect(page.getByTestId('cm-input-quantity.L1')).toHaveValue('5'); // eight accepted, three claimed already: the repeat holds nothing
			await page.getByTestId('cm-input-claim_reference').fill(`CLAIM-${today}`);
			await page.getByTestId('cm-input-invoice_date').fill(today);
			await page.getByTestId('cm-input-quantity.L1').fill('6');
			await press(page);
			await expect(page.getByTestId('cm-root')).toContainText('Waiting on someone');
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract(), 'My work');
			await expect(board(page, 'D08')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Some units have not been accepted.');
			await expect(page.getByTestId('cm-root').locator('tr', { hasText: 'Laptop computer' }).first().locator('td')).toHaveText(['Laptop computer', '6', '5', 'KES 100,000', 'KES 600,000', 'KES 500,000']); // invoiced, eligible, claimed, supported
			await page.getByTestId('cm-primary').click(); // Request correction
			await page.getByTestId('cm-input-reason').fill('Please correct the invoice to match the five accepted laptops.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
		});
		await as(browser, 'david', async (page) => {
			await openAsSupplier(page, contract());
			await tab(page, 'Invoices');
			await expect(board(page, 'D18-C')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('(retained)'); // the claim as first sent is kept
			await expect(page.getByTestId('cm-input-quantity.L1')).toHaveValue('5'); // the held claim no longer holds what its correction will take
			await page.getByTestId('cm-input-reason').fill('Corrected to the five accepted laptops.');
			await press(page); // Submit correction
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract(), 'My work');
			await expect(board(page, 'D08-C')).toBeVisible(); // the corrected claim matches: certification is the next step
			await expect(page.getByTestId('cm-root')).toContainText('KES 500,000');
		});
	});
});
