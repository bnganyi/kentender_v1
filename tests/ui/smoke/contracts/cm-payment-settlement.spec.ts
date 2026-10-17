import { expect, test, type Page } from '@playwright/test';
import { cmWorld } from "../../helpers/anchor";
import { pickRecord } from '../../helpers/picker';
import { as, board, nextStep, openAsSupplier, openContract, press, tab, today, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 7, tracker CM8-707: payment in instalments and an advance, in a real browser. One contract has a certified invoice of KES 800,000 posted by Finance: it is paid KES 500,000 and
// then KES 300,000, each confirmed by an independent person, and the owner sees the invoice partly paid and then settled. Another has an advance: the supplier claims it, the custodian records the guarantee,
// procurement verifies it and signs, Finance pays and confirms, and the first invoice recovers part of it so the cash is less. Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
test.describe('Payment and the advance', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(900_000);
	test.describe.configure({ mode: 'serial' });

	async function prepare(page: Page, amount: string, reference: string) {
		await expect(board(page, 'D09-F')).toBeVisible();
		await page.getByTestId('cm-input-mode_of_payment').selectOption(world.mode);
		await pickRecord(page, '#cm-f-paid_from', 'CM Test Bank');
		await page.getByTestId('cm-input-amount').fill(amount);
		await page.getByTestId('cm-input-reference_no').fill(reference);
		await press(page, 'cm-primary', 2); // Submit payment for approval (saves, then submits)
	}

	async function approveAndSettle(page: Page, reference: string) {
		await expect(board(page, 'D17')).toBeVisible();
		await press(page); // Approve payment
		await expect(board(page, 'D17-S')).toBeVisible(); // a posted payment is not a settled one
		await page.getByTestId('cm-input-effective_date').fill(today);
		await page.getByTestId('cm-input-evidence').fill(`Bank statement line for ${reference}`);
		await press(page); // Confirm payment
	}

	test('KES 500,000 and then KES 300,000 settle one KES 800,000 invoice; the owner sees it partly paid and then settled', async ({ browser }) => {
		const contract = world.payments_contract;
		await as(browser, 'josphat', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(nextStep(page)).toContainText('Prepare the payment record.');
			await prepare(page, '500000', 'INST-1');
		});
		await as(browser, 'beatrice', async (page) => {
			await openContract(page, contract, 'My work');
			await approveAndSettle(page, 'INST-1');
		});
		await as(browser, 'julia', async (page) => {
			await openContract(page, contract);
			await tab(page, 'Invoices');
			await expect(board(page, 'D28')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('KES 500,000');
			await expect(page.getByTestId('cm-root')).toContainText('KES 300,000');
			await expect(page.getByTestId('cm-root')).toContainText('Partly paid');
		});
		await as(browser, 'josphat', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(nextStep(page)).toContainText('Prepare payment for the remaining 300,000.00.');
			await expect(page.getByTestId('cm-input-amount')).toHaveValue('300000.00'); // what is left, not the whole invoice
			await prepare(page, '300000', 'INST-2');
		});
		await as(browser, 'beatrice', async (page) => {
			await openContract(page, contract, 'My work');
			await approveAndSettle(page, 'INST-2');
		});
		await as(browser, 'julia', async (page) => {
			await openContract(page, contract);
			await tab(page, 'Invoices');
			await expect(board(page, 'D28-C')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('KES 800,000');
			await page.reload();
			await expect(board(page, 'D28-C')).toBeVisible();
		});
	});

	test('an advance follows its own route: claim, guarantee, certification, payment, and recovery on the first invoice', async ({ browser }) => {
		const contract = world.advance_contract;
		await as(browser, 'david', async (page) => {
			await openAsSupplier(page, contract);
			await tab(page, 'Invoices');
			await page.getByTestId('cm-secondary-claim-advance').click();
			await page.getByTestId('cm-input-claim_reference').fill('ADV-01');
			await expect(page.getByTestId('cm-input-amount')).toHaveValue('100000.00'); // the issued clause, not a figure the supplier chooses
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D29-H')).toBeVisible(); // nothing to sign while the guarantee is not verified
			await expect(page.getByTestId('cm-root')).toContainText('The advance guarantee has not been verified.');
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
		});
		await as(browser, 'josphat', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D29-G')).toBeVisible();
			await page.getByTestId('cm-input-issuer').fill('Test Bank');
			await page.getByTestId('cm-input-reference').fill('TEST-AG-01');
			await page.getByTestId('cm-input-issued_on').fill(cmWorld('2027-06-01'));
			await page.getByTestId('cm-input-expires_on').fill(cmWorld('2027-08-31'));
			await press(page); // Save guarantee
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D29-V')).toBeVisible();
			await page.getByTestId('cm-primary').click(); // Verify guarantee
			await page.getByTestId('cm-input-confirmation_reference').fill('TEST-AG-CONF-01');
			await page.getByTestId('cm-input-received_on').fill(cmWorld('2027-07-02'));
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D29')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('10% of KES 1,000,000 = KES 100,000');
			await press(page); // Sign advance certification
		});
		await as(browser, 'josphat', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(nextStep(page)).toContainText('Prepare the advance payment.');
			await prepare(page, '100000', 'ADV-BANK-1');
		});
		await as(browser, 'beatrice', async (page) => {
			await openContract(page, contract, 'My work');
			await approveAndSettle(page, 'ADV-BANK-1');
		});
		// the first invoice recovers KES 80,000 of the advance: procurement sees it before signing, Finance pays the rest
		await as(browser, 'david', async (page) => {
			await openAsSupplier(page, contract);
			await tab(page, 'Invoices');
			await page.getByTestId('cm-primary').click(); // Submit invoice
			await page.getByTestId('cm-input-claim_reference').fill(`ADV-INV-${today}`);
			await page.getByTestId('cm-input-invoice_date').fill(today);
			await press(page);
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D29-R')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('KES 80,000');
			await expect(page.getByTestId('cm-root')).toContainText('KES 720,000');
			await press(page); // Sign certification
		});
		await as(browser, 'josphat', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D33')).toBeVisible();
			await press(page, 'cm-primary', 2); // Submit invoice for approval (saves, sets the recovery against it, submits)
		});
		await as(browser, 'beatrice', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D33-A')).toBeVisible();
			await press(page); // Approve accounting invoice
		});
		await as(browser, 'josphat', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D09-F')).toBeVisible();
			await expect(page.getByTestId('cm-input-amount')).toHaveValue('720000.00'); // the cash after the recovery
			await prepare(page, '720000', 'ADV-BANK-2');
		});
		await as(browser, 'beatrice', async (page) => {
			await openContract(page, contract, 'My work');
			await approveAndSettle(page, 'ADV-BANK-2');
		});
	});
});
