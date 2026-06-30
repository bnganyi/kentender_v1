/**
 * DIA Demand Workbench — backend wiring smoke tests (WBX-W9).
 *
 * Covers:
 *   1. Navigating directly to the workbench URL renders live data (title, demand ID).
 *   2. At least one demand item row is visible.
 *   3. Approval timeline has at least one completed ("done") step.
 *   4. Role-aware action buttons are rendered for the current status.
 *   5. "Add Item" button is visible for Draft demands, hidden for Approved demands.
 *   6. Skeleton is replaced by content within a reasonable timeout.
 *   7. NOT_FOUND demand renders an inline error card (not a blank page).
 *   8. Navigating from the Hub row "Open" action lands on the workbench.
 *
 * Requires seeded demands (seed_dia_extended or seed_dia_realistic).
 * Uses Administrator login for broad access.
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openDemandHub } from '../../helpers/diaHub';

// ── Constants ────────────────────────────────────────────────────────────────

const WBX_PATH = (demandName: string) => `/app/demand-workbench/${demandName}`;

// Known seeded demands from seed_dia_realistic — use status-specific ones.
// These are re-queried at runtime to avoid hardcoding brittle names.
async function getFirstDemandByStatus(page: Page, status: string): Promise<string | null> {
  return page.evaluate(async (st) => {
    return new Promise<string | null>((resolve) => {
      frappe.call({
        method: 'frappe.client.get_list',
        args: {
          doctype: 'Demand',
          filters: [['status', '=', st]],
          fields: ['name'],
          limit: 1,
        },
        callback: (r: any) => {
          const rows = r?.message || [];
          resolve(rows.length ? rows[0].name : null);
        },
        error: () => resolve(null),
      });
    });
  }, status);
}

// ── Helper: navigate to workbench and wait for canvas ────────────────────────

async function openWorkbench(page: Page, demandName: string): Promise<void> {
  await page.goto(WBX_PATH(demandName), { waitUntil: 'domcontentloaded' });
  // Wait for skeleton to be replaced by live canvas
  await page.waitForFunction(
    () => !!document.querySelector('.kt-wbx-title'),
    undefined,
    { timeout: 30_000 },
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('DIA Workbench — backend wiring smoke (WBX-W9)', () => {

  test('workbench renders live title and demand ID for a Pending Finance demand', async ({ page }) => {
    await loginAsAdministrator(page);
    const name = await getFirstDemandByStatus(page, 'Pending Finance Approval');
    if (!name) test.skip();

    await openWorkbench(page, name!);

    // Title is non-empty and not the placeholder "Demand"
    const title = page.locator('.kt-wbx-title');
    await expect(title).toBeVisible();
    const titleText = await title.textContent();
    expect(titleText?.trim().length).toBeGreaterThan(3);
    expect(titleText?.trim()).not.toBe('Demand');

    // Demand ID badge visible (contains "DIA-")
    const subtitle = page.locator('.kt-wbx-subtitle');
    await expect(subtitle).toContainText('DIA-');

    // Status badge shows "Funding Review"
    await expect(page.locator('.kt-wbx-badge--reserved')).toBeVisible();
  });

  test('demand items table has at least one row', async ({ page }) => {
    await loginAsAdministrator(page);
    const name = await getFirstDemandByStatus(page, 'Pending Finance Approval');
    if (!name) test.skip();

    await openWorkbench(page, name!);

    const rows = page.locator('.kt-wbx-items-table tbody tr');
    await expect(rows.first()).toBeVisible({ timeout: 15_000 });
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('approval timeline shows at least one completed step', async ({ page }) => {
    await loginAsAdministrator(page);
    const name = await getFirstDemandByStatus(page, 'Pending Finance Approval');
    if (!name) test.skip();

    await openWorkbench(page, name!);

    const doneIcons = page.locator('.kt-wbx-tl-icon--done');
    await expect(doneIcons.first()).toBeVisible({ timeout: 15_000 });
    const count = await doneIcons.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('Finance Review action buttons are rendered (Approve + Return)', async ({ page }) => {
    await loginAsAdministrator(page);
    const name = await getFirstDemandByStatus(page, 'Pending Finance Approval');
    if (!name) test.skip();

    await openWorkbench(page, name!);

    // Primary approve button
    const approveBtn = page.locator('[data-action="approve_finance"]');
    await expect(approveBtn).toBeVisible({ timeout: 15_000 });

    // Return to draft button
    const returnBtn = page.locator('[data-action="return_from_finance"]');
    await expect(returnBtn).toBeVisible();
  });

  test('Add Item button is visible for Draft demand', async ({ page }) => {
    await loginAsAdministrator(page);
    const name = await getFirstDemandByStatus(page, 'Draft');
    if (!name) test.skip();

    await openWorkbench(page, name!);

    const addItemBtn = page.locator('.kt-wbx-add-item-btn');
    await expect(addItemBtn).toBeVisible({ timeout: 15_000 });
  });

  test('Add Item button is hidden for Approved demand', async ({ page }) => {
    await loginAsAdministrator(page);
    const name = await getFirstDemandByStatus(page, 'Approved');
    if (!name) test.skip();

    await openWorkbench(page, name!);

    const addItemBtn = page.locator('.kt-wbx-add-item-btn');
    await expect(addItemBtn).not.toBeVisible({ timeout: 15_000 });
  });

  test('skeleton is replaced by live content within 15s', async ({ page }) => {
    await loginAsAdministrator(page);
    const name = await getFirstDemandByStatus(page, 'Pending HoD Approval');
    if (!name) test.skip();

    await page.goto(WBX_PATH(name!), { waitUntil: 'domcontentloaded' });

    // Skeleton should appear initially
    const skeleton = page.locator('.kt-wbx-skeleton');

    // Wait for canvas (skeleton replaced)
    await page.waitForFunction(
      () => !!document.querySelector('.kt-wbx-title'),
      undefined,
      { timeout: 15_000 },
    );
    // After render, skeleton should be gone
    await expect(skeleton.first()).not.toBeVisible({ timeout: 5_000 });
  });

  test('NOT_FOUND demand renders inline error card with Back to Hub button', async ({ page }) => {
    await loginAsAdministrator(page);
    await page.goto(WBX_PATH('nonexistent-demand-xyz-999'), { waitUntil: 'domcontentloaded' });

    const errorCard = page.locator('.kt-wbx-error-card');
    await expect(errorCard).toBeVisible({ timeout: 20_000 });

    const backBtn = page.locator('#kt-wbx-back-btn2');
    await expect(backBtn).toBeVisible();
  });

  test('Hub row Open action navigates to workbench with correct demand', async ({ page }) => {
    await loginAsAdministrator(page);
    const { hasRows } = await openDemandHub(page);
    if (!hasRows) test.skip();

    // Wait for the first real data row (not skeleton)
    const firstRow = page.locator('[data-testid="kt-dia-row"]').first();
    await expect(firstRow).toBeVisible({ timeout: 20_000 });

    // Click the Open span on that row
    const openBtn = firstRow.locator('[data-action="open"]');
    await openBtn.click();

    // Should land on the workbench URL (Frappe hash routing: /desk#demand-workbench/...)
    await page.waitForFunction(
      () => window.location.href.includes('demand-workbench'),
      undefined,
      { timeout: 20_000 },
    );
    expect(page.url()).toContain('demand-workbench');

    // The workbench title should load
    await page.waitForFunction(
      () => !!document.querySelector('.kt-wbx-title'),
      undefined,
      { timeout: 20_000 },
    );
    const title = page.locator('.kt-wbx-title');
    await expect(title).toBeVisible();
  });

  test('justification section renders beneficiary_summary when present', async ({ page }) => {
    await loginAsAdministrator(page);
    // Use any demand that has been seeded with justification text
    const name = await getFirstDemandByStatus(page, 'Pending Finance Approval');
    if (!name) test.skip();

    await openWorkbench(page, name!);

    const justSection = page.locator('.kt-wbx-just-body');
    const visible = await justSection.isVisible().catch(() => false);
    // If visible, check label is present
    if (visible) {
      await expect(page.locator('.kt-wbx-just-label').first()).toBeVisible();
    }
    // Section is either visible with content or the whole block is absent — no blank crash
    const canvasVisible = await page.locator('.kt-wbx-canvas').isVisible();
    expect(canvasVisible).toBe(true);
  });
});
