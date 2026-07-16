import { expect, type FrameLocator, type Page } from "@playwright/test";

export const ITW_DASHBOARD_ROUTE = "/desk/it-tender-configuration-dashboard";
export const ITW_OVERVIEW_ROUTE = "/desk/it-tender-configuration-overview";

export function dashboardIframe(page: Page): FrameLocator {
	return page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
}

export function overviewIframe(page: Page): FrameLocator {
	return page.frameLocator('[data-testid="it-wizard-overview-iframe"]');
}

export async function openHydratedDashboard(page: Page): Promise<FrameLocator> {
	await page.goto(ITW_DASHBOARD_ROUTE);
	await expect(page.locator(".page-head")).toBeHidden();
	const iframe = dashboardIframe(page);
	await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
		timeout: 30_000,
	});
	return iframe;
}

export async function openHydratedOverview(page: Page, configurationId: string): Promise<FrameLocator> {
	await page.goto(`${ITW_OVERVIEW_ROUTE}?configuration_id=${configurationId}`);
	const iframe = overviewIframe(page);
	await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
		timeout: 30_000,
	});
	return iframe;
}
