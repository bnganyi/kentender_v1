/**
 * W6-06 — Budget Workbench: Budget Line create / edit smoke tests.
 *
 * Contracts:
 *   1. "Add Budget Line" button opens the modal.
 *   2. Saving with valid data closes the modal; the new card appears in Zone 2.
 *   3. Saving with an empty name shows inline validation; modal stays open.
 *   4. "Open Line" pre-populates the modal with the existing line's data.
 *
 * Pre-condition: at least one Budget in status Draft must exist.
 * Budget line mutations are only allowed on Draft budgets (Active/Approved/Submitted
 * require a revision workflow per r3-builder-guard).
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

// ── Constants ─────────────────────────────────────────────────────────────────

const HUB_PATH = '/app/budget-hub';

// ── Helpers ───────────────────────────────────────────────────────────────────

async function openBudgetHub(page: Page): Promise<void> {
	await page.goto(HUB_PATH, { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('kt-bgt-workbench')).toBeVisible({ timeout: 30_000 });
	await expect(
		page.getByTestId('kt-bgt-budget-tbody').locator('tr[data-budget-name]').first(),
	).toBeVisible({ timeout: 15_000 });
}

/**
 * Find the first Budget whose status is Draft so that
 * upsert_budget_line calls will succeed. Active budgets now require
 * the revision workflow (r3-builder-guard).
 */
async function getEditableBudgetName(page: Page): Promise<string> {
	const result = await page.evaluate((): Promise<{ name: string; status: string }[]> => {
		const frappe = (
			window as {
				frappe?: {
					call: (args: {
						method: string;
						args: Record<string, unknown>;
						callback: (r: { message?: unknown }) => void;
						error: (e: unknown) => void;
					}) => void;
				};
			}
		).frappe;
		if (!frappe) return Promise.resolve([]);
		return new Promise((resolve, reject) => {
			frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'Budget',
					filters: [['status', '=', 'Draft'], ['supersedes_budget', 'is', 'not set']],
					fields: ['name', 'status'],
					limit_page_length: 1,
				},
				callback: (r) => resolve((r?.message as { name: string; status: string }[]) || []),
				error: (e) => reject(new Error('frappe.client.get_list failed: ' + JSON.stringify(e))),
			});
		});
	});
	if (!result || result.length === 0) {
		throw new Error(
			'W6-06 pre-condition failed: no Draft Budget found. ' +
				'Ensure at least one Draft budget exists on the site.',
		);
	}
	return result[0].name;
}

/**
 * Navigate directly to the workbench for the given budget and wait for
 * Zone 1 + Zone 2 to finish loading.
 */
async function openWorkbench(page: Page, budgetName: string): Promise<void> {
	await page.goto(`/app/budget-workbench/${encodeURIComponent(budgetName)}`, {
		waitUntil: 'domcontentloaded',
	});
	await expect(page.getByTestId('kt-wbench-root')).toBeVisible({ timeout: 30_000 });
	// Zone 1 resolved when title no longer has the skeleton class
	await expect(page.getByTestId('kt-wbench-title')).not.toHaveClass(/kt-wbench-skel/, {
		timeout: 20_000,
	});
	// Zone 2 loading placeholder must be gone
	await page.waitForFunction(
		() =>
			document.querySelector(
				"[data-testid='kt-wbench-lines-list'] .kt-wbench-lines-loading",
			) === null,
		undefined,
		{ timeout: 20_000 },
	);
}

/** Open the modal (whatever mode), wait for the overlay to be visible. */
async function waitForModalOpen(page: Page): Promise<void> {
	await expect(page.getByTestId('kt-wbench-modal-overlay')).toBeVisible({ timeout: 10_000 });
}

