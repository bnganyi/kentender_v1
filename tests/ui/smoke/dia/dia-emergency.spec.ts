import { test, expect } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

/** S19 — emergency demand cannot be saved/submitted without emergency justification. */
test('Emergency demand requires justification before submit (S19)', async ({ page }) => {
	await loginAsRequisitioner(page);
	await openDIALanding(page);

	const row = page.getByTestId('dia-row-DIA-MOH-2026-0001');
	const hasSeed = await row.isVisible({ timeout: 20_000 }).catch(() => false);
	test.skip(!hasSeed, 'Seed DIA-MOH-2026-0001 draft not present — run seed_dia_basic or seed_dia_extended.');

	await row.click();
	const editBtn = page.getByTestId('dia-action-edit');
	const canEdit = await editBtn.isVisible({ timeout: 10_000 }).catch(() => false);
	test.skip(!canEdit, 'Seed draft is not editable for requisitioner.');

	await editBtn.click();
	await expect(page.getByTestId('dia-builder-page')).toBeVisible({ timeout: 30_000 });

	// Force emergency path and leave justification blank to assert validation block.
	const demandTypeSelect = page.locator('[data-testid="dia-field-demand-type"] select');
	await demandTypeSelect.selectOption({ label: 'Emergency' });
	await page.locator('[data-testid="dia-field-emergency-justification"] textarea').fill('');

	const saveBtn = page.getByRole('button', { name: /save/i }).first();
	await saveBtn.click();
	await expect(page.getByText('Cannot save')).toBeVisible({ timeout: 10_000 });
	await expect(page.getByText('Emergency Justification is required for Emergency demands.')).toBeVisible({
		timeout: 10_000,
	});

	// Second pass: add justification and save should proceed.
	await page
		.locator('[data-testid="dia-field-emergency-justification"] textarea')
		.fill('Urgent continuity requirement due to service interruption risk.');
	await saveBtn.click();
	await expect(page.getByText('Cannot save')).toHaveCount(0);
});
