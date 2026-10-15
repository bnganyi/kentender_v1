import { expect, test, type Page } from '@playwright/test';
import { as, board, openContract, pdf, press, tab, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 8, tracker CM8-808: a delay adjustment and a termination in a real browser. Delay: the head of procurement submits the system's proposal (KES 5,000, five days late) with the causation and clause,
// and the Accounting Officer approves the exact figure. Termination: the head of procurement requests it against the generated position, the Accounting Officer approves, the delivered notice is recorded and the contract becomes
// Terminated, the settlement is prepared and completed and the contract stays Terminated. Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
async function attach(page: Page, field: string, label: string) {
	const uploaded = page.waitForResponse((r) => r.url().includes('upload_file') && r.ok());
	await page.getByTestId(`cm-input-${field}`).setInputFiles(pdf(label));
	await uploaded;
	await expect(page.getByTestId('cm-root')).toContainText(`cm-ui-${label.replace(/\W+/g, '-')}.pdf`);
}

test.describe('A delay adjustment and a termination', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(900_000);
	test.describe.configure({ mode: 'serial' });

	test('the proposed delay adjustment is submitted with its causation and the Accounting Officer approves the exact figure', async ({ browser }) => {
		const contract = world.delay_contract;
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D36')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('5 calendar days (21–25 Jul inclusive)');
			await expect(page.getByTestId('cm-root')).toContainText('KES 1,000 per day × 5');
			await expect(page.getByTestId('cm-root')).toContainText('KES 5,000');
			await page.getByTestId('cm-primary').click(); // Submit adjustment for decision
			await page.getByTestId('cm-input-causation').fill('Supplier shipment delay');
			await page.getByTestId('cm-input-clause').fill('TEST-DELAY-01');
			await page.getByTestId('cm-input-supplier_response').fill('Requests exclusion of two days');
			await page.getByTestId('cm-input-recommendation').fill('No supported exclusion');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D36-A')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('No supported exclusion');
			await page.getByTestId('cm-primary').click(); // Approve adjustment
			await page.getByTestId('cm-input-reason').fill('Supplier-responsible five-day delay established.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
		});
	});

	test('a termination is requested, approved, its notice delivered, the contract terminated and its settlement completed', async ({ browser }) => {
		const contract = world.termination_contract;
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'All contracts');
			await tab(page, 'Obligations');
			await page.getByTestId('cm-secondary-request-termination').click();
			await expect(board(page, 'D20-N')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('KES 800,000'); // generated, not typed
			await page.getByTestId('cm-input-clause').fill('Contract clause 8');
			await page.getByTestId('cm-input-recommendation').fill('Terminate unperformed balance');
			await attach(page, 'evidence', 'Default notice and delivery proof');
			await press(page); // Request termination
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D20')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Material non-delivery');
			await page.getByTestId('cm-primary').click(); // Approve termination
			await page.getByTestId('cm-input-reason').fill('The grounds are established.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await page.reload();
			await expect(board(page, 'D20-P')).toBeVisible();
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D20-R')).toBeVisible();
			await page.getByTestId('cm-input-delivered_on').fill('2027-07-02');
			await page.getByTestId('cm-input-method').fill('Registered post');
			await page.getByTestId('cm-input-reference').fill('RP-0042');
			await page.getByTestId('cm-input-effective_on').fill('2027-07-02');
			await attach(page, 'evidence', 'Proof of delivery');
			await press(page); // Record delivery
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(page.getByTestId('cm-status')).toHaveText('Terminated'); // never Completed
			await expect(board(page, 'D39-P')).toBeVisible();
			await page.getByTestId('cm-primary').click(); // Submit settlement for completion
			await page.getByTestId('cm-input-finance_reference').fill('TERM-01');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D39')).toBeVisible();
			await page.getByTestId('cm-primary').click(); // Complete settlement
			await page.getByTestId('cm-input-reason').fill('All required settlement facts reconciled.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await page.reload();
			await tab(page, 'Obligations'); // no work is left for the Accounting Officer, so the contract opens on its agreement
			await expect(board(page, 'D39-C')).toBeVisible();
			await expect(page.getByTestId('cm-status')).toHaveText('Terminated'); // the settlement is its own fact: the lifecycle stays Terminated
		});
	});
});
