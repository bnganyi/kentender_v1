import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * CFG-05 System Inventory & Bidder Background (C2-CFG5 + column-clarity).
 * Route: /desk/it-tender-configuration-system-inventory/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-system-inventory";
const CFG05 = `/desk/${PAGE_SLUG}`;
const ROOT = '[data-testid="kt-cl-cfg05-root"]';
const CONFIG = "TCFG-SEED-TCFG-IP";
const CFG04_SLUG = "it-tender-configuration-implementation-schedule";

const FORBIDDEN = [
	/\bAsset Register\b/i,
	/\bCMDB\b/i,
	/\bSecurity Console\b/i,
	/\bPayment Milestones\b/i,
	/\bschema version\b/i,
	/\bclause ID\b/i,
	/\bpass mark\b/i,
	/\bSupply & Installation\b/i,
];

const COLUMNS = [
	"ID",
	"Item",
	"Category",
	"Scope",
	"Bidder Consideration",
	"Disclosure Status",
	"Price Link",
	"Setup Status",
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
		throw new Error("CFG-05 seed failed: " + JSON.stringify(result));
	}
}

async function openInventory(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`${CFG05}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

async function fillCompleteItem(page: import("@playwright/test").Page) {
	await page.getByTestId("kt-cl-cfg05-drawer-title-input").fill("Existing Server Room");
	await page
		.getByTestId("kt-cl-cfg05-drawer-description")
		.fill(
			"Current server room with limited rack space and cooling constraints that bidders must account for during installation."
		);
	await page
		.getByTestId("kt-cl-cfg05-drawer-category")
		.selectOption("Infrastructure Environment");
	await page.getByTestId("kt-cl-cfg05-drawer-scope").selectOption("Context only");
	await page
		.getByTestId("kt-cl-cfg05-drawer-consideration")
		.fill("Bidder should account for installation constraints and rack space limitations.");
	await page.getByTestId("kt-cl-cfg05-drawer-disclosure").selectOption("Safe to disclose");
	await page
		.getByTestId("kt-cl-cfg05-drawer-price-link")
		.selectOption("May affect price schedule");
}

test.describe.configure({ mode: "serial" });

test.describe("CFG-05 System Inventory & Bidder Background", () => {
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

	test("layout: strip, banner, filters, columns, guidance, footer, no forbidden terms", async ({
		page,
	}) => {
		await openInventory(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-cfg05-banner")).toContainText(
			/Only include information bidders need/i
		);
		await expect(page.getByTestId("kt-cl-cfg05-filters")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg05-filter-all")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg05-layout")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg05-table")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg05-guidance")).toContainText(
			/Inventory & Background Guidance/i
		);
		await expect(page.getByTestId("kt-cl-cfg05-add")).toHaveText(/Add Inventory Item/i);
		await expect(page.getByTestId("kt-cl-cfg05-add-background")).toHaveText(
			/Add Background Note/i
		);
		await expect(page.getByTestId("kt-cl-cfg05-back")).toHaveText(/Back to Configuration Home/i);
		await expect(page.getByTestId("kt-cl-cfg05-save")).toHaveText(
			/Save Inventory & Background/i
		);
		await expect(page.getByTestId("kt-cl-cfg05-footer").getByTestId("kt-cl-cfg05-run-check")).toHaveText(
			/Run Check/i
		);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(
			/System Inventory & Bidder Background/i
		);
		await expect(page.getByTestId("kt-cl-cfg05-continue")).toHaveText(
			/Continue to Price Schedule/i
		);
		await expect(page.getByTestId("kt-cl-cfg05-continue")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-cfg05-blockers")).toHaveClass(/hidden/);

		const tableText = (await page.getByTestId("kt-cl-cfg05-table").innerText()).toLowerCase();
		for (const col of COLUMNS) {
			expect(tableText, col).toContain(col.toLowerCase());
		}
		expect(tableText).not.toContain("acceptance defined");
		expect(tableText).not.toContain("missing acceptance");

		const body = await page.locator(ROOT).innerText();
		for (const re of FORBIDDEN) {
			expect(body, String(re)).not.toMatch(re);
		}
	});

	test("drawer stays open on backdrop click so draft fields are not discarded", async ({
		page,
	}) => {
		await openInventory(page);
		await page.getByTestId("kt-cl-cfg05-add").click();
		const drawer = page.getByTestId("kt-cl-cfg05-drawer");
		await expect(drawer).toBeVisible();
		const overlay = page.getByTestId("kt-cl-cfg05-drawer-overlay");
		await expect(overlay).toHaveAttribute("data-dismiss", "explicit-only");

		const draftTitle = "Unsaved backdrop draft inventory";
		await page.getByTestId("kt-cl-cfg05-drawer-title-input").fill(draftTitle);
		await overlay.click({ position: { x: 8, y: 8 }, force: true });
		await expect(drawer).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg05-drawer-title-input")).toHaveValue(draftTitle);

		await page.getByTestId("kt-cl-cfg05-drawer-cancel").click();
		await expect(drawer).toHaveCount(0);
	});

	test("Add Inventory Item drawer persists and enables Continue", async ({ page }) => {
		await openInventory(page);
		await page.getByTestId("kt-cl-cfg05-add").click();
		await expect(page.getByTestId("kt-cl-cfg05-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg05-drawer-title")).toContainText(
			/Add Inventory Item/i
		);
		const drawerBody = page.getByTestId("kt-cl-cfg05-drawer-body");
		await expect(drawerBody.getByText(/1\.\s*Item Core Identity/i)).toBeVisible();
		await expect(drawerBody.getByText(/4\.\s*Disclosure/i)).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg05-drawer-id")).toHaveText(/INV-001/i);
		await expect(drawerBody.locator("label", { hasText: /^Item(\s|\*)/ })).toBeVisible();

		await fillCompleteItem(page);
		await page.getByTestId("kt-cl-cfg05-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg05-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Inventory & Background saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg05-continue")).toBeEnabled({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg05-save")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-cfg05-blockers")).toHaveClass(/hidden/);
		await expect(page.getByTestId("kt-cl-cfg05-table")).toContainText(/Existing Server Room/i);
		await expect(page.getByTestId("kt-cl-cfg05-table")).toContainText(/INV-001/);
		await expect(page.getByTestId("kt-cl-cfg05-table")).toContainText(/Safe to disclose/i);
		await expect(page.getByTestId("kt-cl-cfg05-table")).toContainText(/Complete/i);
	});

	test("Drawer Save refreshes issues without footer Save", async ({ page }) => {
		await openInventory(page);
		await page.getByTestId("kt-cl-cfg05-add").click();
		await page.getByTestId("kt-cl-cfg05-drawer-title-input").fill("Incomplete Site Context");
		await page
			.getByTestId("kt-cl-cfg05-drawer-description")
			.fill("Head office user groups need sizing context.");
		await page.getByTestId("kt-cl-cfg05-drawer-category").selectOption("Sites & Users");
		await page.getByTestId("kt-cl-cfg05-drawer-scope").selectOption("In scope");
		await page
			.getByTestId("kt-cl-cfg05-drawer-consideration")
			.fill("Bidder should size the solution for head office users.");
		// Leave disclosure as Not configured / empty if possible — select Needs review without note
		await page
			.getByTestId("kt-cl-cfg05-drawer-disclosure")
			.selectOption("Needs disclosure review");
		await page.getByTestId("kt-cl-cfg05-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg05-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Inventory & Background saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg05-blockers")).not.toHaveClass(/hidden/, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg05-continue")).toBeDisabled();

		await page.getByTestId("kt-cl-cfg05-table").getByRole("button", { name: /^Fix$/i }).click();
		await expect(page.getByTestId("kt-cl-cfg05-drawer")).toBeVisible();
		await page
			.getByTestId("kt-cl-cfg05-drawer-disclosure-note")
			.fill("Confirm no private network details are included before disclosure.");
		await page.getByTestId("kt-cl-cfg05-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg05-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Inventory & Background saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg05-blockers")).toHaveClass(/hidden/, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg05-continue")).toBeEnabled({ timeout: 15_000 });
	});

	test("Add Background Note uses BG id prefix", async ({ page }) => {
		await openInventory(page);
		await page.getByTestId("kt-cl-cfg05-add-background").click();
		await expect(page.getByTestId("kt-cl-cfg05-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg05-drawer-id")).toHaveText(/BG-\d+/i);
		await expect(page.getByTestId("kt-cl-cfg05-drawer-category")).toHaveValue(
			"Background Notes"
		);
		await page.getByTestId("kt-cl-cfg05-drawer-close").click();
	});

	test("subtle delete removes inventory row after confirm", async ({ page }) => {
		await openInventory(page);
		await page.getByTestId("kt-cl-cfg05-add").click();
		await fillCompleteItem(page);
		await page.getByTestId("kt-cl-cfg05-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg05-table")).toContainText(/INV-001/);
		await expect(page.getByTestId("kt-cl-cfg05-row-delete-INV-001")).toBeVisible();
		await page.getByTestId("kt-cl-cfg05-row-delete-INV-001").click();
		await expect(page.getByTestId("kt-cl-confirm-dialog")).toBeVisible({ timeout: 10_000 });
		await expect(page.getByTestId("kt-cl-confirm-ok")).toHaveText(/Remove/i);
		await expect(page.getByTestId("kt-cl-confirm-cancel")).toHaveText(/Cancel/i);
		await page.getByTestId("kt-cl-confirm-ok").click();
		await expect(page.getByText(/Inventory item removed/i)).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg05-table")).not.toContainText(/INV-001/);
		await expect(page.getByTestId("kt-cl-confirm-dialog")).toHaveCount(0);
	});

	test("CFG-04 Continue lands on live System Inventory page", async ({ page }) => {
		await page.goto(
			`/desk/${CFG04_SLUG}/${encodeURIComponent(CONFIG)}`
		);
		await expect(page.getByTestId("kt-cl-cfg04-root")).toBeVisible({ timeout: 30_000 });
		const continueBtn = page.getByTestId("kt-cl-cfg04-continue");
		if (await continueBtn.isDisabled()) {
			await page.getByTestId("kt-cl-cfg04-add").click();
			await page
				.getByTestId("kt-cl-cfg04-drawer-name")
				.fill("Project Kick-off and Detailed Work Plan");
			await page
				.getByTestId("kt-cl-cfg04-drawer-description")
				.fill("Mobilise the delivery team and agree the detailed work plan.");
			await page.getByTestId("kt-cl-cfg04-drawer-sequence").fill("1");
			await page.getByTestId("kt-cl-cfg04-drawer-duration").fill("2");
			await page.getByTestId("kt-cl-cfg04-drawer-duration-unit").selectOption("weeks");
			await page
				.getByTestId("kt-cl-cfg04-drawer-trigger")
				.selectOption("Contract signing and notice to proceed");
			await page
				.getByTestId("kt-cl-cfg04-drawer-deliverable")
				.fill("Approved implementation work plan");
			await page
				.getByTestId("kt-cl-cfg04-drawer-deliverable-description")
				.fill("Detailed work plan covering mobilisation and baseline schedule.");
			await page
				.getByTestId("kt-cl-cfg04-drawer-acceptance")
				.selectOption("PE confirms approved work plan");
			await page.getByTestId("kt-cl-cfg04-drawer-save").click();
			await expect(page.getByTestId("kt-cl-cfg04-continue")).toBeEnabled({ timeout: 15_000 });
		}
		await page.getByTestId("kt-cl-cfg04-continue").click();
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 20_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
	});
});
