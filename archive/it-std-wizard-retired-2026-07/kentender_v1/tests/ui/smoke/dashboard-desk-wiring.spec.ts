import { test, expect, type Page } from "@playwright/test";

import { loginAsAdministrator } from "../../helpers/auth";
import {
	ITW_DASHBOARD_ROUTE,
	installOfflineAssetGuard,
	openNativeDashboard,
} from "../../helpers/itWizardDesk";

const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";
const PATH_A_PACKAGE = "PP-ICT-WIZARD-MODAL-001";

/**
 * ITW-01 / PW-ITW-DASH-01..05 — IT Tender Configurations dashboard (native page).
 *
 * Screen 01 is a native Frappe Desk page (DIA Create-Demand pattern): plain DOM,
 * hand-ported CSS, zero external requests. These are direct-DOM journey tests —
 * `page.locator` + `kt-itw-*` / `data-itw-*` hooks, no `frameLocator`, no iframe
 * hydration handshake. Auth pattern (locked, see
 * `.cursor/rules/it-wizard-test-gate.mdc`): ONE login per spec file via
 * `test.describe.serial` + shared `page` in `beforeAll`. Each test re-opens the
 * dashboard with a real `page.goto`, so every run is a fresh document load.
 * Site fixtures: `it_wizard_dashboard_seed` patch + active KE-PPRA-IT STD.
 * Run via `make it-wizard-screen-01-gate` (not the full wiring regression gate).
 */
