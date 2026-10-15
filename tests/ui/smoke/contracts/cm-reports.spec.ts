import { expect, test } from '@playwright/test';
import { as, board, nextStep, openContract, press, tab, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 8, tracker CM8-808: reporting in a real browser. The July progress report was generated from the records (with its cutoff); the head of procurement reviews and submits it, and the delivery
// to the Accounting Officer is recorded apart. A publication requirement nobody can yet state is shown as needing review with no deadline, and the head records source evidence for the legal owner. Run
// `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
test.describe('Reports and obligations', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(600_000);
	test.describe.configure({ mode: 'serial' });

	test('the head of procurement reviews and submits the generated monthly report', async ({ browser }) => {
		await as(browser, 'charles', async (page) => {
			await openContract(page, world.report_contract, 'My work');
			await expect(board(page, 'D15')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Review and submit the July 2027 report.');
			await expect(page.getByTestId('cm-root')).toContainText('Not included — reconcile before claiming full coverage');
			await press(page); // Submit report
			await tab(page, 'Obligations'); // the task is done: the submitted report is found among the contract's reports
			await page.getByRole('link', { name: 'Monthly contract progress July 2027' }).first().click();
			await expect(board(page, 'D15')).toBeVisible();
			await expect(nextStep(page)).toContainText('The July 2027 report was submitted');
			await expect(page.getByTestId('cm-root')).toContainText('Delivered'); // delivery to the Accounting Officer is recorded apart from the submission
			await expect(page.getByTestId('cm-primary')).toHaveCount(0); // submitted rows are immutable: nothing more to press
		});
	});

	test('a publication requirement that cannot be stated shows no deadline and takes source evidence for the legal owner', async ({ browser }) => {
		await as(browser, 'charles', async (page) => {
			await openContract(page, world.changes_contract, 'All contracts');
			await tab(page, 'Obligations');
			await expect(page.getByTestId('cm-root')).toContainText('Not confirmed — set by current directions');
			await page.getByRole('link', { name: 'Review publication' }).first().click();
			await expect(board(page, 'D15-L')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Award decision recorded 17 Jun 2027');
			await expect(page.getByTestId('cm-root')).toContainText('Not confirmed — set by current directions');
			await page.getByRole('button', { name: 'Record source evidence' }).first().click();
			await page.getByTestId('cm-input-reference').fill('PPRA circular 4/2027');
			await page.getByTestId('cm-input-dated').fill('2027-06-30');
			await page.getByTestId('cm-input-notes').fill('Names a 14-day period; for the legal owner to review.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await expect(page.getByTestId('cm-root')).toContainText('Needs review'); // evidence is a proposal: nothing became a deadline or a verified status
		});
	});
});
