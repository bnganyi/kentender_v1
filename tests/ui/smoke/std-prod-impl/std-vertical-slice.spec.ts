import { execSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const CANONICAL_PACKAGE_ID = "KE-PPRA-IT-2022-04";

function ensureCanonicalStdImport() {
	execSync(
		"cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.package_import.commit.run",
		{ stdio: "ignore" },
	);
}

test.describe("STD prod vertical slice API hydration", () => {
	test.beforeAll(() => {
		ensureCanonicalStdImport();
	});

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("library header harmonizes STD Engine brand and page title", async ({ page }) => {
		await page.goto("/desk/std-library");
		const iframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		const header = iframe.locator('[data-testid="std-prod-page-header"]');
		await expect(header.getByText("STD Engine", { exact: true })).toBeVisible();
		await expect(header.getByRole("heading", { name: "Official STD Library" })).toBeVisible();
		await expect(header.getByText("KenTender", { exact: true })).toHaveCount(0);
	});

	test("library iframe hydrates canonical package identity from read API", async ({ page }) => {
		await page.goto("/desk/std-library");
		const iframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("body")).toHaveAttribute(
			"data-std-package-id",
			CANONICAL_PACKAGE_ID,
		);
		await expect(iframe.getByText(CANONICAL_PACKAGE_ID).first()).toBeVisible();
		await expect(iframe.getByText(/2024-04/)).toHaveCount(0);
	});

	test("library KPI cards hydrate from read API instead of mock totals", async ({ page }) => {
		await page.goto("/desk/std-library");
		const iframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		const kpiGrid = iframe.locator(".col-span-12.lg\\:col-span-8").first();
		await expect(kpiGrid.getByText("42", { exact: true })).toHaveCount(0);
		await expect(kpiGrid.getByText("38", { exact: true })).toHaveCount(0);
		const familiesCard = kpiGrid.locator("div").filter({ hasText: "STD FAMILIES" }).first();
		await expect(familiesCard.getByText("1", { exact: true })).toBeVisible();
		const tableFooter = iframe.locator(".border-t.border-outline-variant").filter({ hasText: "Showing" }).last();
		await expect(tableFooter).toContainText("1-1");
		await expect(tableFooter).toContainText("families");
		await expect(tableFooter.getByRole("button", { name: "2", exact: true })).toHaveCount(0);
		await expect(tableFooter.getByRole("button", { name: "4", exact: true })).toHaveCount(0);
		await expect(iframe.getByText("Unauthorized active versions").locator("..").getByText("0", { exact: true })).toBeVisible();
	});

	test("family detail table footer reflects version count", async ({ page }) => {
		await page.goto("/desk/std-family-detail");
		const iframe = page.frameLocator('[data-testid="std-prod-std-family-detail-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		const tableFooter = iframe.locator(".border-t.border-outline-variant").filter({ hasText: "Showing" }).last();
		await expect(tableFooter).toContainText("1-1");
		await expect(tableFooter.getByRole("button", { name: "2", exact: true })).toHaveCount(0);
	});

	test("family detail KPI cards hydrate from read API", async ({ page }) => {
		await page.goto("/desk/std-family-detail");
		const iframe = page.frameLocator('[data-testid="std-prod-std-family-detail-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		const kpiGrid = iframe.locator(".grid.grid-cols-1.md\\:grid-cols-4").first();
		await expect(kpiGrid.getByText("v2.4.0", { exact: true })).toHaveCount(0);
		await expect(kpiGrid.getByText("12", { exact: true })).toHaveCount(0);
		await expect(kpiGrid.getByText("1,482", { exact: true })).toHaveCount(0);
		await expect(kpiGrid.getByText("DRAFT", { exact: true })).toBeVisible();
		await expect(kpiGrid.getByText("Across 1 cycles")).toBeVisible();
		const tendersCard = kpiGrid.locator("div").filter({ hasText: "TENDERS USING FAMILY" }).first();
		await expect(tendersCard.getByText("0", { exact: true })).toBeVisible();
		await expect(iframe.getByText("USAGE INSIGHTS").locator("..").getByText("1,240")).toHaveCount(0);
	});

	test("family detail iframe hides mock KPIs until hydration completes", async ({ page }) => {
		await page.goto("/desk/std-family-detail");
		const iframe = page.frameLocator('[data-testid="std-prod-std-family-detail-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("#std-prod-hydration-gate")).toHaveCount(1);
	});

	test("library Open navigates to family detail with API context", async ({ page }) => {
		await page.goto("/desk/std-library");
		const libraryIframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(libraryIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await libraryIframe.getByRole("button", { name: "Open" }).first().click();
		await expect(page).toHaveURL(/\/desk\/std-family-detail/, { timeout: 30_000 });

		const familyIframe = page.frameLocator('[data-testid="std-prod-std-family-detail-iframe"]');
		await expect(familyIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(familyIframe.getByText(CANONICAL_PACKAGE_ID).first()).toBeVisible();
	});

	test("STD navigation keeps Procurement sidebar rail visible", async ({ page }) => {
		await page.goto("/desk/std-library");
		const libraryIframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(libraryIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await libraryIframe.getByRole("button", { name: "Open" }).first().click();
		await expect(page).toHaveURL(/\/desk\/std-family-detail/, { timeout: 30_000 });

		await expect(page.getByRole("link", { name: "Procurement Home", exact: true })).toBeVisible();
		await expect(page.getByRole("link", { name: "Planning", exact: true })).toBeVisible();
		await expect(page.getByText("STD Engine Administrator")).toHaveCount(0);
		await expect(page.getByRole("link", { name: "STD Clause", exact: true })).toHaveCount(0);

		await page.goto("/desk/std-version-detail");
		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(page.getByRole("link", { name: "Procurement Home", exact: true })).toBeVisible();
		await expect(page.getByText("STD Engine Administrator")).toHaveCount(0);
	});

	test("version detail exposes validation and audit slice routes", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(versionIframe.getByText(CANONICAL_PACKAGE_ID).first()).toBeVisible();
		await versionIframe.getByRole("button", { name: "View Audit Trail" }).click();
		await expect(page).toHaveURL(/\/desk\/std-audit-log/, { timeout: 30_000 });

		const auditIframe = page.frameLocator('[data-testid="std-prod-std-audit-log-iframe"]');
		await expect(auditIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(auditIframe.getByText("PACKAGE_IMPORT_COMMITTED").first()).toBeVisible({
			timeout: 30_000,
		});
	});

	test("validation report lists persisted findings", async ({ page }) => {
		await page.goto("/desk/std-validation-report");
		const iframe = page.frameLocator('[data-testid="std-prod-std-validation-report-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.getByText(CANONICAL_PACKAGE_ID).first()).toBeVisible();
		await expect(iframe.getByText(/BLOCKER|Blocker/i).first()).toBeVisible();
	});

	test("version detail Traceability opens source document page", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await versionIframe.getByRole("button", { name: "Traceability" }).click();
		await expect(page).toHaveURL(/\/desk\/std-source-doc/, { timeout: 30_000 });
		const sourceIframe = page.frameLocator('[data-testid="std-prod-std-source-doc-iframe"]');
		await expect(sourceIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(sourceIframe.locator('[data-testid="std-prod-page-header"]')).toContainText(
			"Source Documents & Traceability",
		);
	});

	test("section clause map orders tree and updates clause panel on selection", async ({ page }) => {
		await page.goto("/desk/std-section-clauses");
		const sectionsIframe = page.frameLocator('[data-testid="std-prod-std-section-clauses-iframe"]');
		await expect(sectionsIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});

		const sectionRows = sectionsIframe.locator('[data-testid="std-prod-section-row"]');
		await expect(sectionRows.first()).toContainText("Cover / title identity page");
		await expect(sectionRows.nth(1)).toContainText("Invitation to Tender");
		await expect(sectionRows.nth(2)).toContainText("Instructions to Tenderers");

		await expect(sectionsIframe.locator('[data-testid="std-prod-clause-map-header"]')).toContainText(
			"Cover / title identity page",
		);

		await sectionRows.filter({ hasText: "General Conditions of Contract" }).click();
		await expect(sectionsIframe.locator('[data-testid="std-prod-clause-map-header"]')).toContainText(
			"General Conditions of Contract",
		);
		await expect(sectionsIframe.locator(".std-prod-clause-row").first()).toContainText("GCC");
	});

	test("clause detail loads selected clause and switches identity on revisit", async ({ page }) => {
		await page.goto("/desk/std-section-clauses");
		const sectionsIframe = page.frameLocator('[data-testid="std-prod-std-section-clauses-iframe"]');
		await expect(sectionsIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await sectionsIframe
			.locator(".std-prod-section-row")
			.filter({ hasText: "General Conditions of Contract" })
			.click();
		await sectionsIframe.locator(".std-prod-clause-row").filter({ hasText: "Fraud and Corruption" }).click();
		await expect(page).toHaveURL(/\/desk\/std-clause-detail/, { timeout: 30_000 });

		const clauseIframe = page.frameLocator('[data-testid="std-prod-std-clause-detail-iframe"]');
		await expect(clauseIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-title"]')).toContainText(
			"Fraud and Corruption",
		);
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-code"]')).toContainText("GCC 6");
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-legal-text"]')).not.toContainText(
			"3.1 A Tenderer may be a firm",
		);

		await page.goto("/desk/std-section-clauses");
		await expect(sectionsIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await sectionsIframe
			.locator(".std-prod-section-row")
			.filter({ hasText: "General Conditions of Contract" })
			.click();
		await sectionsIframe
			.locator(".std-prod-clause-row")
			.filter({ hasText: "Contract and Interpretation" })
			.click();
		await expect(page).toHaveURL(/\/desk\/std-clause-detail/, { timeout: 30_000 });
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-title"]')).toContainText(
			"Contract and Interpretation",
		);
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-code"]')).toContainText("GCC 1");
	});

	test("section clause map Source Traceability opens source document page", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await versionIframe.getByText("Sections & Containers").click();
		await expect(page).toHaveURL(/\/desk\/std-section-clauses/, { timeout: 30_000 });
		const sectionsIframe = page.frameLocator('[data-testid="std-prod-std-section-clauses-iframe"]');
		await expect(sectionsIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await sectionsIframe.getByRole("button", { name: "SOURCE TRACEABILITY" }).click();
		await expect(page).toHaveURL(/\/desk\/std-source-doc/, { timeout: 30_000 });
		const sourceIframe = page.frameLocator('[data-testid="std-prod-std-source-doc-iframe"]');
		await expect(sourceIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
	});

	test("version detail navigates to parameter dictionary and usage bindings", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});

		await versionIframe.getByText("Parameters & Rules").click();
		await expect(page).toHaveURL(/\/desk\/std-parameter-dictionary/, { timeout: 30_000 });
		const paramIframe = page.frameLocator('[data-testid="std-prod-std-parameter-dictionary-iframe"]');
		await expect(paramIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});

		await page.goto("/desk/std-version-detail");
		const versionIframe2 = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe2.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await versionIframe2.getByRole("button", { name: "View Usage" }).click();
		await expect(page).toHaveURL(/\/desk\/std-usage-and-tender-bindings/, { timeout: 30_000 });
	});

	test("version detail price schedule row opens prod iframe not doctype list", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await versionIframe.getByText("Price Schedule Schema").click();
		await expect(page).toHaveURL(/\/desk\/std-price-schedule-schema/, { timeout: 30_000 });
		await expect(page.locator('[data-testid="std-prod-std-price-schedule-schema-iframe"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator(".list-row-container, .list-row")).toHaveCount(0);
	});
});
