import { expect, test, type Page } from '@playwright/test';
import { cmWorld, longDate } from "../../helpers/anchor";
import { pickRecord } from '../../helpers/picker';
import { as, board, openContract, pdf, press, tab, today, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 8, tracker CM8-808: a warranty claim and a security claim in a real browser. Warranty: the coordinator records the fault on an accepted unit, sends the defect notice, records the collection of the
// unit, and Finance names the native return that carries it. Security: the head of procurement requests a claim on the verified instrument, the Accounting Officer approves the exact claim, the delivery to the issuer
// and then the issuer's outcome are recorded as their own facts. Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
async function attach(page: Page, field: string, label: string) {
	const uploaded = page.waitForResponse((r) => r.url().includes('upload_file') && r.ok());
	await page.getByTestId(`cm-input-${field}`).setInputFiles(pdf(label));
	await uploaded;
	await expect(page.getByTestId('cm-root')).toContainText(`cm-ui-${label.replace(/\W+/g, '-')}.pdf`);
}

test.describe('A warranty claim and a security claim', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(900_000);
	test.describe.configure({ mode: 'serial' });

	test('a warranty claim goes from the fault to the unit collected and Finance reconciling its return', async ({ browser }) => {
		const contract = world.warranty_contract;
		await as(browser, 'carol', async (page) => {
			await openContract(page, contract, 'All contracts');
			await tab(page, 'Obligations');
			await page.getByTestId('cm-secondary-record-a-warranty-claim').click();
			await expect(board(page, 'D16-N')).toBeVisible();
			await page.getByTestId('cm-input-unit').fill(world.warranty_units[3]);
			await page.getByTestId('cm-input-fault').fill('Battery does not charge');
			await page.getByTestId('cm-input-notice_date').fill(cmWorld('2028-06-01'));
			await press(page); // Record claim
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D16-W')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText(`Ends ${longDate(cmWorld('2028-07-02'))}`);
			await press(page); // Send notice
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D35')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Pending — Josphat Mwangi');
			await page.getByTestId('cm-primary').click(); // Record return
			await page.getByTestId('cm-input-collected_on').fill(today);
			await attach(page, 'evidence', 'Collection note WAR-01');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
		});
		await as(browser, 'josphat', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D35-F')).toBeVisible();
			await pickRecord(page, '[id="cm-f-return_document"]', world.warranty_return);
			await press(page); // Reconcile return
			await openContract(page, contract, 'All contracts');
			await tab(page, 'Obligations');
			await expect(page.getByTestId('cm-root').locator('tr', { hasText: 'Warranty claim' }).first()).toContainText('Awaiting reply');
		});
	});

	test('a security claim is requested, decided, delivered and answered, each its own fact', async ({ browser }) => {
		const contract = world.security_contract_actions;
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'All contracts');
			await tab(page, 'Obligations');
			await page.getByTestId('cm-secondary-request-security-claim').click();
			await expect(board(page, 'D37')).toBeVisible();
			await page.getByTestId('cm-primary').click(); // Request claim
			await page.getByTestId('cm-input-amount').fill('40000');
			await page.getByTestId('cm-input-grounds').fill('Failure to perform the unfulfilled obligation');
			await page.getByTestId('cm-input-mandate').fill('Reviewed test mandate 1');
			await attach(page, 'evidence', 'Default notice');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D37-A')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('KES 40,000');
			await page.getByTestId('cm-primary').click(); // Approve claim
			await page.getByTestId('cm-input-reason').fill('The exact claim is supported.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D37-C')).toBeVisible();
			await page.getByTestId('cm-input-sent_on').fill(cmWorld('2027-07-02'));
			await page.getByTestId('cm-input-channel').fill('Courier');
			await page.getByTestId('cm-input-reference').fill('CR-0042');
			await attach(page, 'evidence', 'Proof of delivery');
			await press(page); // Record delivery
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D37-P')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Not recorded'); // the issuer has not answered: a request or a decision is not a payment
			await page.getByTestId('cm-secondary-record-claim-outcome').click();
			await page.getByTestId('cm-input-issuer_reference').fill('TEST-SG-OUT-01');
			await page.getByTestId('cm-input-outcome_on').fill(cmWorld('2027-07-02'));
			await attach(page, 'evidence', 'Issuer outcome');
			await page.getByTestId('cm-input-proceeds').fill('40000');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await tab(page, 'History'); // the claim is answered and nothing is left to do: the contract's history is where it is read
			await expect(page.getByTestId('cm-root')).toContainText('their reference TEST-SG-OUT-01');
			await expect(page.getByTestId('cm-root')).toContainText('40,000.00 proceeds');
		});
	});
});
