import { expect, test } from '@playwright/test';
import { pickRecord } from '../../helpers/picker';
import { as, attr, board, nextStep, openAsSupplier as supplierOpen, openContract as open, pdf, press, tab, today, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 4, tracker CM8-416 / gate CM-G04: the ordinary thread walked in a real browser, one session per person, from the menu: prepare, sign twice, appoint inspectors,
// declare, receive, inspect, certify, accept (8 of 10), invoice, certify, Finance (accounting invoice, payment, settlement), the two replacement units, completion, close-out.
// Each screen is verified on first paint and again after the command it offers (the page re-renders in place), the record survives a reload and Back/Forward, and nobody is sent to a Desk form.
// Run `make cm-ui-world` first (the people, the ERPNext world and the received Award package); `make cm-ui-gate` does both and cleans up. The source handoff is synthetic (L1) and so is the
// funding owner: this spec proves the screens and the ordinary thread, not package acceptance.
const openContract = (page: Parameters<typeof open>[0], view: 'My work' | 'All contracts' = 'All contracts') => open(page, world.contract, view);
const openAsSupplier = (page: Parameters<typeof supplierOpen>[0]) => supplierOpen(page, world.contract);

test.describe('The ordinary contract thread', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(600_000);
	test.describe.configure({ mode: 'serial' });
	const stamp = Date.now().toString(36).toUpperCase();
	const first = Array.from({ length: 10 }, (_, i) => `UI${stamp}-${String(i + 1).padStart(3, '0')}`);
	const second = Array.from({ length: 2 }, (_, i) => `UI${stamp}-R${i + 1}`);

	test('from the Award package to a signed, active agreement', async ({ browser }) => {
		await as(browser, 'charles', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D02')).toBeVisible();
			await expect(page.getByTestId('cm-status')).toHaveText('Preparing');
			await expect(nextStep(page)).toContainText('Your turn');
			// the agreement cannot be sent until the particulars the issued terms do not supply are complete
			await expect(page.getByTestId('cm-primary')).toHaveText('Save particulars');
			await expect(page.getByTestId('cm-secondary-send-for-signature')).toBeDisabled();
			await page.getByTestId('cm-input-agreement_date').fill(today);
			await pickRecord(page, '#cm-f-entity_signatory', 'Amina');
			await pickRecord(page, '[id="cm-f-item_mapping.L1"]', world.item);
			await pickRecord(page, '#cm-f-native_supplier', world.supplier);
			await pickRecord(page, '#cm-f-asset_location', world.location);
			await press(page);
			await expect(page.getByTestId('cm-primary')).toHaveText('Send for signature');
			await expect(page.getByRole('heading', { name: 'Particulars to complete' })).toHaveCount(0);
			// the record survives a reload and Back/Forward
			await page.reload();
			await expect(board(page, 'D02')).toBeVisible();
			await press(page); // Send for signature
			await expect(page.getByTestId('cm-status')).toHaveText('Awaiting signatures');
			await expect(nextStep(page)).toContainText('Waiting on someone');
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
		});

		await as(browser, 'mary', async (page) => {
			await openAsSupplier(page);
			await expect(board(page, 'D03')).toBeVisible();
			await expect(page.getByTestId('cm-back')).toContainText('Back to my contracts');
			await expect(page.getByRole('button', { name: 'Finance' })).toHaveCount(0);
			await press(page); // Sign contract
			await expect(nextStep(page)).toContainText('Waiting on someone');
		});

		await as(browser, 'amina', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D03-A')).toBeVisible();
			await expect(page.getByRole('heading', { name: 'Signatures' })).toBeVisible();
			await press(page); // Sign contract
			await expect(page.getByTestId('cm-status')).toHaveText('Active');
		});
	});

	test('the inspectors are recommended, appointed and declare, in order', async ({ browser }) => {
		await as(browser, 'charles', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D23-R')).toBeVisible();
			await pickRecord(page, '#cm-f-chair', 'Julia');
			await pickRecord(page, '#cm-f-member_technical', 'Peter Mugo');
			await pickRecord(page, '#cm-f-member_other', 'Brian');
			await press(page);
			await expect(nextStep(page)).toContainText('Waiting on someone');
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D23')).toBeVisible();
			await expect(page.getByRole('heading', { name: 'Proposed members' })).toBeVisible();
			await page.getByTestId('cm-primary').click(); // opens the appointment dialog; nothing is appointed yet
			await expect(page.getByTestId('cm-dialog')).toContainText('Appoint inspectors');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await expect(nextStep(page)).not.toContainText('Your turn');
		});
		for (const who of ['julia', 'peter', 'brian']) {
			await as(browser, who, async (page) => {
				await openContract(page, 'My work');
				await expect(board(page, 'D24')).toBeVisible();
				await page.locator('label.radio', { hasText: 'I have a conflict of interest' }).click();
				await expect(page.getByTestId('cm-input-conflict')).toBeVisible(); // the conflict's description appears when a conflict is chosen
				await page.locator('label.radio', { hasText: 'I have no conflict of interest' }).click();
				await expect(page.getByTestId('cm-input-conflict')).toHaveCount(0);
				await press(page);
				await expect(nextStep(page)).not.toContainText('Your turn');
			});
		}
		await as(browser, 'charles', async (page) => {
			await openContract(page);
			await tab(page, 'Agreement');
			await expect(page.locator('[data-testid="cm-root"]')).toContainText('Julia Njeri');
		});
	});

	async function receive(browser: Browser, units: string[], replaces: string[] = []) {
		await as(browser, 'grace', async (page) => {
			await openContract(page);
			await tab(page, 'Deliveries');
			await page.getByTestId('cm-primary').click(); // Record delivery
			await expect(board(page, 'D04')).toBeVisible();
			await page.getByRole('button', { name: 'Enter unit references' }).click();
			await page.getByTestId(`cm-input-units.L1`).fill(units.join('\n'));
			await page.getByTestId('cm-dialog-primary').click(); // Use references
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await expect(page.locator('table.table')).toContainText(units.length > 3 ? `${units[0]}–${units[units.length - 1]}` : units.join(', '));
			await page.getByTestId('cm-input-supplier_reference').fill(`AFYA-DN-${units.length}`);
			await page.getByTestId('cm-input-received_at').fill('2027-07-12T10:00');
			await page.getByTestId('cm-input-quantity.L1').fill(String(units.length));
			if (replaces.length) await page.getByTestId('cm-input-replaces').fill(replaces.join('\n')); // a replacement names the rejected units it replaces: that is what closes their issue
			await press(page);
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
			await expect(board(page, 'D04-S')).toBeVisible();
		});
	}

	async function inspect(browser: Browser, units: string[], failing: string[]) {
		await as(browser, 'peter', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D05')).toBeVisible();
			await page.getByTestId('cm-primary').click(); // Record observations
			for (const unit of units) {
				await page.getByTestId(`cm-input-obs.${unit}.C1`).fill('16');
				await page.getByTestId(`cm-input-obs.${unit}.C2`).fill('512');
				await page.getByTestId(`cm-input-obs.${unit}.C3`).selectOption(failing.includes(unit) ? 'No' : 'Yes');
			}
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await expect(board(page, 'D19')).toBeVisible(); // the findings are in and the technical certificate is his next step
			await expect(page.locator('[data-testid="cm-root"]')).toContainText(`${units.length - failing.length}`);
			await press(page); // Sign technical certificate
		});
	}

	async function accept(browser: Browser) {
		await as(browser, 'julia', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D06')).toBeVisible();
			await press(page); // Prepare report for signing
		});
		for (const who of ['julia', 'peter', 'brian']) {
			await as(browser, who, async (page) => {
				await openContract(page, 'My work');
				await expect(board(page, 'D07')).toBeVisible();
				await expect(page.getByRole('heading', { name: 'Signatures' })).toBeVisible();
				await press(page); // Sign report
			});
		}
	}

	test('ten laptops arrive; eight are inspected, certified and accepted', async ({ browser }) => {
		await receive(browser, first);
		await inspect(browser, first, first.slice(8));
		await accept(browser);
		await as(browser, 'charles', async (page) => {
			await openContract(page);
			await tab(page, 'Deliveries');
			// the accepted units are received into stock and assets; the rejected two are still in the supplier's custody
			await expect(page.locator('[data-testid="cm-root"]')).toContainText('Delivery position');
			await expect(page.locator('table.table').first()).toContainText('8');
		});
		await as(browser, 'grace', async (page) => {
			await openContract(page);
			await tab(page, 'Deliveries');
			await page.getByTestId('cm-secondary-record-collection-of-rejected-units').click();
			await expect(page.getByTestId('cm-input-units')).toHaveValue(new RegExp(first[8])); // the rejected units are offered, none typed
			await page.getByTestId('cm-input-evidence').fill('Supplier gate pass GP-77');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await expect(page.getByTestId('cm-secondary-record-collection-of-rejected-units')).toHaveCount(0);
		});
	});

	async function invoiceAndPay(browser: Browser, quantity: number, reference: string) {
		await as(browser, 'david', async (page) => {
			await openAsSupplier(page);
			await tab(page, 'Invoices');
			await page.getByTestId('cm-primary').click(); // Submit invoice
			await expect(board(page, 'D18')).toBeVisible();
			await page.getByTestId('cm-input-claim_reference').fill(reference);
			await page.getByTestId('cm-input-invoice_date').fill(today);
			await expect(page.getByTestId('cm-input-quantity.L1')).toHaveValue(String(quantity));
			await press(page);
			await expect(board(page, 'D09')).toBeVisible();
			await expect(page.locator('[data-testid="cm-root"]')).not.toContainText('Finance');
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D08-C')).toBeVisible();
			await press(page); // Sign certification
		});
		await as(browser, 'josphat', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D33')).toBeVisible();
			await press(page, 'cm-primary', 2); // Submit invoice for approval (saves, then submits)
		});
		await as(browser, 'beatrice', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D33-A')).toBeVisible();
			await press(page); // Approve accounting invoice
		});
		await as(browser, 'josphat', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D09-F')).toBeVisible();
			await page.getByTestId('cm-input-mode_of_payment').selectOption(world.mode);
			await pickRecord(page, '#cm-f-paid_from', 'CM Test Bank');
			await page.getByTestId('cm-input-reference_no').fill(`BANK-${reference}`);
			await press(page, 'cm-primary', 2); // Submit payment for approval (saves, then submits)
		});
		await as(browser, 'beatrice', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D17')).toBeVisible();
			await press(page); // Approve payment
			await expect(board(page, 'D17-S')).toBeVisible(); // a posted payment is not a settled one: the settlement is its own step
			await page.getByTestId('cm-input-effective_date').fill(today);
			await page.getByTestId('cm-input-evidence').fill(`Bank statement line for ${reference}`);
			await press(page); // Confirm payment
		});
	}

	test('the supplier invoices eight; procurement certifies; Finance prepares, approves, pays and confirms', async ({ browser }) => {
		await invoiceAndPay(browser, 8, `AFYA-${stamp}-1`);
	});

	test('the two replacements are delivered, accepted and paid, then the contract is completed and closed', async ({ browser }) => {
		await receive(browser, second, first.slice(8));
		await inspect(browser, second, []);
		await accept(browser);
		await invoiceAndPay(browser, 2, `AFYA-${stamp}-2`);
		await as(browser, 'charles', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D22')).toBeVisible();
			await press(page); // Sign and issue certificate
			await page.reload();
			await expect(board(page, 'D22-P')).toBeVisible(); // signed is not delivered: the head confirms that it reached the contractor, with the proof
			await page.getByTestId('cm-input-delivered_on').fill('2027-07-02');
			await page.getByTestId('cm-input-method').fill('Hand delivery to the supplier');
			await page.getByTestId('cm-input-reference').fill(`DISP-${stamp}`);
			const uploaded = page.waitForResponse((r) => r.url().includes('upload_file') && r.ok());
			await page.getByTestId('cm-input-evidence').setInputFiles(pdf('Delivery note'));
			await uploaded;
			await press(page); // Confirm delivery
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, 'My work');
			await expect(board(page, 'D11')).toBeVisible();
			await press(page); // Sign close-out
			await expect(page.getByTestId('cm-status')).toHaveText('Closed');
		});
		// the closed contract is still there for everyone who may read it, and nothing is waiting for anyone
		await as(browser, 'charles', async (page) => {
			await openContract(page);
			await expect(page.getByTestId('cm-status')).toHaveText('Closed');
			await tab(page, 'History');
			await expect(page.locator('table.table')).toContainText('Contract closed');
			await page.reload();
			await expect(page.getByTestId('cm-status')).toHaveText('Closed');
			await tab(page, 'Invoices');
			await page.goBack();
			await expect(page.locator('[data-tab="History"]')).toBeVisible();
			await page.goForward();
			await expect(page.locator('[data-tab="Invoices"]')).toBeVisible();
		});
	});
});
