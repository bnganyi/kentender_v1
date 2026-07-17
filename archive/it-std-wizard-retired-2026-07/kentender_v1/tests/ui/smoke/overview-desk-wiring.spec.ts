import { test, expect, type Page } from "@playwright/test";

import { loginAsAdministrator } from "../../helpers/auth";
import {
	ITW_OVERVIEW_ROUTE,
	openNativeDashboard,
	openNativeOverview,
} from "../../helpers/itWizardDesk";

const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";

/**
 * ITW-02 / PW-ITW-OVERVIEW-01 — Tender Configuration Home Desk contract (native).
 */
test.describe.serial("IT Wizard Tender Configuration Home Desk wiring", () => {
	let page: Page;

	test.beforeAll(async ({ browser }) => {
		page = await browser.newPage();
		await loginAsAdministrator(page);
	});

	test.afterAll(async () => {
		await page.close();
	});

	test("dashboard continue opens home with context strip, next action, and step grid", async () => {
		await openNativeDashboard(page);
		await expect(page.getByText(SEED_TITLE)).toBeVisible({ timeout: 30_000 });
		const seedRow = page.locator(`tr[data-configuration-id="${SEED_CODE}"]`);
		await expect(seedRow).toBeVisible();
		await seedRow.getByRole("button", { name: /^Continue Setup$/i }).click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-overview/, { timeout: 15_000 });

		await expect(page.locator('[data-testid="it-wizard-overview"]')).toHaveAttribute(
			"data-itw-native-loaded",
			"1",
			{ timeout: 30_000 },
		);
		await expect(page.getByRole("heading", { name: "Tender Configuration Home" })).toBeVisible();
		const overview = page.locator('[data-testid="it-wizard-overview"]');
		await expect(overview.getByText(SEED_TITLE)).toBeVisible();
		await expect(overview.getByText(SEED_CODE)).toBeVisible();
		await expect(overview.getByText("In configuration")).toBeVisible();
		await expect(overview).not.toContainText("IN_CONFIGURATION");
		await expect(overview.locator("[data-itw-next-action]")).toBeVisible();
		await expect(overview.locator("[data-itw-next-action] button")).toBeVisible();
		await expect(overview.getByText(/Next step:/i)).toBeVisible();
		await expect(overview.locator("[data-itw-step-grid] [data-itw-step-card]")).toHaveCount(13);
		await expect(
			overview.locator('[data-itw-step-card][data-itw-step-current="1"] .kt-itw-step-title', {
				hasText: "IT Requirements",
			}),
		).toBeVisible();
		await expect(overview.getByText("National Treasury")).toBeVisible();
		await expect(overview.getByText("Open Tender")).toBeVisible();
		await expect(overview.getByText("PP-ICT-2024-009")).toBeVisible();
		await expect(overview).not.toContainText("Governance");
		await expect(overview).not.toContainText("Locked");
		await expect(overview).not.toContainText(/\bReady\b/);
		const publicationCard = overview.locator("[data-itw-step-card] .kt-itw-step-title", {
			hasText: "Publication Readiness",
		});
		await publicationCard.scrollIntoViewIfNeeded();
		await expect(publicationCard).toBeVisible();
	});

	test("dashboard continue preserves configuration_id on browser refresh", async () => {
		await openNativeDashboard(page);
		const seedRow = page.locator(`tr[data-configuration-id="${SEED_CODE}"]`);
		await seedRow.getByRole("button", { name: /^Continue Setup$/i }).click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-overview/, { timeout: 15_000 });
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`), { timeout: 15_000 });

		await page.reload();
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`), { timeout: 15_000 });

		await expect(page.locator('[data-testid="it-wizard-overview"]')).toHaveAttribute(
			"data-itw-native-loaded",
			"1",
			{ timeout: 30_000 },
		);
		await expect(page.getByText("Configuration required")).toHaveCount(0);
		await expect(page.getByRole("heading", { name: "Tender Configuration Home" })).toBeVisible();
	});

	test("overview route without configuration_id redirects to dashboard", async () => {
		await page.goto(ITW_OVERVIEW_ROUTE);
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/, { timeout: 15_000 });
	});

	test("overview route with configuration_id hydrates from API", async () => {
		await openNativeOverview(page, SEED_CODE);
		await expect(page.getByRole("heading", { name: "Tender Configuration Home" })).toBeVisible();
		await expect(page.locator("[data-itw-step-grid] [data-itw-step-card]")).toHaveCount(13);
		await expect(page.locator("body")).not.toContainText("TNT/024/2024");
		await expect(page.locator("body")).not.toContainText("CONF-99283");
	});

	test("native overview keeps Procurement sidebar rail visible", async () => {
		await openNativeOverview(page, SEED_CODE);
		await expect(page.locator(".body-sidebar-container")).toBeVisible();
		await expect(page.getByRole("link", { name: "Procurement Home", exact: true })).toBeVisible();
	});

	test("step card opens detail drawer with purpose and configured items", async () => {
		await openNativeOverview(page, SEED_CODE);
		const overview = page.locator('[data-testid="it-wizard-overview"]');
		const reqCard = overview.locator('[data-itw-step-card][data-itw-step-code="IT_REQUIREMENTS"]');
		await reqCard.locator(".kt-itw-step-title").click();
		const portal = page.locator("#kt-itw-home-drawer-portal");
		await expect(portal).toHaveAttribute("data-itw-home-drawer-open", "1", { timeout: 10_000 });
		const drawer = page.locator('[data-testid="it-wizard-overview-drawer"]');
		await expect(drawer).toBeVisible({ timeout: 10_000 });
		await expect(drawer.getByText("IT Requirements")).toBeVisible();
		await expect(drawer.getByText("Purpose")).toBeVisible();
		await expect(drawer.getByText("What is configured")).toBeVisible();
		await expect(drawer.getByText("Progress", { exact: true })).toBeVisible();
		await drawer.locator("[data-itw-drawer-close]").click();
		await expect(portal).toHaveAttribute("data-itw-home-drawer-open", "0", { timeout: 10_000 });
		await expect(portal).toBeHidden({ timeout: 10_000 });
	});

	test("step card continue navigates to IT Requirements route", async () => {
		await openNativeOverview(page, SEED_CODE);
		const currentCard = page.locator('[data-itw-step-card][data-itw-step-current="1"]');
		await currentCard.getByRole("button", { name: /^Continue$/i }).click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-it-requirements/, { timeout: 15_000 });
		await expect(page).toHaveURL(new RegExp(`configuration_id=${SEED_CODE}`));
	});
});
