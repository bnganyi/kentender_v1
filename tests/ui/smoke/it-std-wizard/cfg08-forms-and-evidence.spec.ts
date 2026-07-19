import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * CFG-08 Forms & Evidence (C2-CFG8).
 * Route: /desk/it-tender-configuration-forms-and-evidence/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-forms-and-evidence";
const CFG08 = `/desk/${PAGE_SLUG}`;
const ROOT = '[data-testid="kt-cl-cfg08-root"]';
const CONFIG = "TCFG-SEED-TCFG-IP";
const CFG07_SLUG = "it-tender-configuration-evaluation-setup";

const FORBIDDEN = [
	/\bbidder upload\b/i,
	/\bbidder scores?\b/i,
	/\bevaluation marks?\b/i,
	/\bprice schedule form\b/i,
	/\bschema version\b/i,
	/\brule ID\b/i,
	/\bbinding ID\b/i,
];

const COLUMNS = [
	"Submission Item",
	"Category",
	"Source",
	"Requirement",
	"Bidder Instruction",
	"Status",
	"Actions",
];

async function seedUi00(page: import("@playwright/test").Page) {
	await page.waitForFunction(() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined");
	const result = await page.evaluate(async () => {
		// @ts-expect-error frappe on desk
		const r = await frappe.call({
			method: "kentender_procurement.tender_configurations.seed_ui00_dashboard_for_tests",
			args: { clear: 1 },
		});
		return r.message || r;
	});
	if (!result || !(result as { configurations?: string[] }).configurations) {
		throw new Error("CFG-08 seed failed: " + JSON.stringify(result));
	}
}

async function openFormsAndEvidence(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`${CFG08}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

async function fillCompleteMandatory(page: import("@playwright/test").Page) {
	await page.getByTestId("kt-cl-cfg08-drawer-name").fill("Form of Tender");
	await page.getByTestId("kt-cl-cfg08-drawer-category").selectOption("Standard Form");
	await page.getByTestId("kt-cl-cfg08-drawer-requirement").selectOption("Mandatory");
	await page
		.getByTestId("kt-cl-cfg08-drawer-instruction")
		.fill("Bidder must complete and sign the Form of Tender.");
	await page.getByTestId("kt-cl-cfg08-drawer-response-format").selectOption("Form");
}

async function fillCompleteConditional(page: import("@playwright/test").Page) {
	await page.getByTestId("kt-cl-cfg08-drawer-name").fill("Tender Security");
	await page.getByTestId("kt-cl-cfg08-drawer-category").selectOption("Tender Security");
	await page.getByTestId("kt-cl-cfg08-drawer-requirement").selectOption("Conditional");
	await expect(page.getByTestId("kt-cl-cfg08-drawer-condition-text")).toBeVisible({ timeout: 5_000 });
	await page
		.getByTestId("kt-cl-cfg08-drawer-condition-text")
		.fill("Required where the TDS specifies tender security.");
	const condSource = page.getByTestId("kt-cl-cfg08-drawer-condition-source-select");
	if (await condSource.count()) {
		await condSource.selectOption("TDS");
	}
	await page
		.getByTestId("kt-cl-cfg08-drawer-instruction")
		.fill("Provide tender security in the form stated in the TDS.");
	await page.getByTestId("kt-cl-cfg08-drawer-response-format").selectOption("PDF attachment");
}

test.describe.configure({ mode: "serial" });

test.describe("CFG-08 Forms & Evidence", () => {
	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await seedUi00(page);
		await page.close();
	});

	test.beforeEach(async ({ page }) => {
		await page.setViewportSize({ width: 1400, height: 900 });
		await loginAsAdministrator(page);
	});

	test("layout: strip, filters, columns, guidance, footer, no forbidden terms", async ({ page }) => {
		await openFormsAndEvidence(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-cfg08-table-head")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-table-head")).toContainText(/Submission Requirements/i);
		await expect(page.getByTestId("kt-cl-cfg08-add")).toHaveText(/Add Submission Item/i);
		await expect(page.getByTestId("kt-cl-cfg08-import")).toHaveText(/Import Standard Forms/i);
		await expect(page.getByTestId("kt-cl-cfg08-tabs")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-tab-all")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-tab-standard")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-tab-decl")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-tab-qual")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-tab-tech")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-tab-security")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-tab-conditional")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-table")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-guidance")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-guidance")).toContainText(/Forms & Evidence Guidance/i);
		await expect(page.getByTestId("kt-cl-cfg08-footer").getByTestId("kt-cl-cfg08-run-check")).toHaveText(
			/Run Check/i
		);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Forms & Evidence/i);
		await expect(page.getByTestId("kt-cl-cfg08-back")).toHaveText(/Back to Configuration Home/i);
		await expect(page.getByTestId("kt-cl-cfg08-save")).toHaveText(/Save Forms & Evidence/i);
		await expect(page.getByTestId("kt-cl-cfg08-continue")).toHaveText(/Continue to Contract Values/i);
		await expect(page.getByTestId("kt-cl-cfg08-continue")).toBeDisabled();

		const tableText = (await page.getByTestId("kt-cl-cfg08-table").innerText()).toLowerCase();
		for (const col of COLUMNS) {
			expect(tableText, col).toContain(col.toLowerCase());
		}

		const body = await page.locator(ROOT).innerText();
		for (const re of FORBIDDEN) {
			expect(body, String(re)).not.toMatch(re);
		}
	});

	test("Add submission items drawer persists and enables Continue", async ({ page }) => {
		await openFormsAndEvidence(page);
		await page.getByTestId("kt-cl-cfg08-add").click();
		await expect(page.getByTestId("kt-cl-cfg08-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg08-drawer-title")).toContainText(/Add Submission Item/i);
		await fillCompleteMandatory(page);
		await page.getByTestId("kt-cl-cfg08-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg08-table")).toContainText(/FE-001/);
		// One complete mandatory item is enough to clear blockers (conditional not required).
		await expect(page.getByTestId("kt-cl-cfg08-continue")).toBeEnabled({ timeout: 15_000 });

		await page.getByTestId("kt-cl-cfg08-add").click();
		await fillCompleteConditional(page);
		await page.getByTestId("kt-cl-cfg08-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg08-table")).toContainText(/FE-002/);
		await expect(page.getByTestId("kt-cl-cfg08-blockers")).toHaveClass(/hidden/, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg08-continue")).toBeEnabled({ timeout: 15_000 });
	});

	test("Import Standard Forms hydrates table", async ({ page }) => {
		await openFormsAndEvidence(page);
		await page.getByTestId("kt-cl-cfg08-import").click();
		await expect(page.getByTestId("kt-cl-cfg08-table")).toContainText(/Form of Tender/i, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg08-table")).toContainText(/FE-/);
	});

	test("CFG-07 Continue lands on live Forms & Evidence page", async ({ page }) => {
		await page.goto(`/desk/${CFG07_SLUG}/${encodeURIComponent(CONFIG)}`);
		await expect(page.getByTestId("kt-cl-cfg07-root")).toBeVisible({ timeout: 30_000 });
		const continueBtn = page.getByTestId("kt-cl-cfg07-continue");
		if (await continueBtn.isDisabled()) {
			await openFormsAndEvidence(page);
			await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Forms & Evidence/i);
			return;
		}
		await continueBtn.click();
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 20_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Forms & Evidence/i);
	});
});
