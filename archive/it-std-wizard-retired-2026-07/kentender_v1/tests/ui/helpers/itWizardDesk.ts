import { expect, type Page } from "@playwright/test";

export const ITW_DASHBOARD_ROUTE = "/desk/it-tender-configuration-dashboard";
export const ITW_OVERVIEW_ROUTE = "/desk/it-tender-configuration-overview";

/** Belt-and-suspenders for specs that still call this helper (native pages need no CDN guard). */
export async function installOfflineAssetGuard(_page: Page): Promise<void> {
	// Native IT Wizard screens load only self-hosted /assets — no external hosts to abort.
}

export async function openNativeDashboard(page: Page): Promise<void> {
	await page.goto(ITW_DASHBOARD_ROUTE, { waitUntil: "domcontentloaded" });
	await expect(page.locator('[data-testid="it-wizard-dashboard"]')).toBeVisible({ timeout: 30_000 });
	await page.waitForFunction(
		() => {
			const tbody = document.querySelector("[data-itw-tbody]");
			if (!tbody) return false;
			return !(tbody.textContent || "").includes("Loading");
		},
		{ timeout: 30_000 },
	);
}

/** Overview (Screen 02) — native plain DOM (no iframe). */
export async function openNativeOverview(page: Page, configurationId: string): Promise<void> {
	await page.goto(`${ITW_OVERVIEW_ROUTE}?configuration_id=${configurationId}`, {
		waitUntil: "domcontentloaded",
	});
	await expect(page.locator('[data-testid="it-wizard-overview"]')).toBeVisible({ timeout: 30_000 });
	await expect(page.locator('[data-testid="it-wizard-overview"]')).toHaveAttribute(
		"data-itw-native-loaded",
		"1",
		{ timeout: 30_000 },
	);
}

/** @deprecated Use openNativeOverview — iframe path removed for Screen 02. */
export async function openHydratedOverview(page: Page, configurationId: string): Promise<void> {
	await openNativeOverview(page, configurationId);
}

/** @deprecated Screen 02 is native — use page root selectors directly. */
export function overviewIframe(page: Page) {
	return page.locator('[data-testid="it-wizard-overview"]');
}

export const ITW_REQUIREMENTS_ROUTE = "/desk/it-tender-configuration-it-requirements";

/** IT Requirements (Screen 03) — native plain DOM. */
export async function openNativeItRequirements(page: Page, configurationId: string): Promise<void> {
	await page.goto(`${ITW_REQUIREMENTS_ROUTE}?configuration_id=${configurationId}`, {
		waitUntil: "domcontentloaded",
	});
	await expect(page.locator('[data-testid="it-wizard-it-requirements"]')).toBeVisible({ timeout: 30_000 });
	await expect(page.locator('[data-testid="it-wizard-it-requirements"]')).toHaveAttribute(
		"data-itw-native-loaded",
		"1",
		{ timeout: 30_000 },
	);
}
