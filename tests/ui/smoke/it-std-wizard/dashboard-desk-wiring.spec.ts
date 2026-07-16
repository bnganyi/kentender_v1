import { test, expect, type Page } from "@playwright/test";

import { loginAsAdministrator } from "../../helpers/auth";
import {
	ITW_DASHBOARD_ROUTE,
	dashboardIframe,
	openHydratedDashboard,
} from "../../helpers/itWizardDesk";

const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";
const CANONICAL_PACKAGE_ID = "KE-PPRA-IT-2022-04";

/**
 * ITW-01 / PW-ITW-DASH-01 — dashboard Desk contract only.
 * Site fixtures: `it_wizard_dashboard_seed` patch + active KE-PPRA-IT STD.
 * Run via `make it-wizard-screen-01-gate` (not the full wiring regression gate).
 */
test.describe.serial("IT Wizard Tender Configuration Dashboard Desk wiring", () => {
	let page: Page;

	test.beforeAll(async ({ browser }) => {
		page = await browser.newPage();
		await loginAsAdministrator(page);
	});

	test.afterAll(async () => {
		await page.close();
	});

	test("desk route loads v2 dashboard with hydrated KPIs and reference labels", async () => {
		const iframe = await openHydratedDashboard(page);
		await expect(iframe.locator("[data-itw-kpi-grid] > div")).toHaveCount(4);
		await expect(iframe.locator("[data-itw-table-scroll-host]")).toBeVisible();
		await expect(iframe.getByText("IT Tender Configurations").first()).toBeVisible();
		await expect(iframe.getByText(SEED_TITLE)).toBeVisible({ timeout: 30_000 });
		await expect(
			iframe.locator("table tbody td").filter({ hasText: /^Open Tender$/ }).first(),
		).toBeVisible({ timeout: 30_000 });
		await expect(iframe.locator("table tbody")).not.toContainText("OPEN_NATIONAL");
		const inConfigCard = iframe
			.locator("p", { hasText: /^In Configuration$/i })
			.first()
			.locator("..");
		await expect(inConfigCard.locator(".font-data-mono-lg")).not.toHaveText("24");
		await expect(inConfigCard.getByText("+3 today")).toHaveCount(0);
		await expect(iframe.locator("[data-itw-filter-chips]").locator("span")).toHaveCount(0);
	});

	test("procurement sidebar opens dashboard after Tender Management", async () => {
		await page.goto("/desk/procurement-home");
		await page.getByRole("link", { name: "Tender Configuration Dashboard", exact: true }).click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/);
		const iframe = dashboardIframe(page);
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.getByText(SEED_CODE)).toBeVisible({ timeout: 30_000 });
	});

	test("create tender configuration opens modal and navigates to overview", async () => {
		const iframe = await openHydratedDashboard(page);
		await iframe.getByRole("button", { name: /Create Tender Configuration/i }).click();
		const modal = iframe.locator("#create-modal");
		await expect(modal).not.toHaveClass(/hidden/);
		await expect(page.locator(".modal.show .modal-dialog")).toHaveCount(0);
		const shellSelect = modal.locator("[data-itw-create-shell]");
		await expect
			.poll(async () => shellSelect.locator("option").count(), { timeout: 15_000 })
			.toBeGreaterThan(1);
		await shellSelect.selectOption({ index: 1 });
		await modal.locator("[data-itw-create-start]").click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-overview/, {
			timeout: 30_000,
		});
	});

	test("path A route context opens create modal with active STD", async () => {
		await page.goto(
			`${ITW_DASHBOARD_ROUTE}?tender_id=TND-PW-HANDOFF&std_version_id=${CANONICAL_PACKAGE_ID}&plan_item_id=PPI-PW-001`,
		);
		const iframe = dashboardIframe(page);
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const modal = iframe.locator("#create-modal");
		await expect(modal).not.toHaveClass(/hidden/, { timeout: 30_000 });
		await expect(modal.locator("[data-itw-create-std]")).toContainText(CANONICAL_PACKAGE_ID, {
			timeout: 15_000,
		});
		await modal.getByRole("button", { name: /^Cancel$/i }).click();
		await expect(modal).toHaveClass(/hidden/);
	});

	test("search filters configuration list", async () => {
		const iframe = await openHydratedDashboard(page);
		await expect(iframe.getByText(SEED_TITLE)).toBeVisible({ timeout: 30_000 });
		await expect(iframe.getByText("Digital ID Integration Hub")).toBeVisible();
		await iframe.locator('input[data-itw-search="1"]').fill("Digital ID");
		await expect(iframe.getByText(SEED_TITLE)).toBeHidden({ timeout: 15_000 });
		await expect(iframe.getByText("Digital ID Integration Hub")).toBeVisible();
	});

	test("advanced filter drawer applies needs-action filter and chips", async () => {
		const iframe = await openHydratedDashboard(page);
		await iframe.locator("[data-itw-open-filter-drawer]").click();
		await expect(iframe.locator("[data-itw-filter-drawer]")).toBeVisible();
		await iframe.locator('[data-itw-drawer-filter="validation_failed"]').check();
		await iframe.locator('[data-itw-drawer-action="apply"]').click();
		await expect(iframe.locator("[data-itw-filter-drawer]")).toHaveClass(/hidden/);
		await expect(iframe.locator("[data-itw-filter-chips] span").first()).toBeVisible();
		await expect(iframe.getByText("Digital ID Integration Hub")).toBeVisible({ timeout: 15_000 });
		await expect(iframe.getByText(SEED_TITLE)).toBeHidden({ timeout: 15_000 });
	});
});
