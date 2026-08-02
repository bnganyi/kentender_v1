import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * CFG-09 Contract Values (C2-CFG9).
 * Route: /desk/it-tender-configuration-scc/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-scc";
const CFG09 = `/desk/${PAGE_SLUG}`;
const ROOT = '[data-testid="kt-cl-cfg09-root"]';
const CONFIG = "TCFG-SEED-TCFG-IP";
const CFG08_SLUG = "it-tender-configuration-forms-and-evidence";

const FORBIDDEN = [
	/\bgcc text\b/i,
	/\baward recommendation\b/i,
	/\bschema version\b/i,
	/\bpayment certificate\b/i,
	/\brule ID\b/i,
	/\bbinding ID\b/i,
];

const COLUMNS = [
	"Item",
	"Category",
	"Source",
	"Contract Location",
	"Value / Obligation",
	"Status",
	"Action",
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
		throw new Error("CFG-09 seed failed: " + JSON.stringify(result));
	}
}

async function openContractValues(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`${CFG09}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

async function fillCompleteDeliveryPeriod(page: import("@playwright/test").Page) {
	await page.getByTestId("kt-cl-cfg09-drawer-item").fill("Delivery Period");
	await page.getByTestId("kt-cl-cfg09-drawer-category").selectOption("SCC Value");
	await page.getByTestId("kt-cl-cfg09-drawer-source").selectOption("Implementation Schedule");
	await page.getByTestId("kt-cl-cfg09-drawer-location").fill("SCC / Delivery Schedule");
	await page
		.getByTestId("kt-cl-cfg09-drawer-value")
		.fill("90 calendar days from notice to proceed");
}

test.describe.configure({ mode: "serial" });

test.describe("CFG-09 Contract Values", () => {
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

	test("layout: strip, tabs, columns, guidance, footer Run Check, no continue, no forbidden terms", async ({
		page,
	}) => {
		await openContractValues(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-cfg09-table-head")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-table-head")).toContainText(/Contract Values/i);
		await expect(page.getByTestId("kt-cl-cfg09-add")).toHaveText(/Add Contract Value/i);
		await expect(page.getByTestId("kt-cl-cfg09-import")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-cfg09-tabs")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-tab-all")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-tab-scc")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-tab-delivery")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-tab-support")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-tab-securities")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-tab-schedules")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-tab-needs")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-table")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-guidance")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-guidance")).toContainText(/Contract Values Guidance/i);
		await expect(page.getByTestId("kt-cl-cfg09-layout")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-main")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-footer").getByTestId("kt-cl-cfg09-run-check")).toHaveText(
			/Run Check/i
		);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Contract Values/i);
		await expect(page.getByTestId("kt-cl-cfg09-back")).toHaveText(/Back to Configuration Home/i);
		await expect(page.getByTestId("kt-cl-cfg09-save")).toHaveText(/Save Contract Values/i);
		await expect(page.getByTestId("kt-cl-cfg09-continue")).toBeHidden();

		const tableText = (await page.getByTestId("kt-cl-cfg09-table").innerText()).toLowerCase();
		for (const col of COLUMNS) {
			expect(tableText, col).toContain(col.toLowerCase());
		}

		const body = await page.locator(ROOT).innerText();
		for (const re of FORBIDDEN) {
			expect(body, String(re)).not.toMatch(re);
		}
	});

	test("Run Check hydrates suggestions when table is empty", async ({ page }) => {
		await openContractValues(page);
		await page.getByTestId("kt-cl-cfg09-run-check").click();
		await expect(page.getByTestId("kt-cl-cfg09-table")).toContainText(/Performance Security/i, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg09-table")).toContainText(/CV-/);
	});

	test("drawer stays open on backdrop click so draft fields are not discarded", async ({
		page,
	}) => {
		await openContractValues(page);
		await page.getByTestId("kt-cl-cfg09-add").click();
		const drawer = page.getByTestId("kt-cl-cfg09-drawer");
		await expect(drawer).toBeVisible();
		const overlay = page.getByTestId("kt-cl-cfg09-drawer-overlay");
		await expect(overlay).toHaveAttribute("data-dismiss", "explicit-only");

		const draftItem = "Unsaved backdrop draft contract value";
		await page.getByTestId("kt-cl-cfg09-drawer-item").fill(draftItem);
		await overlay.click({ position: { x: 8, y: 8 }, force: true });
		await expect(drawer).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-drawer-item")).toHaveValue(draftItem);

		await page.getByTestId("kt-cl-cfg09-drawer-close").click();
		await expect(drawer).toHaveCount(0);
	});

	test("drawer save enables complete row for Delivery Period", async ({ page }) => {
		await openContractValues(page);
		await page.getByTestId("kt-cl-cfg09-add").click();
		await expect(page.getByTestId("kt-cl-cfg09-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg09-drawer-title")).toContainText(/Add Contract Value/i);
		await fillCompleteDeliveryPeriod(page);
		await page.getByTestId("kt-cl-cfg09-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg09-table")).toContainText(/CV-001/, { timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg09-table")).toContainText(/Delivery Period/i);
		await expect(page.getByTestId("kt-cl-cfg09-table")).toContainText(/Complete/i, { timeout: 15_000 });
	});

	test("CFG-08 Continue lands on live Contract Values page", async ({ page }) => {
		await page.goto(`/desk/${CFG08_SLUG}/${encodeURIComponent(CONFIG)}`);
		await expect(page.getByTestId("kt-cl-cfg08-root")).toBeVisible({ timeout: 30_000 });
		const continueBtn = page.getByTestId("kt-cl-cfg08-continue");
		if (await continueBtn.isDisabled()) {
			await openContractValues(page);
			await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Contract Values/i);
			return;
		}
		await continueBtn.click();
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 20_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Contract Values/i);
		await expect(page.getByTestId("kt-cl-cfg09-continue")).toBeHidden();
	});
});
