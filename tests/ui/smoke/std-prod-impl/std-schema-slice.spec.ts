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

test.describe("STD prod schema slice API hydration", () => {
	test.beforeAll(() => {
		ensureCanonicalStdImport();
	});

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test("parameter dictionary hydrates canonical rows from read API", async ({ page }) => {
		await page.goto("/desk/std-parameter-dictionary");
		const iframe = page.frameLocator('[data-testid="std-prod-std-parameter-dictionary-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("body")).toHaveAttribute(
			"data-std-package-id",
			CANONICAL_PACKAGE_ID,
		);
		await expect(iframe.locator(".std-prod-param-row").first()).toBeVisible();
		await expect(iframe.getByText(/2024-04/)).toHaveCount(0);
	});

	test("parameter row navigates to parameter detail", async ({ page }) => {
		await page.goto("/desk/std-parameter-dictionary");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-parameter-dictionary-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await dictIframe.locator(".std-prod-param-row").first().click();
		await expect(page).toHaveURL(/\/desk\/std-parameter-detail/, { timeout: 30_000 });

		const detailIframe = page.frameLocator('[data-testid="std-prod-std-parameter-detail-iframe"]');
		await expect(detailIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(detailIframe.locator("h1")).toContainText(/.+/);
	});

	test("rule dictionary and form schema manager hydrate list rows", async ({ page }) => {
		await page.goto("/desk/std-rule-dictionary");
		const ruleIframe = page.frameLocator('[data-testid="std-prod-std-rule-dictionary-iframe"]');
		await expect(ruleIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(ruleIframe.locator(".std-prod-rule-row").first()).toBeVisible();

		await page.goto("/desk/std-form-schema-manager");
		const formIframe = page.frameLocator('[data-testid="std-prod-std-form-schema-manager-iframe"]');
		await expect(formIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(formIframe.locator(".std-prod-form-row").first()).toBeVisible();
	});

	test("requirement schema manager hydrates list-only schema rows", async ({ page }) => {
		await page.goto("/desk/std-requirement-schema-manager");
		const iframe = page.frameLocator('[data-testid="std-prod-std-requirement-schema-manager-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator(".std-prod-req-row").first()).toBeVisible();
	});
});
