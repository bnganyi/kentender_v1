import { expect, type Page } from "@playwright/test";

export type StdProdPageContract = {
	route: string;
	testid: string;
};

export async function expectStdProdPageLoads(page: Page, contract: StdProdPageContract) {
	await expect(page).toHaveURL(new RegExp(`/desk/${contract.route}(?:/|$)`), {
		timeout: 30_000,
	});
	await expect(page.locator(`[data-testid="${contract.testid}-iframe"]`)).toBeVisible({
		timeout: 30_000,
	});
	const iframe = page.frameLocator(`[data-testid="${contract.testid}-iframe"]`);
	await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
		timeout: 30_000,
	});
	await expect(page.getByText(/Page std-.* not found/i)).toHaveCount(0);
}
