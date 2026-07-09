import { execSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const CANONICAL_PACKAGE_ID = "KE-PPRA-IT-2022-04";
const FIXTURE_SOURCE = "SMOKE_TEST_EXPECTATION";

function ensureCanonicalStdImport() {
	execSync(
		"cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.package_import.commit.run",
		{ stdio: "ignore" },
	);
}

test.describe("STD prod governance slice API hydration", () => {
	test.beforeAll(() => {
		ensureCanonicalStdImport();
	});

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("usage bindings header harmonizes STD Engine brand and page title", async ({ page }) => {
		await page.goto("/desk/std-usage-and-tender-bindings");
		const iframe = page.frameLocator('[data-testid="std-prod-std-usage-and-tender-bindings-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		const header = iframe.locator('[data-testid="std-prod-page-header"]');
		await expect(header.getByText("STD Engine", { exact: true })).toBeVisible();
		await expect(header.getByRole("heading", { name: "Usage and Tender Bindings" })).toBeVisible();
		await expect(header.getByText("KenTender", { exact: true })).toHaveCount(0);
	});

	test("usage bindings show seeded fixture source", async ({ page }) => {
		await page.goto("/desk/std-usage-and-tender-bindings");
		const iframe = page.frameLocator('[data-testid="std-prod-std-usage-and-tender-bindings-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("body")).toHaveAttribute(
			"data-std-package-id",
			CANONICAL_PACKAGE_ID,
		);
		await expect(iframe.getByText(FIXTURE_SOURCE).first()).toBeVisible();
	});

	test("usage bindings KPI cards hydrate real tender counts", async ({ page }) => {
		await page.goto("/desk/std-usage-and-tender-bindings");
		const iframe = page.frameLocator('[data-testid="std-prod-std-usage-and-tender-bindings-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		const kpiGrid = iframe.locator("section.grid.grid-cols-1.md\\:grid-cols-4").first();
		await expect(kpiGrid.getByText("1,248", { exact: true })).toHaveCount(0);
		await expect(kpiGrid.getByText("312", { exact: true })).toHaveCount(0);
		await expect(kpiGrid.getByText("936", { exact: true })).toHaveCount(0);
		await expect(kpiGrid.getByText("14", { exact: true })).toHaveCount(0);
		await expect(kpiGrid.getByText("+12%", { exact: true })).toBeHidden();
		const totalCard = kpiGrid.locator("div").filter({ hasText: "TOTAL TENDERS BOUND (ALL VERSIONS)" }).first();
		await expect(totalCard.getByText("0", { exact: true })).toBeVisible();
		const activeCard = kpiGrid.locator("div").filter({ hasText: "ACTIVE TENDERS (THIS VERSION)" }).first();
		await expect(activeCard.getByText("0", { exact: true })).toBeVisible();
	});

	test("usage bindings table footer reflects binding count", async ({ page }) => {
		await page.goto("/desk/std-usage-and-tender-bindings");
		const iframe = page.frameLocator('[data-testid="std-prod-std-usage-and-tender-bindings-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		const tableFooter = iframe
			.locator(".border-t.border-outline-variant")
			.filter({ hasText: "Showing" })
			.last();
		await expect(tableFooter).toContainText("1-3");
		await expect(tableFooter).toContainText("3 bindings");
		await expect(tableFooter.getByText("1,248")).toHaveCount(0);
		await expect(tableFooter.getByRole("button", { name: "2", exact: true })).toHaveCount(0);
		await expect(tableFooter.getByRole("button", { name: "125", exact: true })).toHaveCount(0);
		await expect(tableFooter.locator("span").filter({ hasText: "..." })).toBeHidden();
		const pageSizeSelect = tableFooter.locator("select");
		await expect(pageSizeSelect).toHaveClass(/min-w-12/);
	});

	test("import package review hydrates latest import run manifest fields", async ({ page }) => {
		await page.goto("/desk/std-import-package-review");
		const iframe = page.frameLocator('[data-testid="std-prod-std-import-package-review-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.getByText("manifest.json").first()).toBeVisible();
	});

	test("version diff shows single-version stub banner", async ({ page }) => {
		await page.goto("/desk/std-version-diff-and-supersession");
		const iframe = page.frameLocator(
			'[data-testid="std-prod-std-version-diff-and-supersession-iframe"]',
		);
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.getByText("SINGLE_VERSION_ONLY")).toBeVisible();
	});

	test("review composite hydrates package identity headers", async ({ page }) => {
		await page.goto("/desk/std-review-and-approval");
		const iframe = page.frameLocator('[data-testid="std-prod-std-review-and-approval-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.getByText(CANONICAL_PACKAGE_ID).first()).toBeVisible();
	});
});
