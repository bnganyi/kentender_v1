import { expect, test } from '@playwright/test';
import { as, board, nextStep, openContract, press, world } from './helpers';

// CM-CHG-001 v0.8 plan Phase 6, tracker CM8-606: what the people of an inspection committee can do with a frozen acceptance report in a real browser, and a related service that is evidenced rather than
// received. The contracts are staged by the services to the step each walk starts from (`tests/browser_world.py`): goods inspected, confirmed and the report prepared, with acceptance left to the
// Accounting Officer; and a training session recorded as performed. Run `make cm-ui-world` first; `make cm-ui-gate` does both and cleans up.
test.describe('Delivery, inspection and acceptance', () => {
	test.skip(!world, 'run `make cm-ui-world` first');
	test.setTimeout(600_000);
	test.describe.configure({ mode: 'serial' });
	const goods = () => world.delivery_contract;
	const service = () => world.service_contract;

	test('a member sends the report back, the chair prepares it again, and a member signs with a dissent', async ({ browser }) => {
		await as(browser, 'julia', async (page) => {
			await openContract(page, goods(), 'My work');
			await expect(board(page, 'D07')).toBeVisible();
			await expect(nextStep(page)).toContainText('Sign the acceptance report.');
			await page.getByTestId('cm-secondary-request-correction').click();
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toContainText('Give the reason for the correction.'); // a correction without a reason is not sent
			await page.getByTestId('cm-input-reason').fill('One unit is listed under the wrong delivery.');
			await press(page, 'cm-dialog-primary');
			await expect(board(page, 'D06')).toBeVisible(); // as chair, she is asked to correct it
			await expect(page.getByTestId('cm-root')).toContainText('One unit is listed under the wrong delivery.');
			await press(page); // Prepare report for signing
			await expect(board(page, 'D07')).toBeVisible();
			await press(page); // Sign report (report 2: the report she sent back keeps its signatures as history)
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
		});
		await as(browser, 'peter', async (page) => {
			await openContract(page, goods(), 'My work');
			await expect(board(page, 'D07')).toBeVisible();
			await press(page);
		});
		await as(browser, 'brian', async (page) => {
			await openContract(page, goods(), 'My work');
			await expect(board(page, 'D07')).toBeVisible();
			await page.getByTestId('cm-secondary-sign-with-dissent').click();
			await page.getByTestId('cm-input-dissent_units').fill(world.delivery_units[2]);
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toContainText('Give the reason for your dissent.');
			await page.getByTestId('cm-input-dissent_reason').fill('The case is cracked.');
			await press(page, 'cm-dialog-primary');
			await expect(page.getByTestId('cm-dialog')).toHaveCount(0);
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
		});
	});

	test('the Accounting Officer decides on the recommendation, with the dissent applied, and only the rest is accepted', async ({ browser }) => {
		await as(browser, 'amina', async (page) => {
			await openContract(page, goods(), 'My work');
			await expect(board(page, 'D07-A')).toBeVisible();
			await expect(nextStep(page)).toContainText('Decide on the acceptance report.');
			await expect(page.getByTestId('cm-root')).toContainText('Dissent recorded by Brian Wafula: The case is cracked.');
			await expect(page.getByTestId('cm-primary')).toHaveText('Accept as recommended');
			await press(page);
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
			await page.reload();
			await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
		});
		await as(browser, 'peter', async (page) => {
			await openContract(page, goods(), 'My work');
			await expect(nextStep(page)).toContainText("A member's dissent needs a repeated reading.");
		});
		await as(browser, 'grace', async (page) => {
			await openContract(page, goods());
			await page.getByTestId('cm-tab-deliveries').click();
			const row = page.getByTestId('cm-root').locator('tr', { hasText: 'Laptop computer' }).first();
			// item, ordered, arrived, accepted, rejected, awaiting decision, remaining: the dissented unit is not decided
			await expect(row.locator('td')).toHaveText(['Laptop computer', '10', '4', '3', '0', '1', '7']);
		});
	});

	test('a related service is evidenced on its own board, confirmed, reported and accepted without any receipt', async ({ browser }) => {
		await as(browser, 'peter', async (page) => {
			await openContract(page, service(), 'My work');
			await expect(board(page, 'D31')).toBeVisible();
			await expect(nextStep(page)).toContainText('Record the training evidence.');
			await expect(page.getByTestId('cm-root')).toContainText('Train ten named users to start and operate the supplied laptops');
			await expect(page.getByTestId('cm-root')).toContainText('1 training session · KES 50,000');
			await page.getByTestId('cm-input-obs.TRAIN-01.C4').fill('10');
			await page.getByTestId('cm-input-obs.TRAIN-01.C5').fill('10');
			await press(page); // Save observations
			await expect(board(page, 'D19')).toBeVisible(); // the findings are in and the technical certificate is his next step
			await press(page); // Sign technical certificate
		});
		await as(browser, 'julia', async (page) => {
			await openContract(page, service(), 'My work');
			await expect(board(page, 'D06')).toBeVisible();
			await press(page); // Prepare report for signing
			await expect(board(page, 'D31-A')).toBeVisible();
			await expect(page.getByTestId('cm-root')).toContainText('Invoice entitlement for the service is KES 50,000, once. No stock or asset unit is created for a training service.');
			await press(page); // Sign report
		});
		await as(browser, 'peter', async (page) => {
			await openContract(page, service(), 'My work');
			await expect(board(page, 'D31-A')).toBeVisible();
			await press(page);
		});
		await as(browser, 'brian', async (page) => {
			await openContract(page, service(), 'My work');
			await expect(board(page, 'D31-A')).toBeVisible();
			await press(page); // the last signature: accepted, with nothing to receive
			await expect(page.getByTestId('cm-primary')).toHaveCount(0);
			await page.getByTestId('cm-tab-deliveries').click();
			const row = page.getByTestId('cm-root').locator('tr', { hasText: 'Training session' }).first();
			await expect(row.locator('td')).toHaveText(['Training session', '1', '1', '1', '0', '0', '0']); // ordered 1, arrived 1, accepted 1, nothing remaining
		});
	});
});
