import { expect, type Page } from '@playwright/test';

const LEGACY_TO_TASK_TAB: Record<string, string> = {
	'tm2-tab-overview': 'tm2-tab-overview',
	'tm2-tab-std-readiness': 'tm2-tab-preparation',
	'tm2-tab-timeline': 'tm2-tab-audit',
	'tm2-tab-supplier-access': 'tm2-tab-live-tender',
	'tm2-tab-clarifications': 'tm2-tab-live-tender',
	'tm2-tab-addenda': 'tm2-tab-live-tender',
	'tm2-tab-submissions': 'tm2-tab-live-tender',
	'tm2-tab-opening-readiness': 'tm2-tab-handoff',
	'tm2-tab-evaluation-handoff': 'tm2-tab-handoff',
	'tm2-tab-contract-handoff': 'tm2-tab-handoff',
	'tm2-tab-audit-evidence': 'tm2-tab-audit',
};

/** Click a grouped task tab (Overview, Preparation, Live Tender, Handoff, Audit). */
export async function clickTm2TaskTab(page: Page, taskTabId: string): Promise<void> {
	const shell = page.getByTestId('tm2-workbench-page');
	const tab = shell.getByTestId(taskTabId);
	await expect(tab).toBeVisible({ timeout: 30_000 });
	await tab.click();
}

/**
 * Open a legacy detail tab by clicking the grouped task tab that contains it.
 */
export async function clickTm2LegacyTab(page: Page, legacyTabId: string): Promise<void> {
	const taskTabId = LEGACY_TO_TASK_TAB[legacyTabId] || legacyTabId;
	await clickTm2TaskTab(page, taskTabId);
}
