import { test, expect, type Page } from "@playwright/test";

import { loginAsAdministrator } from "../../helpers/auth";
import {
	ITW_DASHBOARD_ROUTE,
	ITW_OVERVIEW_ROUTE,
	dashboardIframe,
	openHydratedDashboard,
	openHydratedOverview,
	overviewIframe,
} from "../../helpers/itWizardDesk";

const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";

/**
 * ITW-02 / PW-ITW-OVERVIEW-01 — overview Desk contract only.
 * Site fixtures: `it_wizard_dashboard_seed` patch + active KE-PPRA-IT STD.
 * Run via `make it-wizard-screen-02-gate` (not the full wiring regression gate).
 */
test.describe.serial("IT Wizard STD Configuration Overview Desk wiring", () => {
	let page: Page;

	test.beforeAll(async ({ browser }) => {
		page = await browser.newPage();
		await loginAsAdministrator(page);
	});

	test.afterAll(async () => {
		await page.close();
	});

	test("dashboard continue opens overview with hydrated header and step grid", async () => {
		const dashIframe = await openHydratedDashboard(page);
		await expect(dashIframe.getByText(SEED_TITLE)).toBeVisible({ timeout: 30_000 });
		const seedRow = dashIframe.locator(`tr[data-configuration-id="${SEED_CODE}"]`);
		await expect(seedRow).toBeVisible();
		await seedRow.getByRole("button", { name: /^Continue Setup$/i }).click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-overview/, { timeout: 15_000 });

		const iframe = overviewIframe(page);
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.getByRole("heading", { name: SEED_TITLE })).toBeVisible();
		await expect(iframe.getByText(SEED_CODE)).toBeVisible();
		await expect(iframe.getByText("In configuration")).toBeVisible();
		await expect(iframe.locator("body")).not.toContainText("IN_CONFIGURATION");
		await expect(iframe.locator("[data-itw-overview-step-grid] [data-itw-step-card]")).toHaveCount(13);
		await expect(
			iframe.locator('[data-itw-step-card][data-itw-step-current="1"] h3', {
				hasText: "IT Requirements",
			}),
		).toBeVisible();
		await expect(iframe.getByText("National Treasury")).toBeVisible();
		await expect(iframe.getByText("Open Tender")).toBeVisible();
		const scrollHost = iframe.locator("[data-itw-overview-scroll-host]");
		await expect(scrollHost).toBeVisible();
		const scrollMetrics = await scrollHost.evaluate(function (node) {
			return {
				scrollHeight: node.scrollHeight,
				clientHeight: node.clientHeight,
			};
		});
		expect(scrollMetrics.scrollHeight).toBeGreaterThan(scrollMetrics.clientHeight);
		const publicationCard = iframe.locator('[data-itw-step-card] h3', {
			hasText: "Publication Readiness",
		});
		await publicationCard.scrollIntoViewIfNeeded();
		await expect(publicationCard).toBeVisible();
	});

	test("dashboard continue preserves configuration_id on browser refresh", async () => {
		const dashIframe = await openHydratedDashboard(page);
		const seedRow = dashIframe.locator(`tr[data-configuration-id="${SEED_CODE}"]`);
		await seedRow.getByRole("button", { name: /^Continue Setup$/i }).click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-overview/, { timeout: 15_000 });
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`), { timeout: 15_000 });

		await page.reload();
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`), { timeout: 15_000 });

		const iframe = overviewIframe(page);
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(page.getByText("Configuration required")).toHaveCount(0);
		await expect(iframe.getByRole("heading", { name: SEED_TITLE })).toBeVisible();
	});

	test("overview route without configuration_id redirects to dashboard", async () => {
		await page.goto(ITW_OVERVIEW_ROUTE);
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/, { timeout: 15_000 });
	});

	test("overview route with configuration_id hydrates from API", async () => {
		const iframe = await openHydratedOverview(page, SEED_CODE);
		await expect(iframe.getByRole("heading", { name: SEED_TITLE })).toBeVisible();
		await expect(iframe.locator("[data-itw-overview-step-grid] [data-itw-step-card]")).toHaveCount(13);
		await expect(iframe.locator("body")).not.toContainText("TNT/024/2024");
		await expect(iframe.locator("body")).not.toContainText("CONF-99283");
	});
});
