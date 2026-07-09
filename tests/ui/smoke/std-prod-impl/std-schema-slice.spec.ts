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
		await dictIframe
			.locator(".std-prod-param-row")
			.filter({ hasText: "Address for clarifications" })
			.click();
		await expect(page).toHaveURL(/\/desk\/std-parameter-detail/, { timeout: 30_000 });

		const detailIframe = page.frameLocator('[data-testid="std-prod-std-parameter-detail-iframe"]');
		await expect(detailIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(detailIframe.locator('[data-testid="std-prod-parameter-title"]')).toContainText(
			"Address for clarifications",
		);
		await expect(detailIframe.locator('[data-testid="std-prod-parameter-breadcrumb"]')).toContainText(
			"tds.clarification_address",
		);
		await expect(detailIframe.getByText("Tender Reference ID")).toHaveCount(0);
		await expect(detailIframe.getByText("Render Block RB-ITT-1.1")).toHaveCount(0);
		await expect(detailIframe.getByText("LONG_TEXT", { exact: true })).toBeVisible();
		await expect(detailIframe.getByText("No render blocks or validation rules are bound to this parameter yet.")).toBeVisible();
	});

	test("rule dictionary and form schema manager hydrate list rows", async ({ page }) => {
		await page.goto("/desk/std-rule-dictionary");
		const ruleIframe = page.frameLocator('[data-testid="std-prod-std-rule-dictionary-iframe"]');
		await expect(ruleIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(ruleIframe.locator(".std-prod-rule-row").first()).toBeVisible();
		await expect(ruleIframe.getByText("RULE-VAL-REF-01")).toHaveCount(0);
		await expect(ruleIframe.getByText("tender_ref_id")).toHaveCount(0);

		await page.goto("/desk/std-form-schema-manager");
		const formIframe = page.frameLocator('[data-testid="std-prod-std-form-schema-manager-iframe"]');
		await expect(formIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(formIframe.locator(".std-prod-form-row").first()).toBeVisible();
		await expect(formIframe.getByText("FORM-TECH-01")).toHaveCount(0);
	});

	test("rule row navigates to hydrated rule detail", async ({ page }) => {
		await page.goto("/desk/std-rule-dictionary");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-rule-dictionary-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await dictIframe
			.locator(".std-prod-rule-row")
			.filter({ hasText: "Clarification deadline must fall before tender submission deadline." })
			.click();
		await expect(page).toHaveURL(/\/desk\/std-rule-detail/, { timeout: 30_000 });

		const detailIframe = page.frameLocator('[data-testid="std-prod-std-rule-detail-iframe"]');
		await expect(detailIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(detailIframe.locator('[data-testid="std-prod-rule-title"]')).toContainText(
			"Clarification deadline must fall before tender submission deadline.",
		);
		await expect(detailIframe.locator('[data-testid="std-prod-rule-breadcrumb"]')).toContainText(
			"tds.clarification_deadline_before_submission",
		);
		await expect(detailIframe.getByText("RULE-VAL-REF-01")).toHaveCount(0);
		await expect(detailIframe.getByText("tender_ref_id")).toHaveCount(0);
		await expect(detailIframe.getByText("String Length Check")).toHaveCount(0);
		await expect(detailIframe.locator('[data-testid="std-prod-rule-type"]')).toContainText("VALIDATION");
		await expect(detailIframe.locator('[data-testid="std-prod-rule-severity"]')).toContainText("BLOCKER");
	});

	test("form row navigates to hydrated form detail", async ({ page }) => {
		await page.goto("/desk/std-form-schema-manager");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-form-schema-manager-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await dictIframe
			.locator(".std-prod-form-row")
			.filter({ hasText: "Certificate of Independent Tender Determination" })
			.click();
		await expect(page).toHaveURL(/\/desk\/std-form-detail-field-builder/, { timeout: 30_000 });

		const detailIframe = page.frameLocator(
			'[data-testid="std-prod-std-form-detail-field-builder-iframe"]',
		);
		await expect(detailIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(detailIframe.locator('[data-testid="std-prod-form-title"]')).toContainText(
			"Certificate of Independent Tender Determination",
		);
		await expect(detailIframe.locator('[data-testid="std-prod-form-code"]')).toContainText(
			"CERTIFICATE_INDEPENDENT_TENDER_DETERMINATION",
		);
		await expect(detailIframe.getByText("FORM-TECH-01")).toHaveCount(0);
		await expect(detailIframe.getByText("tender_ref_id")).toHaveCount(0);
		await expect(detailIframe.getByRole("cell", { name: "DECLARANT_NAME" })).toBeVisible();
		await expect(detailIframe.locator("table tbody tr").first()).toContainText("Declarant name");
	});

	test("requirement schema manager hydrates list-only schema rows", async ({ page }) => {
		await page.goto("/desk/std-requirement-schema-manager");
		const iframe = page.frameLocator('[data-testid="std-prod-std-requirement-schema-manager-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator(".std-prod-req-row").first()).toBeVisible();
	});

	test("price schedule schema loads prod iframe not doctype list", async ({ page }) => {
		await page.goto("/desk/std-price-schedule-schema");
		await expect(page.locator('[data-testid="std-prod-std-price-schedule-schema-iframe"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator(".list-row-container, .list-row")).toHaveCount(0);
		const iframe = page.frameLocator('[data-testid="std-prod-std-price-schedule-schema-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("body")).toHaveAttribute(
			"data-std-package-id",
			CANONICAL_PACKAGE_ID,
		);
	});

	test("evaluation schema loads prod iframe not doctype list", async ({ page }) => {
		await page.goto("/desk/std-evaluation-schema");
		await expect(page.locator('[data-testid="std-prod-std-evaluation-schema-iframe"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator(".list-row-container, .list-row")).toHaveCount(0);
		const iframe = page.frameLocator('[data-testid="std-prod-std-evaluation-schema-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
	});
});
