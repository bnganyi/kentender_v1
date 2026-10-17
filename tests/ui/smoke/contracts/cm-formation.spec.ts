import { expect, test } from '@playwright/test';
import { cmWorld } from "../../helpers/anchor";
import { pickRecord } from '../../helpers/picker';
import { as, board, nextStep, openAsSupplier, openContract, pdf, press, today, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 5, tracker CM8-512 / gate CM-G05 (the screens): formation walked in a real browser, one session per person, from the menu. Three contracts of the world, each with the issued
// terms its name says: one that requires a performance security (CM-UI-0002), one that permits signing outside the system (CM-UI-0003), one that does not proceed (CM-UI-0004).
// Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up. The sources are synthetic (L1): the real owners' answer is `make cm-seams-gate`, whose report names the sources the canonical award
// cannot yet be formed from. This spec proves the screens and the rules they enforce, not package acceptance.
// the world runs on the seed world's own timeline (2 July 2027): dates the server checks against its clock are that clock's, not the machine's
const NOW = cmWorld('2027-07-02');
const ISSUED = cmWorld('2027-07-01');
const EXPIRES = cmWorld('2028-08-31');

async function prepare(page: import('@playwright/test').Page) {
	await expect(page.getByTestId('cm-primary')).toHaveText('Save particulars');
	await page.getByTestId('cm-input-agreement_date').fill(today);
	await pickRecord(page, '#cm-f-entity_signatory', 'Amina');
	await pickRecord(page, '[id="cm-f-item_mapping.L1"]', world.item);
	await pickRecord(page, '#cm-f-native_supplier', world.supplier);
	await pickRecord(page, '#cm-f-asset_location', world.location);
	await press(page);
}

async function attach(page: import('@playwright/test').Page, field: string, label: string) {
	const uploaded = page.waitForResponse((r) => r.url().includes('upload_file') && r.ok());
	await page.getByTestId(`cm-input-${field}`).setInputFiles(pdf(label));
	await uploaded;
	await expect(page.getByTestId('cm-root')).toContainText(`cm-ui-${label.replace(/\W+/g, '-')}.pdf`);
}

test.describe('Formation: the performance security, signing outside the system, a contract that does not proceed', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(600_000);
	test.describe.configure({ mode: 'serial' });

	test('a required security is recorded, rejected once, replaced and verified before the agreement can be sent', async ({ browser }) => {
		const contract = world.security_contract;
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D02')).toBeVisible();
			await expect(page.getByTestId('cm-status')).toHaveText('Preparing');
			await prepare(page);
			// the issued terms require a security: the head of procurement's turn is to record it, and the agreement cannot yet be sent
			await expect(board(page, 'D25-R')).toBeVisible();
			await expect(nextStep(page)).toContainText('Record the performance security.');
			await page.getByTestId('cm-input-issuer').fill('Test Bank');
			await page.getByTestId('cm-input-reference').fill(`UI-G-${Date.now().toString(36)}`);
			await page.getByTestId('cm-input-amount').fill('100000');
			await page.getByTestId('cm-input-issued_on').fill(ISSUED);
			await page.getByTestId('cm-input-expires_on').fill(EXPIRES);
			await attach(page, 'attachment', 'guarantee-one');
			await press(page);
			// the instrument is recorded: the next step is to check the issuer's confirmation
			await expect(board(page, 'D25')).toBeVisible();
			await expect(nextStep(page)).toContainText("Check the issuer's confirmation.");
			await expect(page.getByTestId('cm-primary')).toHaveText('Verify security');
		});
		await as(browser, 'mary', async (page) => {
			await openAsSupplier(page, contract);
			await expect(page.getByTestId('cm-back')).toContainText('Back to my contracts');
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
			await expect(nextStep(page)).toContainText('Waiting on someone');
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D25')).toBeVisible();
			await page.getByTestId('cm-secondary-reject-security').click();
			await page.getByTestId('cm-input-reason').fill("The issuer could not confirm this instrument.");
			await press(page, 'cm-dialog-primary');
			await expect(board(page, 'D25-R')).toBeVisible(); // a replacement is asked for
		});
		await as(browser, 'mary', async (page) => {
			await openAsSupplier(page, contract);
			await expect(board(page, 'D25-J')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('The issuer could not confirm this instrument.');
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
		});
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await expect(board(page, 'D25-R')).toBeVisible();
			await page.getByTestId('cm-input-issuer').fill('Test Bank');
			await page.getByTestId('cm-input-reference').fill(`UI-G-R-${Date.now().toString(36)}`);
			await page.getByTestId('cm-input-amount').fill('100000');
			await page.getByTestId('cm-input-issued_on').fill(ISSUED);
			await page.getByTestId('cm-input-expires_on').fill(EXPIRES);
			await attach(page, 'attachment', 'guarantee-two');
			await press(page);
			await expect(board(page, 'D25')).toBeVisible();
			// a file is not a verification: the issuer's confirmation reference and the date it was received are asked for
			await page.getByTestId('cm-primary').click();
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toContainText("Enter the issuer's confirmation reference.");
			await page.getByTestId('cm-input-confirmation_reference').fill('TEST-CONF-UI-01');
			await page.getByTestId('cm-input-received_on').fill(NOW);
			await press(page, 'cm-dialog-primary');
			// verified: the same agreement can now be sent
			await expect(board(page, 'D02')).toBeVisible();
			await expect(page.getByTestId('cm-primary')).toHaveText('Send for signature');
			await press(page);
			await expect(page.getByTestId('cm-status')).toHaveText('Awaiting signatures');
		});
	});

	test('where the issued terms permit it, signed copies are recorded for each party and confirmed once, and nobody is asked to sign electronically', async ({ browser }) => {
		const contract = world.outside_contract;
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await prepare(page);
			await press(page); // Send for signature
			await expect(page.getByTestId('cm-status')).toHaveText('Awaiting signatures');
			await page.getByRole('link', { name: 'Record an outside signature' }).click();
			await expect(board(page, 'D26')).toBeVisible();
			await expect(nextStep(page)).toContainText("Record the supplier's signed agreement.");
			await expect(page.getByTestId('cm-input-signed_by')).toHaveValue('Mary Wanjiku');
			await page.getByTestId('cm-input-signed_on').fill(NOW);
			await attach(page, 'copy', 'supplier-signed-copy');
			await press(page);
			// the supplier's evidence is in; the entity's is still to be recorded
			await expect(board(page, 'D26')).toBeVisible();
			await expect(nextStep(page)).toContainText("Record the entity's signed agreement.");
			await expect(page.getByTestId('cm-input-signed_by')).toHaveValue('Amina Hassan');
			await page.getByTestId('cm-input-signed_on').fill(NOW);
			await attach(page, 'copy', 'entity-signed-copy');
			await press(page);
			// both copies are in: check them, then confirm
			await expect(board(page, 'D26-E')).toBeVisible();
			await expect(page.getByTestId('cm-status')).toHaveText('Awaiting signatures');
			await expect(page.getByRole('link', { name: /Signed agreement 1 — supplier/ })).toBeVisible();
			await expect(page.getByRole('link', { name: /Signed agreement 1 — entity/ })).toBeVisible();
			await press(page);
			await expect(page.getByTestId('cm-status')).toHaveText('Active');
			// nobody was asked to sign electronically and the record is not drawn as an electronic proof
			await page.getByTestId('cm-tab-history').click();
			await expect(page.getByTestId('cm-root')).toContainText('Outside signature');
		});
		await as(browser, 'amina', async (page) => {
			await openContract(page, contract, 'All contracts');
			await expect(page.getByRole('button', { name: 'Sign contract' })).toHaveCount(0);
		});
	});

	test('a contract that will not be formed is ended with a reason, and what was done stays', async ({ browser }) => {
		const contract = world.ending_contract;
		await as(browser, 'charles', async (page) => {
			await openContract(page, contract, 'My work');
			await prepare(page);
			await press(page); // Send for signature
			await expect(page.getByTestId('cm-status')).toHaveText('Awaiting signatures');
			await page.getByRole('link', { name: 'Record that the contract did not proceed' }).click();
			await expect(page.getByTestId('cm-dialog')).toBeVisible();
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toContainText('Enter the reason.');
			await page.getByTestId('cm-input-reason').fill('The supplier told us it will not sign.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-status')).toHaveText('Did not proceed');
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
		});
		await as(browser, 'mary', async (page) => {
			await openAsSupplier(page, contract);
			await expect(page.getByTestId('cm-status')).toHaveText('Did not proceed');
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
		});
	});
});
