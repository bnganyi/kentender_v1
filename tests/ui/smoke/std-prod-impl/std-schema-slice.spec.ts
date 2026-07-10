import { execSync } from "node:child_process";
import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const CANONICAL_PACKAGE_ID = "KE-PPRA-IT-2022-04";
const PARAM_TDS_013 = "KE-PPRA-IT-2022-04.parameter.tds.013";
const PARAM_TDS_021 = "KE-PPRA-IT-2022-04.parameter.tds.021";
const FORM_IT_003 = "KE-PPRA-IT-2022-04.form.it_form_003";

function ensureCanonicalStdImport() {
	execSync(
		"cd /home/midasuser/frappe-bench && bench --site kentender.midas.com execute kentender_procurement.std_engine.package_import.commit.run",
		{ stdio: "ignore" },
	);
}

async function showAllTableRows(
	iframe: ReturnType<import("@playwright/test").Page["frameLocator"]>,
) {
	const pageSize = iframe.locator("[data-std-prod-page-size]");
	if ((await pageSize.count()) === 0) {
		return;
	}
	const optionValues = await pageSize.locator("option").evaluateAll((options) =>
		options
			.map((option) => parseInt((option as HTMLOptionElement).value || option.textContent || "", 10))
			.filter((value) => !Number.isNaN(value)),
	);
	const maxPageSize = optionValues.length ? Math.max(...optionValues) : 200;
	await pageSize.selectOption(String(maxPageSize));
}

async function revealTableRow(
	iframe: ReturnType<import("@playwright/test").Page["frameLocator"]>,
	selector: string,
) {
	const row = iframe.locator(selector);
	await expect(row).toHaveCount(1, { timeout: 30_000 });
	await row.evaluate((el) => {
		(el as HTMLElement).style.display = "";
	});
	return row;
}

async function clickParameterRow(
	iframe: ReturnType<import("@playwright/test").Page["frameLocator"]>,
	parameterKey: string,
) {
	const row = await revealTableRow(iframe, `[data-parameter-key="${parameterKey}"]`);
	await row.click({ force: true });
}

async function clickParameterViewRules(
	iframe: ReturnType<import("@playwright/test").Page["frameLocator"]>,
	parameterKey: string,
) {
	const row = await revealTableRow(iframe, `[data-parameter-key="${parameterKey}"]`);
	await row.locator('[title="View Rules"]').click({ force: true });
}

