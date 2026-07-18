import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * CFG-03 IT Requirements (C2-CFG3).
 * Route: /desk/it-tender-configuration-it-requirements/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-it-requirements";
const CFG03 = `/desk/${PAGE_SLUG}`;
const ROOT = '[data-testid="kt-cl-cfg03-root"]';
const CONFIG = "TCFG-SEED-TCFG-IP";

const FORBIDDEN = [
	/\bEvaluation Matrix\b/i,
	/\bScoring Requirements\b/i,
	/\bCompliance Results\b/i,
	/\bSupplier Responses\b/i,
	/\bContract Obligations Editor\b/i,
	/\bschema version\b/i,
	/\bclause ID\b/i,
	/\bhash\b/i,
	/\bpass mark\b/i,
];

const COLUMNS = [
	"ID",
	"Requirement",
	"Category",
	"Treatment",
	"Bidder Response Instruction",
	"Evidence Instruction",
	"Delivery Confirmation Method",
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
		throw new Error("CFG-03 seed failed: " + JSON.stringify(result));
	}
}

async function openRequirements(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`${CFG03}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

async function fillCompleteRequirement(page: import("@playwright/test").Page) {
	await page.getByTestId("kt-cl-cfg03-drawer-title-input").fill("Compute Node Performance");
	await page.getByTestId("kt-cl-cfg03-drawer-description").fill(
		"Bidder must propose compute nodes that meet the stated processor, memory, storage, and redundancy requirements."
	);
	await page.getByTestId("kt-cl-cfg03-drawer-category").selectOption("Technical Requirement");
	await page.getByTestId("kt-cl-cfg03-drawer-treatment").selectOption("Mandatory");
	await page.getByTestId("kt-cl-cfg03-drawer-response-format").selectOption("Yes/No confirmation");
	await page
		.getByTestId("kt-cl-cfg03-drawer-response-instruction")
		.fill("Confirm compliance with the stated compute specification.");
	await page.getByTestId("kt-cl-cfg03-drawer-evidence-requirement").selectOption("Evidence required");
	await page
		.getByTestId("kt-cl-cfg03-drawer-evidence-instruction")
		.fill("Manufacturer datasheet required");
	await page
		.getByTestId("kt-cl-cfg03-drawer-delivery-method")
		.fill("Commissioning test report");
}

test.describe.configure({ mode: "serial" });

test.describe("CFG-03 IT Requirements", () => {
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

	test("layout: strip, table columns, guidance, footer, no forbidden terms", async ({ page }) => {
		await openRequirements(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-cfg03-layout")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg03-table")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg03-guidance")).toContainText(/IT Requirements Guidance/i);
		await expect(page.getByTestId("kt-cl-cfg03-add")).toHaveText(/Add Requirement/i);
		await expect(page.getByTestId("kt-cl-cfg03-back")).toHaveText(/Back to Configuration Home/i);
		await expect(page.getByTestId("kt-cl-cfg03-save")).toHaveText(/Save Requirements/i);
		await expect(page.getByTestId("kt-cl-cfg03-run-check")).toHaveText(/Run Check/i);
		await expect(page.getByTestId("kt-cl-cfg03-continue")).toHaveText(
			/Continue to Implementation Schedule/i
		);
		await expect(page.getByTestId("kt-cl-cfg03-continue")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-cfg03-blockers")).toHaveClass(/hidden/);

		const tableText = (await page.getByTestId("kt-cl-cfg03-table").innerText()).toLowerCase();
		for (const col of COLUMNS) {
			expect(tableText, col).toContain(col.toLowerCase());
		}

		const body = await page.locator(ROOT).innerText();
		for (const re of FORBIDDEN) {
			expect(body, String(re)).not.toMatch(re);
		}
	});

	test("Add Requirement opens drawer; Save Requirement persists and enables Continue", async ({
		page,
	}) => {
		await openRequirements(page);
		await page.getByTestId("kt-cl-cfg03-add").click();
		await expect(page.getByTestId("kt-cl-cfg03-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg03-drawer-title")).toContainText(/Add Requirement/i);
		await expect(page.getByTestId("kt-cl-cfg03-drawer-references")).toBeVisible();

		// Drawer labels must match table columns for ID / Requirement
		const drawerBody = page.getByTestId("kt-cl-cfg03-drawer-body");
		await expect(drawerBody.locator("label", { hasText: /^ID$/ })).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg03-drawer-id")).toContainText(/Assigned on save/i);
		await expect(drawerBody.locator("label", { hasText: /^Requirement/ })).toBeVisible();
		await expect(drawerBody).not.toContainText(/Requirement Title/i);

		await fillCompleteRequirement(page);
		await page.getByTestId("kt-cl-cfg03-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg03-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/IT Requirements saved successfully/i,
			{ timeout: 15_000 }
		);
		// Drawer save must persist + revalidate — no second footer Save required
		await expect(page.getByTestId("kt-cl-cfg03-continue")).toBeEnabled({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg03-save")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-cfg03-blockers")).toHaveClass(/hidden/);
		await expect(page.getByTestId("kt-cl-cfg03-table")).toContainText(/Compute Node Performance/i);
		await expect(page.getByTestId("kt-cl-cfg03-table")).toContainText(/REQ-001/);
		await expect(page.getByTestId("kt-cl-cfg03-table")).toContainText(/Commissioning test report/i);
		await expect(page.getByTestId("kt-cl-cfg03-table")).toContainText(/Complete/i);
		const tableText = (await page.getByTestId("kt-cl-cfg03-table").innerText()).toLowerCase();
		expect(tableText).toContain("setup status");
		expect(tableText).toContain("delivery confirmation method");
		expect(tableText).not.toContain("acceptance defined");
		expect(tableText).not.toContain("missing acceptance");

		// Edit drawer shows the same ID / Requirement labels as the table
		await page.getByTestId("kt-cl-cfg03-table").getByRole("button", { name: /^Edit$/i }).click();
		await expect(page.getByTestId("kt-cl-cfg03-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg03-drawer-id")).toHaveText(/REQ-001/i);
		await expect(page.getByTestId("kt-cl-cfg03-drawer-title-input")).toHaveValue(
			/Compute Node Performance/i
		);
		await page.getByTestId("kt-cl-cfg03-drawer-close").click();
	});

	test("Drawer Save Requirement refreshes issues without footer Save", async ({ page }) => {
		await openRequirements(page);

		// Incomplete row → persist via drawer → issues panel visible
		await page.getByTestId("kt-cl-cfg03-add").click();
		await page.getByTestId("kt-cl-cfg03-drawer-title-input").fill("Incomplete Storage Spec");
		await page.getByTestId("kt-cl-cfg03-drawer-category").selectOption("Technical Requirement");
		await page.getByTestId("kt-cl-cfg03-drawer-treatment").selectOption("Mandatory");
		await page.getByTestId("kt-cl-cfg03-drawer-response-format").selectOption("Narrative response");
		await page
			.getByTestId("kt-cl-cfg03-drawer-response-instruction")
			.fill("Describe the proposed storage architecture.");
		await page.getByTestId("kt-cl-cfg03-drawer-evidence-requirement").selectOption("Evidence required");
		await page
			.getByTestId("kt-cl-cfg03-drawer-evidence-instruction")
			.fill("Architecture diagram required");
		// Intentionally omit delivery confirmation method
		await page.getByTestId("kt-cl-cfg03-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg03-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/IT Requirements saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg03-blockers")).not.toHaveClass(/hidden/, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg03-continue")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-cfg03-table")).toContainText(/Needs attention|Incomplete Storage/i);

		// Fix in drawer → issues refresh/hide without footer Save
		await page.getByTestId("kt-cl-cfg03-table").getByRole("button", { name: /^Fix$/i }).click();
		await expect(page.getByTestId("kt-cl-cfg03-drawer")).toBeVisible();
		await page.getByTestId("kt-cl-cfg03-drawer-delivery-method").fill("Inspection at delivery");
		await page.getByTestId("kt-cl-cfg03-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg03-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/IT Requirements saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg03-blockers")).toHaveClass(/hidden/, { timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg03-continue")).toBeEnabled({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg03-table")).toContainText(/Inspection at delivery/i);
		await expect(page.getByTestId("kt-cl-cfg03-table")).toContainText(/Complete/i);
	});

	test("Run Check refreshes issues; refresh keeps configuration id", async ({ page }) => {
		await openRequirements(page);
		await page.getByTestId("kt-cl-cfg03-run-check").click();
		await expect(page.locator(".desk-alert .alert-message")).toContainText(/Check complete/i, {
			timeout: 15_000,
		});

		await page.reload({ waitUntil: "domcontentloaded" });
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 15_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	});

	test("CFG-02 Continue lands on live IT Requirements page", async ({ page }) => {
		// Ensure TDS can continue first
		await page.goto(`/desk/it-tender-configuration-tds/${encodeURIComponent(CONFIG)}`);
		await expect(page.getByTestId("kt-cl-cfg02-root")).toBeVisible({ timeout: 30_000 });
		const continueBtn = page.getByTestId("kt-cl-cfg02-continue");
		if (await continueBtn.isDisabled()) {
			// Minimal complete TDS fill if prior suite state incomplete
			await page.getByTestId("kt-cl-cfg02-contact_officer").fill("Jane Doe");
			await page.getByTestId("kt-cl-cfg02-contact_email").fill("procurement@example.go.ke");
			await page
				.getByTestId("kt-cl-cfg02-clarification_submission_method")
				.selectOption("E-Procurement Portal");
			await page.getByTestId("kt-cl-cfg02-clarification_deadline").fill("2026-08-01T12:00");
			await page.locator('input[name="kt-cl-cfg02-pre_tender_meeting"][value="No"]').check();
			await page.getByTestId("kt-cl-cfg02-tender_submission_deadline").fill("2026-08-15T17:00");
			await page.getByTestId("kt-cl-cfg02-tender_opening_datetime").fill("2026-08-15T17:30");
			await page.getByTestId("kt-cl-cfg02-bid_validity_period").fill("120");
			await page.getByTestId("kt-cl-cfg02-submission_channel").selectOption("E-Procurement Portal");
			await page.getByTestId("kt-cl-cfg02-submission_language").selectOption("English");
			await page.getByTestId("kt-cl-cfg02-tender_currency").selectOption("KES");
			await page.locator('input[name="kt-cl-cfg02-alternative_tenders_allowed"][value="No"]').check();
			await page.locator('input[name="kt-cl-cfg02-joint_ventures_allowed"][value="Yes"]').check();
			await page
				.getByTestId("kt-cl-cfg02-eligible_tenderers")
				.selectOption("Open to all eligible tenderers");
			await page.locator('input[name="kt-cl-cfg02-reserved_procurement"][value="No"]').check();
			await page.locator('input[name="kt-cl-cfg02-tender_security_required"][value="No"]').check();
			await page.locator('input[name="kt-cl-cfg02-margin_of_preference_applies"][value="No"]').check();
			await page.getByTestId("kt-cl-cfg02-opening_method").selectOption("Electronic Opening");
			await page.getByTestId("kt-cl-cfg02-opening_location").fill("KenTender portal");
			await page.locator('input[name="kt-cl-cfg02-opening_attendance_allowed"][value="Yes"]').check();
			await page.getByTestId("kt-cl-cfg02-save").click();
			await expect(page.getByTestId("kt-cl-cfg02-continue")).toBeEnabled({ timeout: 15_000 });
		}
		await page.getByTestId("kt-cl-cfg02-continue").click();
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 20_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
	});
});
