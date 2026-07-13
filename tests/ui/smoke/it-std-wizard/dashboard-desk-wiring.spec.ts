import { execSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const DASHBOARD_ROUTE = "/desk/it-tender-configuration-dashboard";
const SEED_CODE = "ITCFG-DASH-SEED-001";
const SEED_TITLE = "Data Center Hardware Refresh";
const CANONICAL_PACKAGE_ID = "KE-PPRA-IT-2022-04";

function ensureActiveStdForCreate() {
	const zipPath =
		"/home/midasuser/frappe-bench/apps/kentender_v1/docs/std-prod-impl/data/KE-PPRA-IT-2022-04_Seed_Package_v1_1.zip";
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.package_import.draft_cleanup.force_reset_package_state_for_tests --kwargs '${JSON.stringify({ package_id: CANONICAL_PACKAGE_ID, family_code: "KE-PPRA-IT" })}'`,
		{ stdio: "ignore" },
	);
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.package_import.commit.run --kwargs '${JSON.stringify({ zip_path: zipPath })}'`,
		{ stdio: "ignore" },
	);
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.services.legal_review_service.approve_all_pending --kwargs '${JSON.stringify({ package_id: CANONICAL_PACKAGE_ID })}'`,
		{ stdio: "ignore" },
	);
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.services.activation_readiness_service.sync_activation_flags --kwargs '${JSON.stringify({ package_id: CANONICAL_PACKAGE_ID })}'`,
		{ stdio: "ignore" },
	);
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.services.activation_service.activate_version --kwargs '${JSON.stringify({ package_id: CANONICAL_PACKAGE_ID })}'`,
		{ stdio: "ignore" },
	);
}

test.describe("IT Wizard Tender Configuration Dashboard Desk wiring", () => {
	test.beforeAll(() => {
		ensureActiveStdForCreate();
	});

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("desk route loads dashboard design in iframe with hydrated KPIs", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		await expect(page.locator(".page-head")).toBeHidden();
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("[data-itw-kpi-grid]")).toBeVisible();
		await expect(iframe.locator("[data-itw-kpi-grid] > div")).toHaveCount(6);
		await expect(iframe.locator("[data-itw-table-scroll-host]")).toBeVisible();
		await expect(iframe.locator("[data-itw-table-footer]")).toBeVisible();
		await expect(iframe.getByText("Tender Configuration Dashboard").first()).toBeVisible();
		await expect(iframe.getByText(/^In Configuration$/i).first()).toBeVisible();
		await expect(iframe.getByText(SEED_TITLE)).toBeVisible({ timeout: 30_000 });
		const inConfigCard = iframe
			.locator("p", { hasText: /^In Configuration$/i })
			.first()
			.locator("..")
			.locator(".font-data-mono-lg");
		await expect(inConfigCard).not.toHaveText("24");
	});

	test("procurement sidebar opens dashboard after Tender Management", async ({ page }) => {
		await page.goto("/desk/procurement-home");
		await page.getByRole("link", { name: "Tender Configuration Dashboard", exact: true }).click();
		await expect(page).toHaveURL(/\/desk\/it-tender-configuration-dashboard/);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("[data-itw-kpi-grid]")).toBeVisible();
		await expect(iframe.locator("[data-itw-kpi-grid] > div")).toHaveCount(6);
		await expect(iframe.locator("[data-itw-table-scroll-host]")).toBeVisible();
		await expect(iframe.locator("[data-itw-table-footer]")).toBeVisible();
		await expect(iframe.getByText(SEED_CODE)).toBeVisible({ timeout: 30_000 });
	});

	test("create tender configuration opens dialog and succeeds", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("[data-itw-kpi-grid]")).toBeVisible();
		await expect(iframe.locator("[data-itw-kpi-grid] > div")).toHaveCount(6);
		await expect(iframe.locator("[data-itw-table-scroll-host]")).toBeVisible();
		await expect(iframe.locator("[data-itw-table-footer]")).toBeVisible();
		await iframe.getByRole("button", { name: /Create Tender Configuration/i }).click();
		const dialog = page.locator(".modal.show .modal-dialog");
		await expect(dialog).toBeVisible({ timeout: 10_000 });
		const uniqueTitle = `Playwright Dashboard Create ${Date.now()}`;
		await dialog.locator('input[data-fieldname="title"]').fill(uniqueTitle);
		await dialog.locator('input[data-fieldname="std_template_version_id"]').fill(CANONICAL_PACKAGE_ID);
		await dialog.getByRole("button", { name: "Create", exact: true }).click();
		await expect(dialog).toBeHidden({ timeout: 15_000 });
		await expect(iframe.getByText(uniqueTitle)).toBeVisible({ timeout: 15_000 });
	});

	test("path A route context pre-fills create dialog from query params", async ({ page }) => {
		await page.goto(
			`${DASHBOARD_ROUTE}?tender_id=TND-PW-HANDOFF&std_version_id=${CANONICAL_PACKAGE_ID}&plan_item_id=PPI-PW-001`,
		);
		const dialog = page.locator(".modal.show .modal-dialog").first();
		await expect(dialog).toBeVisible({ timeout: 30_000 });
		await expect(dialog.locator('input[data-fieldname="std_template_version_id"]')).toHaveValue(
			CANONICAL_PACKAGE_ID,
		);
		await expect(dialog.locator('input[data-fieldname="title"]')).toHaveValue(
			/IT Tender Configuration for TND-PW-HANDOFF/,
		);
		await dialog.locator(".btn-modal-close, button.close").first().click();
	});

	test("STD Library page has no Launch IT Wizard control", async ({ page }) => {
		await page.goto("/desk/std-library");
		const iframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(iframe.getByRole("heading", { name: "Standard Tender Documents" })).toBeVisible({
			timeout: 30_000,
		});
		await expect(iframe.getByText(/Launch IT/i)).toHaveCount(0);
		await expect(page.getByText(/Launch IT STD Configuration/i)).toHaveCount(0);
	});

	test("search filters configuration list", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.getByText(SEED_TITLE)).toBeVisible({ timeout: 30_000 });
		await expect(iframe.getByText("Digital ID Integration Hub")).toBeVisible();
		await iframe.locator('input[data-itw-search="1"]').fill("Digital ID");
		await expect(iframe.getByText(SEED_TITLE)).toBeHidden({ timeout: 15_000 });
		await expect(iframe.getByText("Digital ID Integration Hub")).toBeVisible();
	});

	test("status filter includes validation failed and filters list", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator('select[data-itw-filter="status"] option', { hasText: "Validation Failed" })).toHaveCount(1);
		await iframe.locator('select[data-itw-filter="status"]').selectOption("VALIDATION_FAILED");
		await expect(iframe.getByText("Digital ID Integration Hub")).toBeVisible({ timeout: 15_000 });
		await expect(iframe.getByText(SEED_TITLE)).toBeHidden({ timeout: 15_000 });
	});

	test("method column hides internal enum codes", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(
			iframe.locator("table tbody td").filter({ hasText: /^Open Tender$/ }).first(),
		).toBeVisible({ timeout: 30_000 });
		await expect(iframe.locator("table tbody")).not.toContainText("OPEN_NATIONAL");
	});

	test("kpi cards hide mock today deltas when no real delta", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const inConfigCard = iframe
			.locator("p", { hasText: /^In Configuration$/i })
			.first()
			.locator("..");
		await expect(inConfigCard.getByText("+3 today")).toHaveCount(0);
	});

	test("advanced filter drawer applies validation failed filter", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await iframe.locator("[data-itw-open-filter-drawer]").click();
		await expect(iframe.locator("[data-itw-filter-drawer]")).toBeVisible();
		await iframe
			.locator('[data-itw-drawer-filter="validation_failed"]')
			.check();
		await iframe.locator('[data-itw-drawer-action="apply"]').click();
		await expect(iframe.locator("[data-itw-filter-drawer]")).toHaveClass(/hidden/);
		await expect(iframe.getByText("Digital ID Integration Hub")).toBeVisible({ timeout: 15_000 });
		await expect(iframe.getByText(SEED_TITLE)).toBeHidden({ timeout: 15_000 });
	});

	test("rows per page control syncs and hides extra page buttons", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await iframe.locator('input[data-itw-search="1"]').fill(SEED_CODE);
		await expect(iframe.getByText(SEED_TITLE)).toBeVisible({ timeout: 15_000 });
		await expect(iframe.locator('[data-itw-pager-page="2"]')).toHaveCount(0);
		await iframe.locator("[data-itw-page-size]").selectOption("10");
		await expect(iframe.locator("[data-itw-page-size]")).toHaveValue("10");
		await expect(iframe.locator('[data-itw-pager-page="2"]')).toHaveCount(0);
	});

	test("pager active page matches showing range", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await iframe.locator("[data-itw-page-size]").selectOption("10");
		const showing = iframe.locator("[data-itw-pager-showing]");
		await expect(showing).toContainText(/Showing/i, { timeout: 15_000 });
		const text = await showing.innerText();
		const match = text.match(/Showing\s+(\d+)-(\d+)\s+of\s+(\d+)/i);
		expect(match).not.toBeNull();
		const start = Number(match![1]);
		const total = Number(match![3]);
		const expectedPage = Math.floor((start - 1) / 10) + 1;
		await expect(iframe.locator(`[data-itw-pager-page="${expectedPage}"]`)).toHaveClass(/bg-primary/);
		if (total >= 31) {
			const lastPage = Math.ceil(total / 10);
			await iframe.locator(`[data-itw-pager-page="${lastPage}"]`).click();
			const expectedStart = (lastPage - 1) * 10 + 1;
			await expect(showing).toContainText(`${expectedStart}-${total}`, { timeout: 15_000 });
			await expect(iframe.locator(`[data-itw-pager-page="${lastPage}"]`)).toHaveClass(/bg-primary/);
		}
	});

	test("drawer stubs category and shows capability note", async ({ page }) => {
		await page.goto(DASHBOARD_ROUTE);
		const iframe = page.frameLocator('[data-testid="it-wizard-dashboard-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await iframe.locator("[data-itw-open-filter-drawer]").click();
		await expect(iframe.locator("[data-itw-drawer-capability-note]")).toBeVisible();
		const goodsLabel = iframe.locator('label[data-itw-drawer-stub-surface]', { hasText: /^Goods$/ });
		await expect(goodsLabel).toBeVisible();
		await expect(goodsLabel.locator('input[type="checkbox"]')).toBeDisabled();
	});
});
