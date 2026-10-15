import { expect, test } from '@playwright/test';
import { pickRecord } from '../../helpers/picker';
import { as, board, nextStep, pdf, press, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 5, tracker CM8-512: a contract signed before KenTender, registered, reviewed and started in a real browser. The preparer registers it from the Contracts list (saved while
// incomplete, then completed), Finance confirms the opening position against the native receipt and invoice it is linked to, and the head of procurement starts management: nobody is asked to sign.
// Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
test.describe('An existing signed contract', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(600_000);
	test.describe.configure({ mode: 'serial' });
	const existing = () => world.existing;
	let contract = '';

	test('the preparer registers it, saves it incomplete, completes it, and a second registration of the same contract is refused', async ({ browser }) => {
		await as(browser, 'brian', async (page) => {
			await page.goto('/app/home');
			await page.locator('.body-sidebar').getByText('Contract Management', { exact: true }).click();
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace');
			await page.getByRole('button', { name: 'Register existing contract' }).click();
			await expect(board(page, 'D12')).toBeVisible();
			await expect(nextStep(page)).toContainText('Record the signed contract and its current position.');
			// the source and the supplier are all it takes to save; the rest is named as still to give
			await page.getByTestId('cm-input-reference').fill(existing().reference);
			await page.getByTestId('cm-input-supplier_country').fill(existing().country);
			await page.getByTestId('cm-input-supplier_registration').fill(existing().registration);
			const uploaded = page.waitForResponse((r) => r.url().includes('upload_file') && r.ok());
			await page.getByTestId('cm-input-agreement_file').setInputFiles(pdf('existing-agreement'));
			await uploaded;
			await page.getByTestId('cm-input-signed_on').fill('2027-07-02');
			await page.getByTestId('cm-input-effective_on').fill('2027-07-02');
			await page.getByTestId('cm-input-cutover').fill('2027-08-03T00:00');
			await pickRecord(page, '#cm-f-owner', 'Julia');
			await pickRecord(page, '#cm-f-managing_unit', world.unit);
			await pickRecord(page, '#cm-f-entity_signatory', 'Amina');
			await page.getByTestId('cm-input-original_value').fill('1000000');
			await page.getByTestId('cm-input-current_value').fill('1000000');
			const row = (n: string, v: string) => page.getByTestId(`cm-input-row.1.${n}`).fill(v);
			await row('description', 'Laptop computer');
			await row('quantity', '10');
			await row('uom', 'Each');
			await row('rate', '100000');
			await row('accepted', '4');
			await row('in_custody', '2');
			await row('invoiced_quantity', '4');
			await page.getByTestId('cm-input-delivery_due').fill('2027-07-20');
			await page.getByTestId('cm-input-payment_days').fill('30');
			await page.getByTestId('cm-input-warranty_months').fill('12');
			await page.getByTestId('cm-input-security_required').selectOption('No');
			await page.getByTestId('cm-input-advance_allowed').selectOption('No');
			await page.getByTestId('cm-input-acceptance').fill('RAM | >= | 16 | GB\nStorage | >= | 512 | GB\nStarts successfully | = | Yes | ');
			await page.getByTestId('cm-input-clauses').fill('Agreement EXT-UI §§2-8');
			await page.getByTestId('cm-input-prior_activity').selectOption('Some');
			await page.getByTestId('cm-input-opening_invoiced').fill('400000');
			await page.getByTestId('cm-input-opening_credits').fill('0');
			await page.getByTestId('cm-input-opening_cash_paid').fill('0');
			await page.getByTestId('cm-input-opening_outstanding').fill('400000');
			await page.getByTestId('cm-input-opening_advance').fill('0');
			await page.getByTestId('cm-input-units_in_custody').fill('CM-UI-EXT-9\nCM-UI-EXT-10');
			await pickRecord(page, '#cm-f-link_purchase_receipt', existing().receipt);
			await pickRecord(page, '#cm-f-link_purchase_invoice', existing().invoice);
			await pickRecord(page, '#cm-f-native_supplier', world.supplier);
			await pickRecord(page, '#cm-f-asset_location', world.location);
			await press(page); // Save and review: the case exists, the catalogue item for the line is still to give
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
			await expect(page.getByTestId('cm-status')).toHaveText('Preparing');
			contract = (await page.getByTestId('cm-ref').innerText()).trim();
			await expect(page.getByTestId('cm-root')).toContainText('Still to give: catalogue item for each line');
			await pickRecord(page, '[id="cm-f-item_mapping.L1"]', world.item);
			await press(page); // revised: nothing is missing now
			await expect(page.getByTestId('cm-root')).not.toContainText('Still to give');
			await expect(nextStep(page)).toContainText('Waiting on someone');
		});
		await as(browser, 'brian', async (page) => {
			// the same contract a second time is one case, not two
			await page.goto('/app/home');
			await page.locator('.body-sidebar').getByText('Contract Management', { exact: true }).click();
			await page.getByRole('button', { name: 'Register existing contract' }).click();
			await page.getByTestId('cm-input-reference').fill(existing().reference);
			await page.getByTestId('cm-input-supplier_country').fill(existing().country);
			await page.getByTestId('cm-input-supplier_registration').fill(existing().registration);
			await page.getByTestId('cm-primary').click();
			await expect(page.getByTestId('cm-refusal')).toContainText('This submission may already be recorded.');
		});
	});

	test('Finance confirms the opening position and the head of procurement starts management; nobody is asked to sign', async ({ browser }) => {
		await as(browser, 'beatrice', async (page) => {
			await page.goto('/app/home');
			await page.locator('.body-sidebar').getByText('Contract Management', { exact: true }).click();
			await page.getByTestId('cm-view-1').click();
			await page.getByTestId(`cm-row-${contract}`).getByRole('link', { name: contract }).click();
			await expect(board(page, 'D21')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Custody record 2');
			await expect(page.getByTestId('cm-primary')).toHaveText('Confirm opening position');
			await press(page);
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
		});
		await as(browser, 'charles', async (page) => {
			await page.goto('/app/home');
			await page.locator('.body-sidebar').getByText('Contract Management', { exact: true }).click();
			await page.getByTestId('cm-view-1').click();
			await page.getByTestId(`cm-row-${contract}`).getByRole('link', { name: contract }).click();
			await expect(board(page, 'D21-H')).toBeVisible();
			await expect(page.getByTestId('cm-primary')).toHaveText('Start management');
			await press(page);
			await expect(page.getByTestId('cm-status')).toHaveText('Active');
			await expect(page.getByRole('button', { name: 'Sign contract' })).toHaveCount(0);
			await page.reload();
			await expect(page.getByTestId('cm-status')).toHaveText('Active');
		});
	});
});
