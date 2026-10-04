import { execSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const CANONICAL_PACKAGE_ID = "KE-PPRA-IT-2022-04";

function ensureCanonicalStdImport() {
	const zipPath =
		"/home/midasuser/frappe-bench/apps/kentender_v1/docs/std-prod-impl/data/KE-PPRA-IT-2022-04_Seed_Package_v1_1.zip";
	execSync(
		`cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.package_import.commit.run --kwargs '${JSON.stringify({ zip_path: zipPath })}'`,
		{ stdio: "ignore" },
	);
}

async function clickLibraryOpenButton(
	iframe: ReturnType<import("@playwright/test").Page["frameLocator"]>,
) {
	const openButton = iframe.getByRole("button", { name: "Open" }).first();
	const scrollHost = iframe.locator('[data-std-prod-table-scroll-host="1"]');
	if ((await scrollHost.count()) > 0) {
		await scrollHost.evaluate(() => {
			const openBtn = Array.from(document.querySelectorAll("button")).find(
				(btn) => (btn.textContent || "").trim() === "Open",
			);
			if (openBtn) {
				openBtn.scrollIntoView({ block: "nearest", inline: "end" });
			}
		});
	}
	await openButton.click({ force: true });
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

	test("version detail removes compensatory top offset after header harmonization", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const iframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("body")).toHaveClass(/std-prod-header-harmonized/);
		const mainPaddingTop = await iframe.locator("main").evaluate((el) => {
			return window.getComputedStyle(el).paddingTop;
		});
		expect(mainPaddingTop).toBe("0px");
		const chromeGap = await iframe.locator('[data-testid="std-prod-page-header"]').evaluate((header) => {
			const rect = header.getBoundingClientRect();
			const next = header.nextElementSibling;
			if (!next) {
				return 999;
			}
			return next.getBoundingClientRect().top - rect.bottom;
		});
		expect(chromeGap).toBeLessThan(4);
	});

	test("validation report keeps activation banner flush under harmonized header", async ({ page }) => {
		await page.goto("/desk/std-validation-report");
		const iframe = page.frameLocator('[data-testid="std-prod-std-validation-report-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("body")).toHaveClass(/std-prod-header-harmonized/);
		const mainPaddingTop = await iframe.locator("main").evaluate((el) => {
			return window.getComputedStyle(el).paddingTop;
		});
		expect(mainPaddingTop).toBe("0px");
		const chromeGap = await iframe.locator('[data-testid="std-prod-page-header"]').evaluate((header) => {
			const rect = header.getBoundingClientRect();
			const next = header.nextElementSibling;
			if (!next) {
				return 999;
			}
			return next.getBoundingClientRect().top - rect.bottom;
		});
		expect(chromeGap).toBeLessThan(4);
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

	test("library table exposes horizontal scroll inside viewport-bounded pane", async ({ page }) => {
		await page.goto("/desk/std-library");
		const iframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("body.std-prod-table-viewport")).toHaveCount(0);
		await expect(iframe.locator('[data-std-prod-table-scroll-host="1"]')).toBeVisible();
		const scrollHost = iframe.locator('[data-std-prod-table-scroll-host="1"]');
		const rail = iframe.locator(
			'[data-std-prod-table-hscroll-rail="1"].std-prod-table-hscroll-rail--viewport.std-prod-table-hscroll-rail--active',
		);
		await expect(rail).toBeVisible();
		const metrics = await scrollHost.evaluate((el) => {
			const table = el.querySelector("table");
			const styles = window.getComputedStyle(el);
			return {
				overflowX: styles.overflowX,
				overflowY: styles.overflowY,
				scrollWidth: el.scrollWidth,
				clientWidth: el.clientWidth,
				scrollHeight: el.scrollHeight,
				clientHeight: el.clientHeight,
				tableScrollWidth: table ? table.scrollWidth : 0,
			};
		});
		expect(metrics.overflowX).toMatch(/auto|scroll/);
		expect(["visible", "auto"]).toContain(metrics.overflowY);
		expect(metrics.scrollHeight).toBeLessThanOrEqual(metrics.clientHeight + 2);
		expect(Math.max(metrics.scrollWidth, metrics.tableScrollWidth)).toBeGreaterThan(
			metrics.clientWidth,
		);
		await rail.evaluate((el) => {
			el.scrollLeft = 240;
		});
		expect(await scrollHost.evaluate((el) => el.scrollLeft)).toBeGreaterThan(0);
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

	test("library Open navigates to version detail when family has single version", async ({ page }) => {
		await page.goto("/desk/std-library");
		const libraryIframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(libraryIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await clickLibraryOpenButton(libraryIframe);
		await expect(page).toHaveURL(/\/desk\/std-version-detail/, { timeout: 30_000 });

		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(versionIframe.getByText(CANONICAL_PACKAGE_ID).first()).toBeVisible();
	});

	test("STD navigation keeps Procurement sidebar rail visible", async ({ page }) => {
		await page.goto("/desk/std-library");
		const libraryIframe = page.frameLocator('[data-testid="std-prod-std-library-iframe"]');
		await expect(libraryIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await clickLibraryOpenButton(libraryIframe);
		await expect(page).toHaveURL(/\/desk\/std-version-detail/, {
			timeout: 30_000,
		});

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
		await versionIframe
			.locator("section")
			.filter({ hasText: "Governance & Lifecycle Actions" })
			.getByRole("button", { name: "Traceability" })
			.click();
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
		await expect(sectionRows.first()).toContainText("Cover Page");
		await expect(sectionRows.nth(1)).toContainText("Table of Contents");
		await expect(sectionRows.nth(2)).toContainText("Preface");

		await expect(sectionsIframe.locator('[data-testid="std-prod-clause-map-header"]')).toContainText(
			"Cover Page",
		);

		await sectionRows.filter({ hasText: "Section X - General Conditions of Contract" }).click();
		await expect(sectionsIframe.locator('[data-testid="std-prod-clause-map-header"]')).toContainText(
			"Section X - General Conditions of Contract",
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
			.filter({ hasText: "Section X - General Conditions of Contract" })
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
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-code"]')).toContainText("GCC-006");
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-legal-text"]')).toContainText(
			"Fraud and Corruption",
		);
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-legal-text"]')).not.toContainText(
			"not yet extracted",
		);
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-legal-text"]')).not.toContainText(
			"pending extraction",
		);
		await expect(clauseIframe.getByText("ConflictOfInterestCheck")).toHaveCount(0);
		await expect(clauseIframe.getByText("RB-ITT-3.1-V2.4")).toHaveCount(0);
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-legal-text"]')).toContainText(
			"extracted from the official source",
		);
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-render-preview"]')).not.toContainText(
			"TITLE EXTRACTED FULL TEXT HASH PENDING",
		);

		await page.goto("/desk/std-section-clauses");
		await expect(sectionsIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await sectionsIframe
			.locator(".std-prod-section-row")
			.filter({ hasText: "Section X - General Conditions of Contract" })
			.click();
		await sectionsIframe
			.locator(".std-prod-clause-row")
			.filter({ hasText: "Definitions" })
			.first()
			.click();
		await expect(page).toHaveURL(/\/desk\/std-clause-detail/, { timeout: 30_000 });
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-title"]')).toContainText(
			"Definitions",
		);
		await expect(clauseIframe.locator('[data-testid="std-prod-clause-code"]')).toContainText("GCC-001");
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

		await versionIframe.locator("table tbody tr").filter({ hasText: "Parameter Dictionary" }).click();
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
		await versionIframe2.locator("table tbody tr").filter({ hasText: "Rule Dictionary" }).click();
		await expect(page).toHaveURL(/\/desk\/std-rule-dictionary/, { timeout: 30_000 });
		const rulesIframe = page.frameLocator('[data-testid="std-prod-std-rule-dictionary-iframe"]');
		await expect(rulesIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});

		await page.goto("/desk/std-version-detail");
		const versionIframe3 = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe3.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await versionIframe3.getByRole("button", { name: "View Usage" }).click();
		await expect(page).toHaveURL(/\/desk\/std-usage-and-tender-bindings/, { timeout: 30_000 });
	});

	test("version detail price schedule row opens prod iframe not doctype list", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await versionIframe.locator("table tbody tr").filter({ hasText: "Price Schedule Schema" }).click();
		await expect(page).toHaveURL(/\/desk\/std-price-schedule-schema/, { timeout: 30_000 });
		await expect(page.locator('[data-testid="std-prod-std-price-schedule-schema-iframe"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator(".list-row-container, .list-row")).toHaveCount(0);
	});

	test("version detail integrity rows deep-link section tree vs clause inventory", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});

		await versionIframe.locator("table tbody tr").filter({ hasText: "Sections & Containers" }).click();
		await expect(page).toHaveURL(/\/desk\/std-section-clauses/, { timeout: 30_000 });
		const sectionsIframe = page.frameLocator('[data-testid="std-prod-std-section-clauses-iframe"]');
		await expect(sectionsIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(sectionsIframe.locator("body")).toHaveAttribute("data-std-prod-map-focus", "sections");
		await expect(sectionsIframe.locator('[data-testid="std-prod-clause-map-header"]')).toContainText(
			"Cover Page",
		);

		await page.goto("/desk/std-version-detail");
		const versionIframe2 = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe2.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await versionIframe2.locator("table tbody tr").filter({ hasText: "Standard Clauses" }).click();
		await expect(page).toHaveURL(/\/desk\/std-section-clauses/, { timeout: 30_000 });
		const clausesIframe = page.frameLocator('[data-testid="std-prod-std-section-clauses-iframe"]');
		await expect(clausesIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(clausesIframe.locator("body")).toHaveAttribute("data-std-prod-map-focus", "clauses");
		await expect(clausesIframe.locator('[data-testid="std-prod-clause-map-header"]')).toContainText(
			"Clause Inventory",
		);
		await expect(clausesIframe.locator('[data-testid="std-prod-clause-map-subtitle"]')).toContainText(
			/clauses across all sections/,
		);
		await expect(clausesIframe.locator(".std-prod-clause-row")).toHaveCount(94);
	});

	test("version detail workspace opens form evaluation and render blocks", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const versionIframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(versionIframe.locator('[data-testid="std-version-workspace"]')).toBeVisible();

		await versionIframe
			.locator('[data-std-workspace-route="std-form-schema-manager"]')
			.click();
		await expect(page).toHaveURL(/\/desk\/std-form-schema-manager/, { timeout: 30_000 });
		const formIframe = page.frameLocator('[data-testid="std-prod-std-form-schema-manager-iframe"]');
		await expect(formIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(formIframe.locator("nav[data-std-prod-breadcrumb]")).toContainText("KE-PPRA-IT-2022-04");

		await page.goto("/desk/std-version-detail");
		const versionIframe2 = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe2.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await versionIframe2.locator('[data-std-workspace-route="std-evaluation-schema"]').click();
		await expect(page).toHaveURL(/\/desk\/std-evaluation-schema/, { timeout: 30_000 });

		await page.goto("/desk/std-version-detail");
		const versionIframe3 = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(versionIframe3.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await versionIframe3.locator('[data-std-workspace-route="std-render-blocks"]').click();
		await expect(page).toHaveURL(/\/desk\/std-render-blocks/, { timeout: 30_000 });
	});

	test("clause detail shows verbatim hash and page references", async ({ page }) => {
		await page.goto("/desk/std-section-clauses");
		const sectionsIframe = page.frameLocator('[data-testid="std-prod-std-section-clauses-iframe"]');
		await expect(sectionsIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await sectionsIframe
			.locator(".std-prod-section-row")
			.filter({ hasText: "Section X - General Conditions of Contract" })
			.click();
		await sectionsIframe.locator(".std-prod-clause-row").filter({ hasText: "Fraud and Corruption" }).click();
		const clauseIframe = page.frameLocator('[data-testid="std-prod-std-clause-detail-iframe"]');
		await expect(clauseIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(clauseIframe.getByText(/SHA-256:/)).toBeVisible();
		await expect(clauseIframe.getByText("SHA-256: unavailable")).toHaveCount(0);
		await expect(clauseIframe.getByText(/Page(s)? \d+/)).toBeVisible();
		await expect(clauseIframe.getByText(/Verification:/i)).toBeVisible();
	});

	test("validation report surfaces legal review gate banner", async ({ page }) => {
		await page.goto("/desk/std-validation-report");
		const iframe = page.frameLocator('[data-testid="std-prod-std-validation-report-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.getByText(/LEGAL_REVIEW_PENDING|legal review pending/i).first()).toBeVisible();
	});

	test("parameter detail shows extracted source hash for TDS-013", async ({ page }) => {
		await page.goto("/desk/std-library");
		await page.evaluate(() => {
			// @ts-ignore
			frappe.route_options = {
				package_id: "KE-PPRA-IT-2022-04",
				parameter_key: "KE-PPRA-IT-2022-04.parameter.tds.013",
			};
			// @ts-ignore
			frappe.set_route("std-parameter-detail");
		});
		await expect(page).toHaveURL(/\/desk\/std-parameter-detail/, { timeout: 30_000 });
		const paramIframe = page.frameLocator('[data-testid="std-prod-std-parameter-detail-iframe"]');
		await expect(paramIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(
			paramIframe.getByText("Source text hash and verbatim extraction are pending"),
		).toHaveCount(0);
		await expect(paramIframe.getByText(/SHA-256: 714153/)).toBeVisible();
	});
});
