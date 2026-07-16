import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const SEED = "ITCFG-DASH-SEED-001";

const SCREENS: { route: string; testid: string; expectText: RegExp }[] = [
	{
		route: "it-tender-configuration-price-schedule",
		testid: "it-wizard-price-schedule",
		expectText: /Core Platform Supply|Price Schedule|Not configured/,
	},
	{
		route: "it-tender-configuration-evaluation-setup",
		testid: "it-wizard-evaluation-setup",
		expectText: /Evaluation|marks|Not configured|criterion/i,
	},
	{
		route: "it-tender-configuration-forms-and-evidence",
		testid: "it-wizard-forms-and-evidence",
		expectText: /Forms|Evidence|submission|Not configured/i,
	},
	{
		route: "it-tender-configuration-scc",
		testid: "it-wizard-scc",
		expectText: /SCC|Carry|Not configured|obligation/i,
	},
	{
		route: "it-tender-configuration-validation-report",
		testid: "it-wizard-validation-report",
		expectText: /Validation|finding|Blocker|Warning|Not configured/i,
	},
	{
		route: "it-tender-configuration-review-and-approval",
		testid: "it-wizard-review-and-approval",
		expectText: /Review|Pending|Approved|Not configured/i,
	},
	{
		route: "it-tender-configuration-render-preview",
		testid: "it-wizard-render-preview",
		expectText: /Preview|Publication|checklist|Not configured|confirm/i,
	},
	{
		route: "it-tender-configuration-publication-readiness",
		testid: "it-wizard-publication-readiness",
		expectText: /Publication|Ready|checklist|Not configured/i,
	},
];

test.describe("IT Wizard ITW-08–15 Desk wiring", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	for (const screen of SCREENS) {
		test(`${screen.route} hydrates with configuration_id`, async ({ page }) => {
			await page.evaluate((route) => {
				localStorage.removeItem(`_page:${route}`);
			}, screen.route);
			await page.goto(`/desk/${screen.route}?configuration_id=${SEED}`, {
				waitUntil: "domcontentloaded",
			});
			const frame = page.frameLocator(`[data-testid="${screen.testid}-iframe"]`);
			await expect(frame.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
				timeout: 45_000,
			});
			await expect(frame.locator("body")).toContainText(screen.expectText);
		});
	}

	test("inventory continues to price schedule", async ({ page }) => {
		await page.goto(`/desk/it-tender-configuration-system-inventory?configuration_id=${SEED}`, {
			waitUntil: "domcontentloaded",
		});
		const inventory = page.frameLocator('[data-testid="it-wizard-system-inventory-iframe"]');
		await expect(inventory.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 45_000,
		});
		await inventory.locator("[data-itw-inv-continue]").click();
		await expect(page).toHaveURL(/it-tender-configuration-price-schedule/, { timeout: 30_000 });
		const price = page.frameLocator('[data-testid="it-wizard-price-schedule-iframe"]');
		await expect(price.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 45_000,
		});
	});
});
