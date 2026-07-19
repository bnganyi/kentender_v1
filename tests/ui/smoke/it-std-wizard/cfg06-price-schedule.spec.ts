import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * CFG-06 Price Schedule (C2-CFG6 + column-clarity).
 * Route: /desk/it-tender-configuration-price-schedule/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-price-schedule";
const CFG06 = `/desk/${PAGE_SLUG}`;
const ROOT = '[data-testid="kt-cl-cfg06-root"]';
const CONFIG = "TCFG-SEED-TCFG-IP";
const CFG05_SLUG = "it-tender-configuration-system-inventory";

const FORBIDDEN = [
	/\bbid ranking\b/i,
	/\baward recommendation\b/i,
	/\bpayment certificate\b/i,
	/\bbudget approval\b/i,
	/\bschema version\b/i,
	/\brule ID\b/i,
	/\bpass mark\b/i,
];

const COLUMNS = [
	"ID",
	"Price Item",
	"Price Group",
	"Pricing Basis",
	"Quantity / Duration",
	"Source",
	"Evaluated Price",
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
		throw new Error("CFG-06 seed failed: " + JSON.stringify(result));
	}
}

async function openPriceSchedule(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`${CFG06}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

async function fillCompleteItem(page: import("@playwright/test").Page) {
	await page.getByTestId("kt-cl-cfg06-drawer-name").fill("Server compute nodes");
	await page
		.getByTestId("kt-cl-cfg06-drawer-description")
		.fill("Provide unit prices for server compute nodes including delivery to site.");
	await page.getByTestId("kt-cl-cfg06-drawer-group").selectOption("Supply & Installation");
	await page.getByTestId("kt-cl-cfg06-drawer-source").selectOption("User added");
	await page.getByTestId("kt-cl-cfg06-drawer-basis").selectOption("Unit price");
	await page.getByTestId("kt-cl-cfg06-drawer-quantity").fill("12");
	await page.getByTestId("kt-cl-cfg06-drawer-unit").fill("units");
	await page.getByTestId("kt-cl-cfg06-drawer-evaluated").selectOption("Included");
	await page
		.getByTestId("kt-cl-cfg06-drawer-instruction")
		.fill("Enter a firm unit price for each server compute node as specified.");
}

test.describe.configure({ mode: "serial" });

test.describe("CFG-06 Price Schedule", () => {
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

	test("layout: strip, tabs, columns, footer, no forbidden terms", async ({ page }) => {
		await openPriceSchedule(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-cfg06-tabs")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-tab-all")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-tab-supply")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-tab-recurrent")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-tab-optional")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-tab-needs")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-table")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-add")).toHaveText(/Add Price Item/i);
		await expect(page.getByTestId("kt-cl-cfg06-import")).toHaveText(/Import Price Items/i);
		// Tabs/actions row needs top padding so Add/Import are not flush under the issues banner.
		await expect
			.poll(async () => {
				return page.locator(".kt-cl-cfg06-tabs-row").evaluate((el) => {
					return parseFloat(getComputedStyle(el).paddingTop) >= 10;
				});
			})
			.toBe(true);
		await expect(page.getByTestId("kt-cl-cfg06-tabs-actions").getByTestId("kt-cl-cfg06-run-check")).toHaveCount(
			0
		);
		await expect(page.getByTestId("kt-cl-cfg06-footer").getByTestId("kt-cl-cfg06-run-check")).toHaveText(
			/Run Check/i
		);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Price Schedule/i);
		await expect(page.getByTestId("kt-cl-cfg06-back")).toHaveText(/Back to Configuration Home/i);
		await expect(page.getByTestId("kt-cl-cfg06-save")).toHaveText(/Save Price Schedule/i);
		await expect(page.getByTestId("kt-cl-cfg06-continue")).toHaveText(
			/Continue to Evaluation Setup/i
		);
		await expect(page.getByTestId("kt-cl-cfg06-continue")).toBeDisabled();

		const tableText = (await page.getByTestId("kt-cl-cfg06-table").innerText()).toLowerCase();
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

	test("Add Price Item drawer persists and enables Continue", async ({ page }) => {
		await openPriceSchedule(page);
		await page.getByTestId("kt-cl-cfg06-add").click();
		await expect(page.getByTestId("kt-cl-cfg06-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-drawer-title")).toContainText(/Add Price Item/i);
		const drawerBody = page.getByTestId("kt-cl-cfg06-drawer-body");
		await expect(drawerBody.getByText(/1\.\s*Price Item/i)).toBeVisible();
		await expect(drawerBody.getByText(/3\.\s*Evaluated Price/i)).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-drawer-id")).toHaveText(/PRI-001/i);

		await fillCompleteItem(page);
		await page.getByTestId("kt-cl-cfg06-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg06-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Price item saved/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg06-continue")).toBeEnabled({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg06-save")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-cfg06-blockers")).toHaveClass(/hidden/);
		await expect(page.getByTestId("kt-cl-cfg06-table")).toContainText(/Server compute nodes/i);
		await expect(page.getByTestId("kt-cl-cfg06-table")).toContainText(/PRI-001/);
		await expect(page.getByTestId("kt-cl-cfg06-table")).toContainText(/Included/i);
		await expect(page.getByTestId("kt-cl-cfg06-table")).toContainText(/Complete/i);
	});

	test("Drawer Save refreshes issues without footer Save", async ({ page }) => {
		await openPriceSchedule(page);
		await page.getByTestId("kt-cl-cfg06-add").click();
		await page.getByTestId("kt-cl-cfg06-drawer-name").fill("Cloud backup subscription");
		await page
			.getByTestId("kt-cl-cfg06-drawer-description")
			.fill("Recurring cloud backup service for protected workloads.");
		await page.getByTestId("kt-cl-cfg06-drawer-group").selectOption("Recurrent Cost");
		await page.getByTestId("kt-cl-cfg06-drawer-source").selectOption("User added");
		await page.getByTestId("kt-cl-cfg06-drawer-basis").selectOption("Monthly");
		await page.getByTestId("kt-cl-cfg06-drawer-quantity").fill("36");
		await page.getByTestId("kt-cl-cfg06-drawer-unit").fill("months");
		// Missing conditional rule only (quantity + unit cover duration)
		await page.getByTestId("kt-cl-cfg06-drawer-evaluated").selectOption("Conditional");
		await page
			.getByTestId("kt-cl-cfg06-drawer-instruction")
			.fill("Price monthly backup subscription for the stated term.");
		await page.getByTestId("kt-cl-cfg06-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg06-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Price item saved/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg06-blockers")).not.toHaveClass(/hidden/, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg06-continue")).toBeDisabled();

		await page.getByTestId("kt-cl-cfg06-table").getByRole("button", { name: /^Fix$/i }).click();
		await expect(page.getByTestId("kt-cl-cfg06-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg06-drawer-duration")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-cfg06-drawer-tax")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-cfg06-drawer-body")).toContainText(
			/Quantity \/ Duration/i
		);
		await page
			.getByTestId("kt-cl-cfg06-drawer-conditional")
			.fill("Included only if the PE exercises the optional backup lot.");
		await page.getByTestId("kt-cl-cfg06-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg06-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Price item saved/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg06-blockers")).toHaveClass(/hidden/, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg06-continue")).toBeEnabled({ timeout: 15_000 });
	});

	test("Import Price Items creates draft rows from upstream", async ({ page }) => {
		// Seed upstream CFG-03/04/05 then import
		await page.goto("/desk", { waitUntil: "domcontentloaded" });
		await page.waitForFunction(() => typeof (window as unknown as { frappe?: unknown }).frappe !== "undefined");
		await page.evaluate(async () => {
			// @ts-expect-error frappe on desk
			await frappe.call({
				method: "kentender_procurement.tender_configurations.save_tender_configuration_requirements",
				args: {
					configuration_id: "TCFG-SEED-TCFG-IP",
					payload: {
						requirements: [
							{
								title: "Data migration support requirement",
								description:
									"Migrate existing finance records into the new system with validation reports.",
								category_label: "Technical Requirement",
								treatment_label: "Mandatory",
								bidder_response_format: "Yes/No confirmation",
								bidder_response_instruction:
									"Bidder must confirm the migration approach and validation method.",
								evidence_requirement: "Evidence required",
								evidence_instruction: "Migration validation report",
								delivery_confirmation_method: "Commissioning test report",
							},
						],
					},
				},
			});
		});

		await openPriceSchedule(page);
		await page.getByTestId("kt-cl-cfg06-import").click();
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Price items imported/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg06-table")).toContainText(/PRI-/);
		await expect(page.getByTestId("kt-cl-cfg06-table")).toContainText(/IT Requirements|Data migration/i);
	});

	test("subtle delete removes price item row after confirm", async ({ page }) => {
		await openPriceSchedule(page);
		await page.getByTestId("kt-cl-cfg06-add").click();
		await fillCompleteItem(page);
		await page.getByTestId("kt-cl-cfg06-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg06-table")).toContainText(/PRI-001/);
		await expect(page.getByTestId("kt-cl-cfg06-row-delete-PRI-001")).toBeVisible();
		// Action column: delete control is flush-right with the Edit/Fix group.
		await expect
			.poll(async () => {
				return page.locator(".kt-cl-cfg06-row-actions").first().evaluate((el) => {
					const cs = getComputedStyle(el);
					return cs.justifyContent === "flex-end" && cs.display.includes("flex");
				});
			})
			.toBe(true);
		await page.getByTestId("kt-cl-cfg06-row-delete-PRI-001").click();
		await expect(page.getByTestId("kt-cl-confirm-dialog")).toBeVisible({ timeout: 10_000 });
		await expect(page.getByTestId("kt-cl-confirm-ok")).toHaveText(/Remove/i);
		await expect(page.getByTestId("kt-cl-confirm-cancel")).toHaveText(/Cancel/i);
		await page.getByTestId("kt-cl-confirm-ok").click();
		await expect(page.getByText(/Price item removed/i)).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg06-table")).not.toContainText(/PRI-001/);
		await expect(page.getByTestId("kt-cl-cfg06-continue")).toBeDisabled();
	});

	test("CFG-05 Continue lands on live Price Schedule page", async ({ page }) => {
		await page.goto(`/desk/${CFG05_SLUG}/${encodeURIComponent(CONFIG)}`);
		await expect(page.getByTestId("kt-cl-cfg05-root")).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(
			/System Inventory & Bidder Background/i
		);
		const continueBtn = page.getByTestId("kt-cl-cfg05-continue");
		if (await continueBtn.isDisabled()) {
			await page.getByTestId("kt-cl-cfg05-add").click();
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
			await page.getByTestId("kt-cl-cfg05-drawer-save").click();
			await expect(page.getByTestId("kt-cl-cfg05-continue")).toBeEnabled({ timeout: 15_000 });
		}
		await page.getByTestId("kt-cl-cfg05-continue").click();
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 20_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-breadcrumb-current")).toHaveText(/Price Schedule/i);
	});
});
