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
});