async function clickFormRow(
	iframe: ReturnType<import("@playwright/test").Page["frameLocator"]>,
	formKey: string,
) {
	await showAllTableRows(iframe);
	const row = await revealTableRow(iframe, `[data-form-key="${formKey}"]`);
	await row.click({ force: true });
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
		await expect(iframe.locator(".std-prod-param-row").first()).toBeVisible({ timeout: 30_000 });
		await expect(iframe.getByText(/2024-04/)).toHaveCount(0);
	});

	test("parameter dictionary preserves design table columns after hydration", async ({ page }) => {
		await page.goto("/desk/std-parameter-dictionary");
		const iframe = page.frameLocator('[data-testid="std-prod-std-parameter-dictionary-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("thead")).toContainText("PARAMETER KEY");
		await expect(iframe.locator("thead")).toContainText("VALIDATION RULES");
		await expect(iframe.locator("thead")).toContainText("ACTIONS");
		const firstRow = iframe.locator(".std-prod-param-row").first();
		await expect(firstRow.locator('[title="View Rules"]')).toBeVisible();
		await expect(firstRow.locator('[title="Open"]')).toBeVisible();
		const columnCount = await firstRow.evaluate((row) => row.querySelectorAll("td").length);
		expect(columnCount).toBe(13);
	});

	test("rule dictionary preserves design table columns after hydration", async ({ page }) => {
		await page.goto("/desk/std-rule-dictionary");
		const iframe = page.frameLocator('[data-testid="std-prod-std-rule-dictionary-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("thead")).toContainText("RULE KEY");
		await expect(iframe.locator("thead")).toContainText("SEVERITY");
		await expect(iframe.locator("thead")).toContainText("ACTIONS");
		const firstRow = iframe.locator(".std-prod-rule-row").first();
		await expect(firstRow.locator('[title="Open Rule"]')).toBeVisible();
		const columnCount = await firstRow.evaluate((row) => row.querySelectorAll("td").length);
		expect(columnCount).toBe(11);
	});

	test("parameter view rules opens filtered rule dictionary", async ({ page }) => {
		await page.goto("/desk/std-parameter-dictionary");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-parameter-dictionary-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await clickParameterViewRules(dictIframe, PARAM_TDS_021);
		await expect(page).toHaveURL(/\/desk\/std-rule-dictionary/, { timeout: 30_000 });

		const rulesIframe = page.frameLocator('[data-testid="std-prod-std-rule-dictionary-iframe"]');
		await expect(rulesIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(rulesIframe.locator("[data-std-prod-rule-filter-banner]")).toBeVisible();
		const ruleCount = await rulesIframe.locator(".std-prod-rule-row").count();
		expect(ruleCount).toBeGreaterThan(0);
		expect(ruleCount).toBeLessThan(22);
	});

	test("parameter row navigates to parameter detail", async ({ page }) => {
		await page.goto("/desk/std-parameter-dictionary");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-parameter-dictionary-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await clickParameterRow(dictIframe, PARAM_TDS_013);
		await expect(page).toHaveURL(/\/desk\/std-parameter-detail/, { timeout: 30_000 });

		const detailIframe = page.frameLocator('[data-testid="std-prod-std-parameter-detail-iframe"]');
		await expect(detailIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(detailIframe.locator('[data-testid="std-prod-parameter-title"]')).toContainText(
			"Clarification street address",
		);
		await expect(detailIframe.locator('[data-testid="std-prod-parameter-breadcrumb"]')).toContainText(
			"tds.013",
		);
		await expect(detailIframe.getByText("Tender Reference ID")).toHaveCount(0);
		await expect(detailIframe.getByText("Render Block RB-ITT-1.1")).toHaveCount(0);
		await expect(detailIframe.getByText("ADDRESS", { exact: true })).toBeVisible();
		await expect(detailIframe.getByRole("cell", { name: "tds.validation_013" })).toBeVisible();
		await expect(detailIframe.getByText("KE-PPRA-IT-2022-04.parameter.")).toHaveCount(0);
		await expect(detailIframe.getByText("not yet extracted", { exact: false })).toHaveCount(0);
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
		await expect(ruleIframe.locator("nav[data-std-prod-breadcrumb]")).toContainText("KE-PPRA-IT-2022-04");

		await page.goto("/desk/std-form-schema-manager");
		const formIframe = page.frameLocator('[data-testid="std-prod-std-form-schema-manager-iframe"]');
		await expect(formIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(formIframe.locator(".std-prod-form-row").first()).toBeVisible();
		await expect(formIframe.getByText("FORM-TECH-01")).toHaveCount(0);
		await expect(formIframe.locator("nav[data-std-prod-breadcrumb]")).toContainText("Form Schema Manager");
	});

	test("form schema manager preserves design table columns after hydration", async ({ page }) => {
		await page.goto("/desk/std-form-schema-manager");
		const iframe = page.frameLocator('[data-testid="std-prod-std-form-schema-manager-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("thead")).toContainText("Form Code");
		await expect(iframe.locator("thead")).toContainText("Field Count");
		await expect(iframe.locator("thead")).toContainText("Actions");
		const firstRow = iframe.locator(".std-prod-form-row").first();
		const columnCount = await firstRow.evaluate((row) => row.querySelectorAll("td").length);
		expect(columnCount).toBe(11);
		await expect(firstRow.locator('[title="Open Form"]')).toBeVisible();
	});

	test("price schedule pagination updates showing label and page size", async ({ page }) => {
		await page.goto("/desk/std-price-schedule-schema");
		const iframe = page.frameLocator('[data-testid="std-prod-std-price-schedule-schema-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator('[data-std-prod-table-footer]')).toContainText("Showing 1-6 of 6");
		await iframe.locator('[data-std-prod-page-size]').selectOption("25");
		await expect(iframe.locator('[data-std-prod-table-footer]')).toContainText("Showing 1-6 of 6");
		await expect(iframe.locator(".std-prod-price-row")).toHaveCount(6);
	});

	test("parameter detail breadcrumb returns to parameter dictionary", async ({ page }) => {
		await page.goto("/desk/std-parameter-dictionary");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-parameter-dictionary-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await clickParameterRow(dictIframe, PARAM_TDS_013);
		await expect(page).toHaveURL(/\/desk\/std-parameter-detail/, { timeout: 30_000 });

		const detailIframe = page.frameLocator('[data-testid="std-prod-std-parameter-detail-iframe"]');
		await expect(detailIframe.locator('[data-testid="std-prod-breadcrumb"]')).toBeVisible();
		await detailIframe.getByRole("link", { name: "Parameter Dictionary" }).click();
		await expect(page).toHaveURL(/\/desk\/std-parameter-dictionary/, { timeout: 30_000 });
	});

	test("version detail breadcrumb returns to STD library", async ({ page }) => {
		await page.goto("/desk/std-version-detail");
		const iframe = page.frameLocator('[data-testid="std-prod-std-version-detail-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator('[data-testid="std-prod-breadcrumb"]')).toBeVisible();
		await iframe.getByRole("link", { name: "STD Library" }).click();
		await expect(page).toHaveURL(/\/desk\/std-library/, { timeout: 30_000 });
	});

	test("form detail breadcrumb returns to form schema manager", async ({ page }) => {
		await page.goto("/desk/std-form-schema-manager");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-form-schema-manager-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await dictIframe.locator(".std-prod-form-row").first().click();
		await expect(page).toHaveURL(/\/desk\/std-form-detail-field-builder/, { timeout: 30_000 });

		const detailIframe = page.frameLocator('[data-testid="std-prod-std-form-detail-field-builder-iframe"]');
		await expect(detailIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await detailIframe.getByRole("link", { name: "Form Schema Manager" }).click();
		await expect(page).toHaveURL(/\/desk\/std-form-schema-manager/, { timeout: 30_000 });
	});

	test("rule detail breadcrumb returns to rule dictionary", async ({ page }) => {
		await page.goto("/desk/std-rule-dictionary");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-rule-dictionary-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await dictIframe
			.locator(".std-prod-rule-row")
			.filter({
				hasText: "Clarification request deadline offset must be populated before tender publication.",
			})
			.click();
		await expect(page).toHaveURL(/\/desk\/std-rule-detail/, { timeout: 30_000 });

		const detailIframe = page.frameLocator('[data-testid="std-prod-std-rule-detail-iframe"]');
		await expect(detailIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await detailIframe.getByRole("link", { name: "Rule Dictionary" }).click();
		await expect(page).toHaveURL(/\/desk\/std-rule-dictionary/, { timeout: 30_000 });
	});

	test("rule row navigates to hydrated rule detail", async ({ page }) => {
		await page.goto("/desk/std-rule-dictionary");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-rule-dictionary-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await dictIframe
			.locator(".std-prod-rule-row")
			.filter({
				hasText: "Clarification request deadline offset must be populated before tender publication.",
			})
			.click();
		await expect(page).toHaveURL(/\/desk\/std-rule-detail/, { timeout: 30_000 });

		const detailIframe = page.frameLocator('[data-testid="std-prod-std-rule-detail-iframe"]');
		await expect(detailIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(detailIframe.locator('[data-testid="std-prod-rule-title"]')).toContainText(
			"Clarification request deadline offset must be populated before tender publication.",
		);
		await expect(detailIframe.locator('[data-testid="std-prod-rule-breadcrumb"]')).toContainText(
			"tds.validation_021",
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
		await clickFormRow(dictIframe, FORM_IT_003);
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
			"IT-FORM-003",
		);
		await expect(detailIframe.getByText("FORM-TECH-01")).toHaveCount(0);
		await expect(detailIframe.getByText("tender_ref_id")).toHaveCount(0);
		await expect(detailIframe.locator("table tbody tr").first().getByRole("cell", { name: "reference", exact: true })).toBeVisible();
		await expect(detailIframe.locator("table tbody tr").first()).toContainText("Reference");
		await expect(detailIframe.locator("table tbody tr").nth(1)).toContainText("Legal Name");
	});

	test("parameter with validation rules shows business rule codes", async ({ page }) => {
		await page.goto("/desk/std-parameter-dictionary");
		const dictIframe = page.frameLocator('[data-testid="std-prod-std-parameter-dictionary-iframe"]');
		await expect(dictIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await clickParameterViewRules(dictIframe, PARAM_TDS_021);
		await expect(page).toHaveURL(/\/desk\/std-rule-dictionary/, { timeout: 30_000 });

		const rulesIframe = page.frameLocator('[data-testid="std-prod-std-rule-dictionary-iframe"]');
		await expect(rulesIframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(rulesIframe.locator("[data-std-prod-rule-filter-banner]")).toContainText("tds.021");
		const ruleRow = rulesIframe
			.locator(".std-prod-rule-row")
			.filter({
				hasText: "Clarification request deadline offset must be populated before tender publication.",
			})
			.first();
		await revealTableRow(rulesIframe, `[data-rule-key="KE-PPRA-IT-2022-04.rule.tds.validation_021"]`);
		await expect(ruleRow).toBeVisible();
		await expect(ruleRow).toContainText("tds.021");
		await expect(ruleRow.getByText("KE-PPRA-IT-2022-04.rule.")).toHaveCount(0);
	});

	test("render blocks dictionary shows business block codes", async ({ page }) => {
		await page.goto("/desk/std-render-blocks");
		const iframe = page.frameLocator('[data-testid="std-prod-std-render-blocks-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		const firstRow = iframe.locator(".std-prod-render-row").first();
		await expect(firstRow).toBeVisible();
		const code = (await firstRow.locator("td").first().innerText()).trim();
		expect(code.length).toBeGreaterThan(0);
		expect(code).not.toMatch(/KE-PPRA-IT-2022-04\.render_block\./);
		await expect(iframe.getByText("KE-PPRA-IT-2022-04.render_block.")).toHaveCount(0);
	});

	test("requirement schema manager preserves design table columns after hydration", async ({ page }) => {
		await page.goto("/desk/std-requirement-schema-manager");
		const iframe = page.frameLocator('[data-testid="std-prod-std-requirement-schema-manager-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("thead")).toContainText("Category");
		await expect(iframe.locator("thead")).toContainText("Requirement Class");
		await expect(iframe.locator("thead")).toContainText("Compliance Response Type");
		await expect(iframe.locator("thead")).toContainText("Actions");
		const firstRow = iframe.locator(".std-prod-req-row").first();
		await expect(firstRow).toBeVisible();
		const columnCount = await firstRow.evaluate((row) => row.querySelectorAll("td").length);
		expect(columnCount).toBe(11);
		await expect(iframe.locator('[data-std-prod-table-footer]')).toContainText(/Showing 1-\d+ of \d+/);
	});

	test("price schedule schema preserves design table columns after hydration", async ({ page }) => {
		await page.goto("/desk/std-price-schedule-schema");
		const iframe = page.frameLocator('[data-testid="std-prod-std-price-schedule-schema-iframe"]');
		await expect(iframe.locator("body")).toHaveAttribute("data-std-prod-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(iframe.locator("thead")).toContainText("Schedule Code");
		await expect(iframe.locator("thead")).toContainText("Formula / Calc Rule");
		await expect(iframe.locator("thead")).toContainText("Eval Linkage");
		await expect(iframe.locator("thead")).toContainText("Actions");
		const grandSummaryRow = iframe.locator(".std-prod-price-row").filter({
			has: iframe.locator("td").first().getByText("GS-001", { exact: true }),
		});
		await expect(grandSummaryRow.locator('[title="Open Schedule"]').first()).toBeVisible();
		const columnCount = await grandSummaryRow.evaluate((row) => row.querySelectorAll("td").length);
		expect(columnCount).toBe(14);
		await expect(grandSummaryRow).toContainText("Grand Summary Cost Table");
		await expect(grandSummaryRow).toContainText("Aggregated Total");
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