/** Assert the modal is gone from the DOM. */
async function waitForModalClose(page: Page): Promise<void> {
	await expect(page.getByTestId('kt-wbench-modal-overlay')).not.toBeAttached({
		timeout: 15_000,
	});
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('Budget Workbench — line CRUD smoke (W6-06)', () => {
	// Shared login / editable budget — set up once per describe block via
	// beforeEach so each test gets a fresh page load (Playwright isolation).
	let editableBudgetName: string;

	test.beforeAll(async ({ browser }) => {
		// Resolve an editable budget name once for the whole suite.
		const page = await browser.newPage();
		await loginAsAdministrator(page);
		await openBudgetHub(page);
		editableBudgetName = await getEditableBudgetName(page);
		await page.close();
	});

	// ── 1. Add Budget Line button opens the modal ──────────────────────────────

	test('"Add Budget Line" button opens the modal', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkbench(page, editableBudgetName);

		await page.getByTestId('kt-wbench-btn-add').click();
		await waitForModalOpen(page);

		// Modal title must be "Add Budget Line"
		await expect(page.getByTestId('kt-wbench-modal-title')).toHaveText('Add Budget Line');

		// Required field inputs must be present
		await expect(page.locator('[name="budget_line_name"]')).toBeVisible();
		await expect(page.locator('[name="amount_allocated"]')).toBeVisible();

		// Close the modal before the next assertion
		await page.getByTestId('kt-wbench-modal-close').click();
		await waitForModalClose(page);
	});

	// ── 2. Valid save closes modal and new card appears in Zone 2 ──────────────

	test('Saving with valid data closes modal; new line card appears in Zone 2', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await openWorkbench(page, editableBudgetName);

		// Open "Add Budget Line" modal
		await page.getByTestId('kt-wbench-btn-add').click();
		await waitForModalOpen(page);

		// Fill required fields (unique name via timestamp to avoid duplicates)
		const uniqueName = `Smoke Test Line ${Date.now()}`;
		await page.locator('[name="budget_line_name"]').fill(uniqueName);
		await page.locator('[name="amount_allocated"]').fill('100000');

		// Programme is mandatory on Budget Line — wait for async options to load
		// then pick the first real option (skip the placeholder "— None —")
		const programSelect = page.locator('[name="program"]');
		await expect(programSelect).toBeVisible();
		await page.waitForFunction(
			() => {
				const sel = document.querySelector('[name="program"]') as HTMLSelectElement | null;
				if (!sel) return false;
				// More than one option means real data loaded (beyond the placeholder)
				return sel.options.length > 1;
			},
			{ timeout: 10_000 },
		);
		// Select the first non-placeholder option
		await programSelect.selectOption({ index: 1 });

		// Submit
		await page.getByTestId('kt-wbench-modal-submit').click();

		// Modal must close on success
		await waitForModalClose(page);

		// _loadBuilderData refreshes Zone 2 in-place (no loading placeholder re-shown).
		// Wait directly for the new card's name to be visible — this is the real contract.
		const linesList = page.getByTestId('kt-wbench-lines-list');
		await expect(linesList.getByText(uniqueName)).toBeVisible({ timeout: 20_000 });
	});

	// ── 3. Empty name shows inline validation; modal stays open ───────────────

	test('Saving with empty name shows inline validation; modal stays open', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkbench(page, editableBudgetName);

		await page.getByTestId('kt-wbench-btn-add').click();
		await waitForModalOpen(page);

		// Submit without filling anything
		await page.getByTestId('kt-wbench-modal-submit').click();

		// Modal must remain open
		await expect(page.getByTestId('kt-wbench-modal-overlay')).toBeVisible();

		// Inline error for budget_line_name must be visible
		const nameErr = page.locator('[data-err="budget_line_name"]');
		await expect(nameErr).toBeVisible({ timeout: 5_000 });
		const errText = (await nameErr.textContent()) ?? '';
		expect(errText.trim().length).toBeGreaterThan(0);

		// The budget_line_name input must have a red border (error state)
		const nameInput = page.locator('[name="budget_line_name"]');
		const borderColor = await nameInput.evaluate((el) => (el as HTMLElement).style.borderColor);
		expect(borderColor).toBeTruthy(); // non-empty means error style was applied

		// Dismiss
		await page.getByTestId('kt-wbench-modal-close').click();
		await waitForModalClose(page);
	});

	// ── 4. "Open Line" pre-populates the modal with existing data ─────────────

	test('"Open Line" pre-populates the modal with the existing line data', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkbench(page, editableBudgetName);

		const linesList = page.getByTestId('kt-wbench-lines-list');

		// At least one line card must exist
		await expect(linesList.getByTestId('kt-wbench-line-card').first()).toBeVisible({
			timeout: 15_000,
		});

		// Get the displayed name of the first card so we can assert it appears in the modal
		const firstCard = linesList.getByTestId('kt-wbench-line-card').first();
		const cardNameEl = firstCard.getByTestId('kt-wbench-line-name').first();
		const existingName = ((await cardNameEl.textContent()) ?? '').trim();

		// Click the "Open Line" button on the first card
		await firstCard.getByTestId('kt-wbench-btn-open-line').click();
		await waitForModalOpen(page);

		// Modal title must indicate edit mode
		await expect(page.getByTestId('kt-wbench-modal-title')).toHaveText('Edit Budget Line');

		// The budget_line_name field must be pre-filled with the existing line's name
		const nameField = page.locator('[name="budget_line_name"]');
		await expect(nameField).toBeVisible();
		const fieldValue = await nameField.inputValue();
		expect(fieldValue.trim()).toBe(existingName);

		// Amount field must be filled (non-zero)
		const amtField = page.locator('[name="amount_allocated"]');
		const amtValue = await amtField.inputValue();
		expect(Number(amtValue)).toBeGreaterThan(0);

		// Dismiss without saving
		await page.getByTestId('kt-wbench-modal-close').click();
		await waitForModalClose(page);
	});
});