test.describe.serial("IT Wizard IT Tender Configurations dashboard (native)", () => {
	let page: Page;

	test.beforeAll(async ({ browser }) => {
		page = await browser.newPage();
		await installOfflineAssetGuard(page);
		await loginAsAdministrator(page);
	});

	test.afterAll(async () => {
		await page.close();
	});

	// PW-ITW-DASH-01 ───────────────────────────────────────────────────────────
	test("loads KPI cards and the seeded configuration list with human labels", async () => {
		await openNativeDashboard(page);

		await expect(page.locator('[data-testid="it-wizard-dashboard"]')).toBeVisible();
		// Two headings carry this label by design (fixed app bar h1 + page h2).
		await expect(
			page.getByRole("heading", { name: "IT Tender Configurations" }).first(),
		).toBeVisible();

		// Four KPI cards.
		await expect(page.locator("[data-itw-kpi-grid] [data-itw-kpi]")).toHaveCount(4);
		await expect(page.locator('[data-itw-kpi="in_configuration"]')).toBeVisible();
		await expect(page.locator('[data-itw-kpi="publication_ready"]')).toBeVisible();

		// Seeded row visible with human status label — never enum codes.
		const seedRow = page.locator(`tr[data-configuration-id="${SEED_CODE}"]`);
		await expect(seedRow).toBeVisible();
		await expect(seedRow.getByText(SEED_TITLE)).toBeVisible();
		await expect(page.locator("[data-itw-tbody]")).not.toContainText("IN_CONFIGURATION");
		await expect(page.locator("[data-itw-tbody]")).not.toContainText("OPEN_NATIONAL");
	});

	// PW-ITW-DASH-02 ───────────────────────────────────────────────────────────
	test("create configuration modal fills through package and navigates to overview", async () => {
		await openNativeDashboard(page);

		await page.locator("[data-itw-open-create-modal]").click();
		const modal = page.locator("[data-itw-create-modal]");
		await expect(modal).toBeVisible();

		const packageSelect = page.locator("[data-itw-create-package]");
		await expect
			.poll(async () => packageSelect.locator("option").count(), { timeout: 20_000 })
			.toBeGreaterThan(1);

		// Pick the first real package option → read-only fields fill through.
		await packageSelect.selectOption({ index: 1 });
		await expect(page.locator("[data-itw-create-entity]")).not.toHaveValue("");
		await expect(page.locator("[data-itw-create-method]")).not.toHaveValue("");

		await page.locator("[data-itw-create-submit]").click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-overview/, { timeout: 20_000 });
		await expect(page).toHaveURL(/configuration_id=ITCFG-/, { timeout: 20_000 });
	});

	// PW-ITW-DASH-03 ───────────────────────────────────────────────────────────
	test("Path A query params auto-open the create modal", async () => {
		await page.goto(
			`${ITW_DASHBOARD_ROUTE}?procurement_package_id=${PATH_A_PACKAGE}`,
			{ waitUntil: "domcontentloaded" },
		);
		await expect(page.locator('[data-testid="it-wizard-dashboard"]')).toBeVisible({ timeout: 30_000 });
		await expect(page.locator("[data-itw-create-modal]")).toBeVisible({ timeout: 20_000 });
		await expect(page.locator("[data-itw-create-package]")).toBeVisible();
		// Close so it doesn't bleed into the next test. Use the footer Cancel
		// button — the header close icon can be overlapped by the field grid, and
		// Escape only fires when focus is inside the modal (not on Path A open).
		await page.getByRole("button", { name: "Cancel", exact: true }).click();
		await expect(page.locator("[data-itw-create-modal]")).toBeHidden({ timeout: 10_000 });
	});

	// PW-ITW-DASH-04 ───────────────────────────────────────────────────────────
	test("search narrows the configuration list", async () => {
		await openNativeDashboard(page);
		await expect(page.locator(`tr[data-configuration-id="${SEED_CODE}"]`)).toBeVisible();

		await page.locator("[data-itw-search]").fill("zzz-no-match-should-empty");
		await expect(page.locator("[data-itw-empty]")).toBeVisible({ timeout: 15_000 });

		await page.locator("[data-itw-search]").fill(SEED_TITLE);
		await expect(page.locator(`tr[data-configuration-id="${SEED_CODE}"]`)).toBeVisible({
			timeout: 15_000,
		});
	});

	// PW-ITW-DASH-05 ───────────────────────────────────────────────────────────
	test("filter drawer applies a status filter and shows a removable chip", async () => {
		await openNativeDashboard(page);

		// The Status chip is always visible (mockup contract): "Status: All" at rest.
		const stateChip = page.locator('[data-itw-filter-chip="state"]');
		await expect(stateChip).toContainText("Status: All");

		await page.locator("[data-itw-open-filter-drawer]").click();
		const drawer = page.locator("[data-itw-filter-drawer]");
		await expect(drawer).toBeVisible();

		const statusSelect = drawer.locator('[data-itw-drawer-filter="state"]');
		await expect
			.poll(async () => statusSelect.locator("option").count(), { timeout: 15_000 })
			.toBeGreaterThan(1);
		await statusSelect.selectOption({ index: 1 });
		await drawer.locator('[data-itw-drawer-action="apply"]').click();

		await expect(drawer).toBeHidden();
		// Applied status → chip label changes away from "All".
		await expect(stateChip).toBeVisible();
		await expect(stateChip).not.toContainText("Status: All");

		// Remove the chip → status reverts to the always-visible "All" default.
		await stateChip.locator("[data-itw-chip-remove]").click();
		await expect(page.locator('[data-itw-filter-chip="state"]')).toContainText("Status: All");
	});

	// PW-ITW-DASH-06 — Procurement sidebar stays visible ─────────────────────────
	test("keeps the Procurement sidebar rail visible with mockup chrome", async () => {
		await openNativeDashboard(page);

		await expect(page.locator(".body-sidebar-container")).toBeVisible();
		await expect(page.getByRole("link", { name: "Procurement Home", exact: true })).toBeVisible();
		await expect(page.locator("[data-itw-appbar]")).toBeVisible();
		const footer = page.locator("[data-itw-footer]");
		await expect(footer).toBeVisible();
		await expect(footer.getByRole("button", { name: /Export Report/ })).toBeVisible();
		await expect(footer.getByRole("button", { name: /Audit Logs/ })).toBeVisible();
	});

	// PW-ITW-DASH-07 — self-hosted brand typography + Material Symbols ───────────
	test("applies self-hosted brand fonts and Material Symbols (no CDN)", async () => {
		await openNativeDashboard(page);
		await page.evaluate(() => (document as unknown as { fonts: FontFaceSet }).fonts.ready);

		const titleFont = await page
			.locator(".kt-itw-page-title")
			.first()
			.evaluate((el) => getComputedStyle(el).fontFamily);
		expect(titleFont).toMatch(/Manrope/);

		const monoFont = await page
			.locator(".kt-itw-mono")
			.first()
			.evaluate((el) => getComputedStyle(el).fontFamily);
		expect(monoFont).toMatch(/JetBrains Mono/);

		const iconFont = await page
			.locator(".material-symbols-outlined")
			.first()
			.evaluate((el) => getComputedStyle(el).fontFamily);
		expect(iconFont).toMatch(/Material Symbols Outlined/);

		// The self-hosted faces are actually loaded (not just declared).
		const loaded = await page.evaluate(() => {
			const f = (document as unknown as { fonts: FontFaceSet }).fonts;
			return {
				manrope: f.check('700 28px "Manrope"'),
				symbols: f.check('24px "Material Symbols Outlined"'),
			};
		});
		expect(loaded.manrope).toBe(true);
		expect(loaded.symbols).toBe(true);
	});

	// PW-ITW-DASH-08 — numbered pagination + rows selector ───────────────────────
	test("renders numbered pagination and a rows-per-page selector", async () => {
		await openNativeDashboard(page);

		const footer = page.locator("[data-itw-table-footer]");
		await expect(footer).toBeVisible();
		await expect(footer.locator("[data-itw-rows-select]")).toBeVisible();
		// At least one numbered page button, and page 1 is active.
		await expect(footer.locator("[data-itw-pager-page]").first()).toBeVisible();
		await expect(footer.locator('[data-itw-pager-page="1"]')).toHaveClass(/kt-itw-pager-page--active/);
	});
});
