import { Page, expect } from '@playwright/test';

/** Frappe Desk workspace URL: `/app/<slug>` where slug matches Workspace name (spaces → hyphens, lowercased). */
export function workspaceAppPath(workspaceName: string): string {
	const slug = workspaceName.trim().toLowerCase().replace(/\s+/g, '-');
	return `/app/${slug}`;
}

export async function openWorkspace(page: Page, workspaceName: string) {
	await page.goto(workspaceAppPath(workspaceName));
	await page.waitForLoadState('networkidle');
	await expect(page.locator('body')).toContainText(workspaceName);
}

export async function expectNoBlankPage(page: Page) {
	await expect(page.locator('body')).not.toHaveText(/^$/);
}

/** Desk module tile anchor (`desktop_icon.html` sets `data-id` to the icon label). */
export function desktopModuleTile(page: Page, moduleDesktopLabel: string) {
	return page.locator(`a.desktop-icon[data-id="${moduleDesktopLabel}"]`);
}

/** Close release-notes / onboarding modals that block clicks on the home grid. */
export async function dismissOptionalDeskModals(page: Page) {
	const modal = page.locator('div.modal.show[role="dialog"]');
	if ((await modal.count()) === 0) return;
	await page.keyboard.press('Escape');
	await modal.first().waitFor({ state: 'hidden', timeout: 8000 }).catch(() => {});
}

/**
 * From `/app` home: open a module Desktop Icon, then click the workspace entry in the sidebar.
 * Matches Desk: module tile → Workspace Sidebar → workspace link (no Awesome Bar search).
 */
export async function openWorkspaceFromDeskLauncher(
	page: Page,
	moduleDesktopLabel: string,
	workspaceLabel: string,
) {
	await page.goto('/app');
	await page.waitForLoadState('domcontentloaded');
	await dismissOptionalDeskModals(page);
	const tile = desktopModuleTile(page, moduleDesktopLabel);
	await tile.waitFor({ state: 'visible', timeout: 45_000 });
	await tile.click();
	await page.waitForLoadState('domcontentloaded');
	const ws = page.getByRole('link', { name: workspaceLabel, exact: true });
	await ws.waitFor({ state: 'visible', timeout: 45_000 });
	await ws.click();
	await page.waitForLoadState('domcontentloaded');
}
