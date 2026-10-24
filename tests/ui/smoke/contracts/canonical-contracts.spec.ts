import { expect, test } from '@playwright/test';
import { login } from '../../helpers/auth';
import { openContract } from './helpers';

// SEED-002 v0.10 §A8.1: the canonical world's contracts, as the head of procurement meets them from the menu. Needs the world seeded with the contracts stage (`make seed-canonical`, the default where
// Contract Management is installed): the workstations paid and waiting for their completion certificate, the printers in delivery, the laptops waiting for the contract to be prepared.
// Verifies first paint, an interactive re-render (the list, a contract, back) and a reload that keeps the contract (AGENTS.md section 6.4). It changes nothing.
const HEAD = 'charles.mutiso@moh.example.test';
const SEED_PASSWORD = 'Test@123'; // kentender_core.seeds.constants.TEST_PASSWORD
const CONTRACTS = { workstations: 'CM-2025-0001', printers: 'CM-2026-0001', laptops: 'CM-2026-0002' };

test.describe('The canonical contracts', () => {
	test('the head of procurement finds the three contracts and each stands where the story puts it', async ({ page }) => {
		test.setTimeout(240_000);
		const problems: string[] = [];
		page.on('pageerror', (error) => problems.push(error.message));
		page.on('framenavigated', (frame) => {
			if (frame === page.mainFrame() && /\/app\/(contract-|purchase-|payment-)/.test(frame.url())) problems.push(`sent to a Desk form: ${frame.url()}`);
		});
		await login(page, HEAD, SEED_PASSWORD);

		// the paid workstations: everything delivered, accepted, claimed and paid, so the next step is the completion certificate
		await openContract(page, CONTRACTS.workstations);
		const paid = page.getByTestId('cm-root');
		await expect(paid).toContainText('Confirm contract completion');
		await expect(paid).toContainText('Afya Digital Supplies Limited');
		await expect(paid).toContainText('Issue the completion certificate.');
		await expect(paid).toContainText('120 staff workstation desktop computers');
		await expect(paid).toContainText('All fulfilled');
		await expect(paid).toContainText('Warranty');

		// back to the list and on to the printers: an interactive re-render, not a reload
		await page.goBack();
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'workspace');
		await openContract(page, CONTRACTS.printers);
		const printers = page.getByTestId('cm-root');
		await expect(printers).toContainText('30 Multifunction office printers at KES 191,400 each');
		await expect(printers).toContainText('20 accepted units');
		await expect(printers).toContainText('Dr Peter Kimani');
		await expect(printers).not.toContainText('Confirm contract completion');

		// the laptops: delivered to Contracting, the contract not yet prepared
		await openContract(page, CONTRACTS.laptops);
		const laptops = page.getByTestId('cm-root');
		await expect(laptops).toContainText('Prepare contract');
		await expect(laptops).toContainText('Review the contract and send it for signature.');
		await expect(laptops).toContainText('60 Replacement staff laptops at KES 191,400 each');

		// a reload keeps the contract
		await page.reload();
		await expect(page.getByTestId('cm-root')).toHaveAttribute('data-screen', 'board');
		await expect(page.getByTestId('cm-root')).toContainText('Prepare contract');
		expect(problems).toEqual([]);
	});
});
