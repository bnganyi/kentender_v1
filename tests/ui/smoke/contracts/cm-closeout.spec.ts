import { expect, test, type Page } from '@playwright/test';
import { cmWorld } from "../../helpers/anchor";
import { as, board, openContract, pdf, press, tab, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 9, tracker CM8-909: final acceptance, completion, the certificate's delivery, the close-out and its correction in a real browser. The Accounting Officer records the final acceptance, the
// head of procurement issues the completion certificate and then confirms that it reached the contractor, the Accounting Officer closes the contract. Later the head asks for a correction because the delivery was recorded
// without proof; the Accounting Officer reopens the contract, the delivery is confirmed again and the contract is closed a second time. Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
async function attach(page: Page, field: string, label: string) {
	const uploaded = page.waitForResponse((r) => r.url().includes('upload_file') && r.ok());
	await page.getByTestId(`cm-input-${field}`).setInputFiles(pdf(label));
	await uploaded;
	await expect(page.getByTestId('cm-root')).toContainText(`cm-ui-${label.replace(/\W+/g, '-')}.pdf`);
}

async function confirmDelivery(page: Page, reference: string, proof: string) {
	await page.getByTestId('cm-input-delivered_on').fill(cmWorld('2027-07-02'));
	await page.getByTestId('cm-input-method').fill('Hand delivery to the supplier');
	await page.getByTestId('cm-input-reference').fill(reference);
	await attach(page, 'evidence', proof);
	await press(page); // Confirm delivery
}

test.describe('Final acceptance to a closed contract, and its correction', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(900_000);
	test.describe.configure({ mode: 'serial' });

	test('the Accounting Officer records the final acceptance, the head completes it, delivers the certificate and the contract is closed', async ({ browser }) => {
		const contract = world.closeout_contract;
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D32')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Units accepted');
			await expect(page.getByTestId('cm-root')).toContainText('I record final acceptance on');
			await expect(page.getByTestId('cm-root')).toContainText('Whole contract — 10');
			await press(page); // Sign final acceptance
			await page.reload();
			await expect(page.getByTestId('cm-next-step')).not.toContainText('Review the final acceptance evidence.');
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D22')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Final acceptance');
			await expect(page.getByTestId('cm-root')).toContainText('Recorded');
			await press(page); // Sign and issue certificate
			await page.reload();
			await expect(board(page, 'D22-P')).toBeVisible(); // signed is not delivered: the head still has to confirm delivery
			await expect(page.getByTestId('cm-root')).toContainText('Not yet evidenced');
			await confirmDelivery(page, 'DISP-UI-01', 'Signed delivery note');
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D11')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Certificate 1');
			await expect(page.getByTestId('cm-root')).toContainText('I close this procurement contract');
			await press(page); // Sign close-out
			await page.reload();
			await expect(page.getByTestId('cm-status')).toHaveText('Closed');
			await tab(page, 'Obligations');
			await expect(board(page, 'D11-C')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Commitment closed by the funding owner');
		});
	});

	test('a correction is requested, the contract reopened, the delivery confirmed again and the contract closed a second time', async ({ browser }) => {
		const contract = world.closeout_contract;
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'All contracts');
			await tab(page, 'Obligations');
			await page.getByTestId('cm-secondary-request-close-out-correction').click();
			await expect(board(page, 'D38-P')).toBeVisible();
			await page.getByTestId('cm-input-reason').fill('Required completion certificate delivery was recorded without evidence');
			await attach(page, 'evidence', 'Delivery incident');
			await press(page); // Submit correction
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D38')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Keep closed with surviving work is unavailable');
			await page.getByTestId('cm-primary').click(); // Reopen contract
			await page.getByTestId('cm-input-reason').fill('Required completion evidence was not established.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await page.reload();
			await expect(page.getByTestId('cm-status')).toHaveText('Active');
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D38-R')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Closure 1');
			await expect(page.getByTestId('cm-root')).toContainText('Retained');
			await confirmDelivery(page, 'DISP-UI-02', 'Signed delivery note second');
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D11')).toBeVisible();
			await press(page); // Sign close-out, a second time
			await page.reload();
			await expect(page.getByTestId('cm-status')).toHaveText('Closed');
		});
	});
});
