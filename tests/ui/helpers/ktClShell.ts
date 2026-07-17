import { expect, Locator, Page } from "@playwright/test";

export const KT_CL_SIDENAV = '[data-testid="kt-cl-sidenav"]';
export const KT_CL_TOOLBAR = '[data-testid="kt-cl-toolbar"]';
export const KT_CL_TOOLBAR_TITLE = '[data-testid="kt-cl-toolbar-title"]';
export const KT_CL_TOOLBAR_SEARCH = '[data-testid="kt-cl-toolbar-search"]';
export const KT_CL_BREADCRUMBS = '[data-testid="kt-cl-breadcrumbs"]';
export const KT_CL_BREADCRUMB_CURRENT = '[data-testid="kt-cl-breadcrumb-current"]';
export const KT_CL_PAGE_SUBTITLE = '[data-testid="kt-cl-page-subtitle"]';
export const KT_CL_PAGE_ROOT = '[data-testid="kt-cl-page-root"]';
export const KT_CL_SIDEBAR_BRAND = '[data-testid="kt-cl-sidebar-brand"]';
export const KT_CL_SIDEBAR_FOOTER = '[data-testid="kt-cl-sidebar-footer"]';
export const KT_CL_PAGE_HEADER_ACTIONS = '[data-testid="kt-cl-page-header-actions"]';

// Content-area components
export const KT_CL_BENTO = '[data-testid="kt-cl-bento"]';
export const KT_CL_METRICS_GRID = '[data-testid="kt-cl-metrics-grid"]';
export const KT_CL_KPI_CARD = '[data-testid="kt-cl-kpi-card"]';
export const KT_CL_CALENDAR = '[data-testid="kt-cl-calendar"]';
export const KT_CL_CALENDAR_ITEM = '[data-testid="kt-cl-calendar-item"]';
export const KT_CL_DATA_TABLE = '[data-testid="kt-cl-data-table"]';
export const KT_CL_TABLE_ROW = '[data-testid="kt-cl-table-row"]';
export const KT_CL_TABLE_FILTER = '[data-testid="kt-cl-table-filter"]';
export const KT_CL_TABLE_FOOTER = '[data-testid="kt-cl-table-footer"]';
export const KT_CL_STATUS_CHIP = '[data-testid="kt-cl-status-chip"]';
export const KT_CL_NAV_GROUP = '[data-testid="kt-cl-nav-group"]';
export const KT_CL_NAV_CHILD = '[data-testid="kt-cl-nav-child"]';
export const KT_CL_COLLAPSE_TOGGLE = '[data-testid="kt-cl-collapse-toggle"]';

export async function gotoKtClShellPoc(page: Page) {
	await page.goto("/desk/kt-cl-shell-poc");
	await expect(page.locator(KT_CL_PAGE_ROOT)).toBeVisible({ timeout: 30_000 });
}

export async function expectKtClShellChrome(page: Page) {
	await expect(page.locator(".navbar")).toBeHidden();
	await expect(page.locator(".page-head")).toBeHidden();
	await expect(page.locator(".body-sidebar-container")).toBeHidden();
	await expect(page.locator(KT_CL_SIDENAV)).toBeVisible();
	await expect(page.locator(KT_CL_SIDEBAR_BRAND)).toContainText("KenTender");
	await expect(page.locator(KT_CL_SIDEBAR_BRAND)).toContainText(/Procurement Portal/i);
	await expect(page.locator(KT_CL_SIDEBAR_FOOTER)).toBeVisible();
	await expect(page.locator(KT_CL_TOOLBAR)).toBeVisible();
	await expect(page.locator(KT_CL_TOOLBAR_TITLE)).toHaveText(/Procurement Home/i);
	await expect(page.locator(KT_CL_TOOLBAR_SEARCH)).toBeVisible();
	await expect(page.locator(KT_CL_BREADCRUMBS)).toBeVisible();
	await expect(page.locator(KT_CL_BREADCRUMB_CURRENT)).toHaveText(/Procurement Home/i);
	await expect(page.locator(KT_CL_PAGE_SUBTITLE)).toHaveText(/Fiscal Year 2024\/2025 Overview/i);
	await expect(page.locator(KT_CL_PAGE_HEADER_ACTIONS)).toBeVisible();
	await expect(page.getByTestId("kt-cl-action-export")).toBeVisible();
	await expect(page.getByTestId("kt-cl-action-submit")).toBeVisible();
}

export function breadcrumbLink(page: Page, label: string | RegExp): Locator {
	return page.locator(KT_CL_BREADCRUMBS).getByRole("link", { name: label });
}
