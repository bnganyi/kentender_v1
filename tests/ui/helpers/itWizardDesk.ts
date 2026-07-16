import { expect, type FrameLocator, type Page } from "@playwright/test";

export const ITW_DASHBOARD_ROUTE = "/desk/it-tender-configuration-dashboard";

export function dashboardIframe(page: Page): FrameLocator {
	return page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
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
