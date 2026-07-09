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
