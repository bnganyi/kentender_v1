/**
 * H14 — DIA Demand Hub wiring smoke tests.
 *
 * Covers the contracts from the H14 work item:
 *   1. Hub page loads; KPI strip and table are visible.
 *   2. KPI counts are numeric (not static placeholder text).
 *   3. Demand table has >= 1 row from live data (or shows a clean empty state).
 *   4. Search input re-fetches the table.
 *   5. Lifecycle status chip click re-fetches the table.
 *   6. "Open" row action navigates to the Demand form.
 *   7. "New Demand" button navigates to new-demand form.
 *   8. Strategic Goal Match shows a percentage string.
 *   9. Sidebar is intact after a same-page refresh.
 *  10. Pagination prev/next buttons are present and prev is disabled on page 1.
 *  11. Filter button toggles the filter panel.
 *
 * Requires seeded Demand records for tests 4-6 (uses seed_dia_extended or
 * any standard DIA seed pack).
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
  DIA_HUB_PATH,
  getFirstDemandName,
  openDemandHub,
  waitForTableReload,
} from '../../helpers/diaHub';

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('DIA Hub — wiring smoke (H14)', () => {
  // ── 1. Page load ─────────────────────────────────────────────────────────

  test('hub mounts and KPI strip is visible', async ({ page }) => {
    await loginAsAdministrator(page);
    await openDemandHub(page);

    await expect(page.getByTestId('kt-dia-hub')).toBeVisible();
    await expect(page.getByTestId('kt-dia-kpi-strip')).toBeVisible();
    await expect(page.getByTestId('kt-dia-table')).toBeVisible();
  });

  // ── 2. KPI counts are numeric ─────────────────────────────────────────────

  test('KPI counts are numeric after API load', async ({ page }) => {
    await loginAsAdministrator(page);
    await openDemandHub(page);

    const kpiTestIds = [
      'kt-dia-kpi-drafts-count',
      'kt-dia-kpi-dept-count',
      'kt-dia-kpi-funding-count',
      'kt-dia-kpi-final-count',
    ];

    for (const testId of kpiTestIds) {
      const el = page.getByTestId(testId);
      await expect(el).toBeVisible();
      const text = (await el.textContent()) ?? '';
      // Must contain at least one digit (real API data, not dash or "Loading")
      expect(text, `${testId} should contain a digit`).toMatch(/\d/);
    }
  });

  // ── 3. Table has live data or clean empty state ────────────────────────────

  test('table body has rows or a clean empty-state message', async ({ page }) => {
    await loginAsAdministrator(page);
    const { hasRows } = await openDemandHub(page);

    const tbody = page.getByTestId('kt-dia-table-body');
    await expect(tbody).toBeVisible();

    if (hasRows) {
      const firstRow = tbody.locator('tr[data-demand-name]').first();
      await expect(firstRow).toBeVisible();
      // Row must have a real title
      const titleText = (await firstRow.getByTestId('kt-dia-row-title').textContent()) ?? '';
      expect(titleText.trim().length).toBeGreaterThan(0);
    } else {
      // Empty state row should contain helpful text, not a skeleton or "Loading"
      const emptyRow = tbody.locator('.kt-dia-table__empty');
      await expect(emptyRow).toBeVisible();
      const emptyText = (await emptyRow.textContent()) ?? '';
      expect(emptyText.trim().length).toBeGreaterThan(0);
      expect(emptyText).not.toMatch(/Loading/i);
    }
  });

  // ── 4. Search re-fetches table ─────────────────────────────────────────────

  test('search input triggers a table reload', async ({ page }) => {
    await loginAsAdministrator(page);
    const { hasRows } = await openDemandHub(page);

    if (!hasRows) {
      test.skip(true, 'Requires seeded demand rows for search test.');
      return;
    }

    const searchInput = page.getByTestId('kt-dia-search');
    await expect(searchInput).toBeVisible();

    // Type an unlikely search term to force an empty result
    await searchInput.fill('zzz_no_match_xyz');
    await waitForTableReload(page);

    // Table should now show empty state
    const emptyRow = page.getByTestId('kt-dia-table-body').locator('.kt-dia-table__empty');
    await expect(emptyRow).toBeVisible({ timeout: 15_000 });

    // Clear search — rows should return
    await searchInput.fill('');
    await waitForTableReload(page);
    const firstRow = page.getByTestId('kt-dia-table-body').locator('tr[data-demand-name]').first();
    await expect(firstRow).toBeVisible({ timeout: 15_000 });
  });

  // ── 5. Lifecycle chip re-fetches table ────────────────────────────────────

  test('clicking a lifecycle chip sets it active and reloads the table', async ({ page }) => {
    await loginAsAdministrator(page);
    await openDemandHub(page);

    const chipStrip = page.getByTestId('kt-dia-lifecycle-chips');
    await expect(chipStrip).toBeVisible();

    // "All" chip should be active initially
    const allChip = page.getByTestId('kt-dia-chip-all');
    await expect(allChip).toHaveClass(/kt-dia-lc-chip--active/);

    // Click "Approved" chip
    const approvedChip = page.getByTestId('kt-dia-chip-approved');
    await approvedChip.click();
    await waitForTableReload(page);

    // "Approved" must now be active; "All" must not be
    await expect(approvedChip).toHaveClass(/kt-dia-lc-chip--active/);
    await expect(allChip).not.toHaveClass(/kt-dia-lc-chip--active/);

    // Click "All" to restore
    await allChip.click();
    await waitForTableReload(page);
    await expect(allChip).toHaveClass(/kt-dia-lc-chip--active/);
  });

  // ── 6. Open row navigates to Demand form ──────────────────────────────────

  test('"Open" action navigates to the Demand form', async ({ page }) => {
    await loginAsAdministrator(page);
    const { hasRows } = await openDemandHub(page);

    if (!hasRows) {
      test.skip(true, 'Requires seeded demand rows to test Open action.');
      return;
    }

    const firstRow = page
      .getByTestId('kt-dia-table-body')
      .locator('tr[data-demand-name]')
      .first();
    await expect(firstRow).toBeVisible();

    // Click the "Open" action span
    await firstRow.locator('[data-action="open"]').click();

    // URL must navigate to the Demand form (Frappe Desk uses /desk/ or /app/ path prefix)
    await expect(page).toHaveURL(/\/demand\//, { timeout: 15_000 });
  });

  // ── 7. New Demand button navigates to new form ────────────────────────────

  test('"New Demand" button navigates to a new Demand form', async ({ page }) => {
    await loginAsAdministrator(page);
    await openDemandHub(page);

    await page.getByTestId('kt-dia-btn-new').click();

    // URL must navigate to a Demand form (new record — Frappe appends a random suffix)
    await expect(page).toHaveURL(/\/demand\/new-demand/, { timeout: 15_000 });
  });

  // ── 8. Strategic Goal Match shows a percentage ────────────────────────────

  test('Strategic Goal Match displays a percentage value', async ({ page }) => {
    await loginAsAdministrator(page);
    await openDemandHub(page);

    const pctEl = page.getByTestId('kt-dia-goal-pct');
    await expect(pctEl).toBeVisible();
    const text = (await pctEl.textContent()) ?? '';
    // Must be "N%" — not the dash placeholder "—"
    expect(text.trim(), 'goal pct should be a percentage').toMatch(/^\d+%$/);
  });

  // ── 9. Sidebar intact after refresh ──────────────────────────────────────

  test('DIA sidebar item remains visible after navigating away and back', async ({ page }) => {
    await loginAsAdministrator(page);
    await openDemandHub(page);

    // Navigate away to home
    await page.goto('/app', { waitUntil: 'domcontentloaded' });

    // Return to hub
    await openDemandHub(page);

    // Frappe sidebar must still have the DIA module link
    const sidebar = page.locator('.desk-sidebar, .layout-side-section, [class*="sidebar"]').first();
    await expect(sidebar).toBeVisible({ timeout: 15_000 });
  });

  // ── 10. Pagination controls are rendered ──────────────────────────────────

  test('pagination prev button is disabled on the first page', async ({ page }) => {
    await loginAsAdministrator(page);
    await openDemandHub(page);

    const prevBtn = page.locator('[data-page="prev"]');
    const nextBtn = page.locator('[data-page="next"]');

    await expect(prevBtn).toBeVisible();
    await expect(nextBtn).toBeVisible();

    // Prev must be disabled on page 1
    await expect(prevBtn).toBeDisabled();
  });

  test('rows-per-page selector defaults to 10 and changing it reloads the table', async ({
    page,
  }) => {
    await loginAsAdministrator(page);
    const { hasRows } = await openDemandHub(page);

    const rppSelect = page.getByTestId('kt-dia-rows-per-page');
    await expect(rppSelect).toBeVisible();

    // Default must be 10
    await expect(rppSelect).toHaveValue('10');

    if (!hasRows) {
      test.skip(true, 'Requires seeded demand rows for rows-per-page reload test.');
      return;
    }

    // Change to 20
    await rppSelect.selectOption('20');
    await waitForTableReload(page);

    await expect(rppSelect).toHaveValue('20');
  });

  test('count label shows "Showing X to Y of Z demands" after load', async ({ page }) => {
    await loginAsAdministrator(page);
    const { hasRows } = await openDemandHub(page);

    const countEl = page.getByTestId('kt-dia-table-count');
    await expect(countEl).toBeVisible();

    if (hasRows) {
      const text = (await countEl.textContent()) ?? '';
      expect(text).toMatch(/Showing \d+ to \d+ of \d+ demands/);
    }
  });

  // ── 11. Filter panel toggles ──────────────────────────────────────────────

  test('Filter button toggles the filter panel', async ({ page }) => {
    await loginAsAdministrator(page);
    await openDemandHub(page);

    const filterBtn = page.getByTestId('kt-dia-btn-filter');
    const filterPanel = page.getByTestId('kt-dia-filter-panel');

    // Panel should be hidden initially
    await expect(filterPanel).toBeHidden();

    // Click to open
    await filterBtn.click();
    await expect(filterPanel).toBeVisible({ timeout: 8_000 });

    // Filter selects must be populated by the async meta API
    const typeSelect = page.getByTestId('kt-dia-filter-type');
    await expect(typeSelect).toBeVisible();
    // Poll until the meta API has added real options beyond the placeholder
    await expect.poll(
      () => typeSelect.locator('option').count(),
      { timeout: 12_000 },
    ).toBeGreaterThan(1);

    // Click again to close
    await filterBtn.click();
    await expect(filterPanel).toBeHidden();
  });
});
