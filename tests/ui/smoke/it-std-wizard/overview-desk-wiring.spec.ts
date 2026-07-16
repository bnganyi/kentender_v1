import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const DASHBOARD_ROUTE = "/desk/it-tender-configuration-dashboard";
const OVERVIEW_ROUTE = "/desk/it-tender-configuration-overview";
const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";

test.describe("IT Wizard STD Configuration Overview Desk wiring", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("dashboard continue opens overview with hydrated header and step grid", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const dashIframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(dashIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(dashIframe.getByText(SEED_TITLE)).toBeVisible({ timeout: 30_000 });
		const seedRow = dashIframe.locator(`tr[data-configuration-id="${SEED_CODE}"]`);
		await expect(seedRow).toBeVisible();
		await seedRow.getByRole("button", { name: /^Continue Setup$/i }).click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-overview/, { timeout: 15_000 });

		const overviewIframe = page.frameLocator('[data-testid="it-wizard-overview-iframe"]');
		await expect(overviewIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(overviewIframe.getByRole("heading", { name: SEED_TITLE })).toBeVisible();
		await expect(overviewIframe.getByText(SEED_CODE)).toBeVisible();
		await expect(overviewIframe.getByText("In configuration")).toBeVisible();
		await expect(overviewIframe.locator("body")).not.toContainText("IN_CONFIGURATION");
		await expect(overviewIframe.locator("[data-itw-overview-step-grid] [data-itw-step-card]")).toHaveCount(13);
		await expect(
			overviewIframe.locator('[data-itw-step-card][data-itw-step-current="1"] h3', {
				hasText: "IT Requirements",
			}),
		).toBeVisible();
		await expect(overviewIframe.getByText("National Treasury")).toBeVisible();
		await expect(overviewIframe.getByText("Open Tender")).toBeVisible();
		const scrollHost = overviewIframe.locator("[data-itw-overview-scroll-host]");
		await expect(scrollHost).toBeVisible();
		const scrollMetrics = await scrollHost.evaluate(function (node) {
			return {
				scrollHeight: node.scrollHeight,
				clientHeight: node.clientHeight,
			};
		});
		expect(scrollMetrics.scrollHeight).toBeGreaterThan(scrollMetrics.clientHeight);
		const publicationCard = overviewIframe.locator('[data-itw-step-card] h3', {
			hasText: "Publication Readiness",
		});
		await publicationCard.scrollIntoViewIfNeeded();
		await expect(publicationCard).toBeVisible();
	});

	test("dashboard continue preserves configuration_id on browser refresh", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const dashIframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(dashIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const seedRow = dashIframe.locator(`tr[data-configuration-id="${SEED_CODE}"]`);
		await seedRow.getByRole("button", { name: /^Continue Setup$/i }).click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-overview/, { timeout: 15_000 });
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`), { timeout: 15_000 });

		await page.reload();
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`), { timeout: 15_000 });

		const overviewIframe = page.frameLocator('[data-testid="it-wizard-overview-iframe"]');
		await expect(overviewIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(page.getByText("Configuration required")).toHaveCount(0);
		await expect(overviewIframe.getByRole("heading", { name: SEED_TITLE })).toBeVisible();
	});

	test("overview route without configuration_id redirects to dashboard", async ({ page }) => {
		await page.goto(OVERVIEW_ROUTE);
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/, { timeout: 15_000 });
	});

	test("overview route with configuration_id hydrates from API", async ({ page }) => {
		await page.goto(`${OVERVIEW_ROUTE}?configuration_id=${SEED_CODE}`);
		const overviewIframe = page.frameLocator('[data-testid="it-wizard-overview-iframe"]');
		await expect(overviewIframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(overviewIframe.getByRole("heading", { name: SEED_TITLE })).toBeVisible();
		await expect(overviewIframe.locator("[data-itw-overview-step-grid] [data-itw-step-card]")).toHaveCount(13);
		await expect(overviewIframe.locator("body")).not.toContainText("TNT/024/2024");
		await expect(overviewIframe.locator("body")).not.toContainText("CONF-99283");
	});
});
