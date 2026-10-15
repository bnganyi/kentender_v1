import { expect, test, type Page } from '@playwright/test';
import { pickRecord } from '../../helpers/picker';
import { as, board, openAsSupplier, openContract, pdf, press, tab, today, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 8, tracker CM8-808: a change to the contract in a real browser. The contract coordinator asks for a delivery extension with the supplier's request; the head of procurement names three reviewers
// by appointment reference; each declares no conflict, records and signs a recommendation; the head submits; the Accounting Officer approves; the supplier signs the amendment and then the entity; the change is effective and
// the register says so. A quantity above the 15% ceiling is refused with the limit it exceeds and nothing is recorded. Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
async function attach(page: Page, field: string, label: string) {
	const uploaded = page.waitForResponse((r) => r.url().includes('upload_file') && r.ok());
	await page.getByTestId(`cm-input-${field}`).setInputFiles(pdf(label));
	await uploaded;
	await expect(page.getByTestId('cm-root')).toContainText(`cm-ui-${label.replace(/\W+/g, '-')}.pdf`);
}

async function review(page: Page, contract: string, recommendation: string, reference = '') {
	await openContract(page, contract, 'My work');
	await expect(board(page, 'D27-V')).toBeVisible();
	await page.locator('label.radio', { hasText: 'No conflict' }).first().click();
	await page.getByTestId('cm-input-recommendation').fill(recommendation);
	if (reference) await page.getByTestId('cm-input-reference').fill(reference);
	await press(page); // Record review
	await expect(board(page, 'D27-S')).toBeVisible(); // the recommendation is read back before it is signed
	await press(page); // Sign review
}

test.describe('A change to the contract', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(900_000);
	test.describe.configure({ mode: 'serial' });
	const contract = () => world.changes_contract;

	test('a quantity above the ceiling is refused with the limit and records nothing', async ({ browser }) => {
		await as(browser, 'carol', async (page) => {
			await openContract(page, contract(), 'All contracts');
			await tab(page, 'Obligations');
			await page.getByTestId('cm-secondary-request-quantity-change').click();
			await expect(board(page, 'D34')).toBeVisible();
			await expect(page.getByTestId('cm-input-quantity.L1')).toHaveValue('11'); // one more unit at the issued rate: the rate is not a field
			await expect(page.getByTestId('cm-root')).toContainText('KES 1,100,000');
			await page.getByTestId('cm-input-quantity.L1').fill('12');
			await page.getByTestId('cm-input-reason').fill('Two more users need the same specified laptop.');
			await attach(page, 'evidence', 'Quantity request 1');
			await page.getByTestId('cm-primary').click();
			await expect(page.getByTestId('cm-refusal')).toContainText('20% above the original 10');
			await expect(page.getByTestId('cm-refusal')).toContainText('15%');
			await tab(page, 'Obligations');
			await expect(page.getByTestId('cm-root')).not.toContainText('Contract changes'); // nothing was recorded
		});
	});

	test('an extension is requested, reviewed, decided, signed by both parties and takes effect', async ({ browser }) => {
		await as(browser, 'carol', async (page) => {
			await openContract(page, contract(), 'All contracts');
			await tab(page, 'Obligations');
			await page.getByTestId('cm-secondary-request-delivery-extension').click();
			await expect(board(page, 'D27')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('20 Jul 2027');
			await page.getByTestId('cm-input-proposed_date').fill('2027-07-27');
			await page.getByTestId('cm-input-reason').fill('Supplier reports a seven-day shipment delay.');
			await attach(page, 'evidence', 'Supplier request 1');
			await press(page); // Request extension
			await expect(page.getByTestId('cm-root')).toContainText('Contract changes');
			await expect(page.getByTestId('cm-root')).toContainText('Delivery date to 27 Jul 2027');
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract(), 'My work');
			await expect(board(page, 'D27-N')).toBeVisible();
			await page.getByTestId('cm-input-reference').fill('AO/VAR/2027/001');
			await pickRecord(page, '[id="cm-f-reviewer.technical-review"]', 'Peter');
			await pickRecord(page, '[id="cm-f-reviewer.committee-recommendation"]', 'Faith');
			await pickRecord(page, '[id="cm-f-reviewer.legal-review"]', 'Brian');
			await press(page); // Appoint reviewers
		});
		await as(browser, 'peter', (page) => review(page, contract(), 'Approve date extension without price change'));
		await as(browser, 'faith', (page) => review(page, contract(), 'Approve date extension without price change'));
		await as(browser, 'brian', (page) => review(page, contract(), 'Approve date extension without price change'));
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract(), 'My work');
			await expect(board(page, 'D27-R')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('AO/VAR/2027/001');
			await expect(page.getByTestId('cm-root').locator('tr', { hasText: 'Peter Mugo' }).locator('td')).toContainText(['Peter Mugo', 'Technical review', 'No conflict']);
			await press(page); // Submit change for decision
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract(), 'My work');
			await expect(board(page, 'D14')).toBeVisible();
			await expect(page.getByTestId('cm-root').locator('tr', { hasText: 'Delivery date' }).locator('td')).toHaveText(['Delivery date', '20 July 2027', '27 July 2027']);
			await page.getByTestId('cm-primary').click(); // Approve extension
			await page.getByTestId('cm-input-reason').fill('The documented grounds support the revised date without changing price or quantity.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await page.reload();
			await expect(board(page, 'D14-P')).toBeVisible(); // approved, the amendment not yet effective
			await expect(page.getByTestId('cm-root')).toContainText('20 July 2027 — amendment not yet effective');
		});
		await as(browser, 'mary', async (page) => {
			await openAsSupplier(page, contract());
			await expect(board(page, 'D27-A')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Amended');
			await press(page); // Sign amendment
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract(), 'My work');
			await expect(board(page, 'D27-A')).toBeVisible(); // the entity signs the same version second
			await press(page); // Sign amendment
		});
		await as(browser, 'carol', async (page) => {
			await openContract(page, contract(), 'All contracts');
			await tab(page, 'Obligations');
			await expect(page.getByTestId('cm-root').locator('tr', { hasText: 'Change 1' }).locator('td')).toContainText(['Change 1', 'Delivery date to 27 Jul 2027', 'Effective']);
		});
	});
});
