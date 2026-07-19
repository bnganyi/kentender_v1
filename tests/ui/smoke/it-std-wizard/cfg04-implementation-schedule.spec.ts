import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { expectConfigurationContextStrip } from "../../helpers/ktClConfigContext";

/**
 * CFG-04 Implementation Schedule (C2-CFG4 + column-clarity).
 * Route: /desk/it-tender-configuration-implementation-schedule/<configuration_id>
 */

const PAGE_SLUG = "it-tender-configuration-implementation-schedule";
const CFG04 = `/desk/${PAGE_SLUG}`;
const ROOT = '[data-testid="kt-cl-cfg04-root"]';
const CONFIG = "TCFG-SEED-TCFG-IP";

const FORBIDDEN = [
	/\bProject Execution\b/i,
	/\bPayment Milestones\b/i,
	/\bContract Administration\b/i,
	/\bInspection Records\b/i,
	/\bWork Progress\b/i,
	/\bschema version\b/i,
	/\bclause ID\b/i,
	/\bpass mark\b/i,
];

const COLUMNS = [
	"ID",
	"Milestone",
	"Expected Duration",
	"Trigger",
	"Key Deliverable",
	"Acceptance Method",
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
		throw new Error("CFG-04 seed failed: " + JSON.stringify(result));
	}
}

async function openSchedule(page: import("@playwright/test").Page, configId = CONFIG) {
	await page.goto(`${CFG04}/${encodeURIComponent(configId)}`);
	await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
	await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${configId}`), { timeout: 15_000 });
	await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
}

async function fillCompleteMilestone(page: import("@playwright/test").Page) {
	await page.getByTestId("kt-cl-cfg04-drawer-name").fill("Project Kick-off and Detailed Work Plan");
	await page
		.getByTestId("kt-cl-cfg04-drawer-description")
		.fill("Mobilise the delivery team and agree the detailed work plan.");
	await page.getByTestId("kt-cl-cfg04-drawer-sequence").fill("1");
	await page.getByTestId("kt-cl-cfg04-drawer-duration").fill("2");
	await page.getByTestId("kt-cl-cfg04-drawer-duration-unit").selectOption("weeks");
	await page
		.getByTestId("kt-cl-cfg04-drawer-trigger")
		.fill("Contract signing and notice to proceed");
	await page
		.getByTestId("kt-cl-cfg04-drawer-deliverable")
		.fill("Approved implementation work plan");
	await page
		.getByTestId("kt-cl-cfg04-drawer-deliverable-description")
		.fill("Detailed work plan covering mobilisation and baseline schedule.");
	await page
		.getByTestId("kt-cl-cfg04-drawer-acceptance")
		.fill("PE confirms approved work plan");
	await page.getByTestId("kt-cl-cfg04-drawer-evidence").fill("Signed work plan approval");
}

test.describe.configure({ mode: "serial" });

test.describe("CFG-04 Implementation Schedule", () => {
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

	test("layout: strip, approach, columns, guidance, footer, no forbidden terms", async ({
		page,
	}) => {
		await openSchedule(page);
		await expectConfigurationContextStrip(page, {
			family: /Information Technology/i,
			stdDocument: /IT Standard Tender Document/i,
		});
		await expect(page.getByTestId("kt-cl-cfg04-approach")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg04-approach-phased")).toBeChecked();
		await expect(page.getByTestId("kt-cl-cfg04-layout")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg04-table")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg04-guidance")).toContainText(
			/Implementation Schedule Guidance/i
		);
		await expect(page.getByTestId("kt-cl-cfg04-add")).toHaveText(/Add Milestone/i);
		await expect(page.getByTestId("kt-cl-cfg04-back")).toHaveText(/Back to Configuration Home/i);
		await expect(page.getByTestId("kt-cl-cfg04-save")).toHaveText(/Save Schedule/i);
		await expect(page.getByTestId("kt-cl-cfg04-run-check")).toHaveText(/Run Check/i);
		await expect(page.getByTestId("kt-cl-cfg04-continue")).toHaveText(
			/Continue to System Inventory/i
		);
		await expect(page.getByTestId("kt-cl-cfg04-continue")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-cfg04-blockers")).toHaveClass(/hidden/);

		const tableText = (await page.getByTestId("kt-cl-cfg04-table").innerText()).toLowerCase();
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

	test("Add Milestone drawer persists and enables Continue", async ({ page }) => {
		await openSchedule(page);
		await page.getByTestId("kt-cl-cfg04-add").click();
		await expect(page.getByTestId("kt-cl-cfg04-drawer")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg04-drawer-title")).toContainText(/Add Milestone/i);
		const drawerBody = page.getByTestId("kt-cl-cfg04-drawer-body");
		await expect(drawerBody.getByText(/1\.\s*Milestone Core Identity/i)).toBeVisible();
		await expect(drawerBody.getByText(/2\.\s*Deliverables/i)).toBeVisible();
		await expect(drawerBody.getByText(/3\.\s*Formal Acceptance/i)).toBeVisible();
		await expect(drawerBody.locator("label", { hasText: /^ID$/ })).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg04-drawer-id")).toHaveText(/MS-001/i);
		await expect(drawerBody.locator("label", { hasText: /^Milestone Name/ })).toBeVisible();
		await expect(drawerBody.locator("label", { hasText: /^Acceptance Method/ })).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg04-drawer-duration-unit")).toBeVisible();
		await expect(page.getByTestId("kt-cl-cfg04-drawer-related-pick")).toBeVisible();

		await fillCompleteMilestone(page);
		await page.getByTestId("kt-cl-cfg04-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg04-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Implementation Schedule saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg04-continue")).toBeEnabled({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg04-save")).toBeDisabled();
		await expect(page.getByTestId("kt-cl-cfg04-blockers")).toHaveClass(/hidden/);
		await expect(page.getByTestId("kt-cl-cfg04-table")).toContainText(
			/Project Kick-off and Detailed Work Plan/i
		);
		await expect(page.getByTestId("kt-cl-cfg04-table")).toContainText(/MS-001/);
		await expect(page.getByTestId("kt-cl-cfg04-table")).toContainText(
			/PE confirms approved work plan/i
		);
		await expect(page.getByTestId("kt-cl-cfg04-table")).toContainText(/Complete/i);
	});

	test("Drawer Save Milestone refreshes issues without footer Save", async ({ page }) => {
		await openSchedule(page);
		await page.getByTestId("kt-cl-cfg04-add").click();
		await page.getByTestId("kt-cl-cfg04-drawer-name").fill("Incomplete Install Milestone");
		await page.getByTestId("kt-cl-cfg04-drawer-description").fill("Install infrastructure.");
		await page.getByTestId("kt-cl-cfg04-drawer-duration").fill("4");
		await page.getByTestId("kt-cl-cfg04-drawer-duration-unit").selectOption("weeks");
		await page.getByTestId("kt-cl-cfg04-drawer-trigger").fill("Delivery acceptance");
		await page.getByTestId("kt-cl-cfg04-drawer-deliverable").fill("Installed infrastructure");
		await page
			.getByTestId("kt-cl-cfg04-drawer-deliverable-description")
			.fill("Installed and configured infrastructure.");
		// Omit acceptance method
		await page.getByTestId("kt-cl-cfg04-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg04-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Implementation Schedule saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg04-blockers")).not.toHaveClass(/hidden/, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg04-continue")).toBeDisabled();

		await page.getByTestId("kt-cl-cfg04-table").getByRole("button", { name: /^Fix$/i }).click();
		await expect(page.getByTestId("kt-cl-cfg04-drawer")).toBeVisible();
		await page.getByTestId("kt-cl-cfg04-drawer-acceptance").fill("Inspection at delivery");
		await page.getByTestId("kt-cl-cfg04-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg04-drawer")).toHaveCount(0);
		await expect(page.locator(".desk-alert .alert-message")).toContainText(
			/Implementation Schedule saved successfully/i,
			{ timeout: 15_000 }
		);
		await expect(page.getByTestId("kt-cl-cfg04-blockers")).toHaveClass(/hidden/, {
			timeout: 15_000,
		});
		await expect(page.getByTestId("kt-cl-cfg04-continue")).toBeEnabled({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg04-table")).toContainText(/Inspection at delivery/i);
	});

	test("Single Turnkey form hides table and can continue", async ({ page }) => {
		await openSchedule(page);
		await page.getByTestId("kt-cl-cfg04-approach-single").check();
		// Confirm appears when phased milestones exist — accept if present
		const yesBtn = page.locator(".modal .btn-primary").filter({ hasText: /^Yes$/i });
		try {
			await yesBtn.first().click({ timeout: 4_000 });
		} catch {
			/* no confirm when there are no phased milestones */
		}
		await expect(page.getByTestId("kt-cl-cfg04-single-form")).toBeVisible({ timeout: 20_000 });
		await expect(page.getByTestId("kt-cl-cfg04-table")).toHaveCount(0);
		await expect(page.getByTestId("kt-cl-cfg04-approach-single")).toBeChecked();

		await page.getByTestId("kt-cl-cfg04-single-duration").fill("6");
		await page.getByTestId("kt-cl-cfg04-single-duration-unit").selectOption("months");
		await page
			.getByTestId("kt-cl-cfg04-single-trigger")
			.fill("Contract signing and notice to proceed");
		await page
			.getByTestId("kt-cl-cfg04-single-deliverables")
			.fill(
				"Fully supplied, installed, configured, tested, documented, and handed-over IT solution"
			);
		await page
			.getByTestId("kt-cl-cfg04-single-acceptance")
			.fill(
				"Procuring Entity confirms delivery, installation, testing, training, documentation, and operational readiness."
			);
		await page
			.getByTestId("kt-cl-cfg04-single-evidence")
			.fill("Completion report, test results, training records, and handover certificate.");
		await expect(page.getByTestId("kt-cl-cfg04-save")).toBeEnabled({ timeout: 5_000 });
		await page.getByTestId("kt-cl-cfg04-save").click();
		await expect(page.getByTestId("kt-cl-cfg04-save")).toBeDisabled({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg04-continue")).toBeEnabled({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg04-single-duration")).toHaveValue("6");
		await expect(page.getByTestId("kt-cl-cfg04-single-duration-unit")).toHaveValue("months");
	});

	test("subtle delete removes milestone row after confirm", async ({ page }) => {
		await openSchedule(page);
		await page.getByTestId("kt-cl-cfg04-add").click();
		await fillCompleteMilestone(page);
		await page.getByTestId("kt-cl-cfg04-drawer-save").click();
		await expect(page.getByTestId("kt-cl-cfg04-table")).toContainText(/MS-001/);
		await expect(page.getByTestId("kt-cl-cfg04-row-delete-MS-001")).toBeVisible();
		await page.getByTestId("kt-cl-cfg04-row-delete-MS-001").click();
		await expect(page.getByTestId("kt-cl-confirm-dialog")).toBeVisible({ timeout: 10_000 });
		await expect(page.getByTestId("kt-cl-confirm-ok")).toHaveText(/Remove/i);
		await expect(page.getByTestId("kt-cl-confirm-cancel")).toHaveText(/Cancel/i);
		await page.getByTestId("kt-cl-confirm-ok").click();
		await expect(page.getByText(/Milestone removed/i)).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId("kt-cl-cfg04-table")).not.toContainText(/MS-001/);
		await expect(page.getByTestId("kt-cl-cfg04-continue")).toBeDisabled();
	});

	test("CFG-03 Continue lands on live Implementation Schedule page", async ({ page }) => {
		await page.goto(
			`/desk/it-tender-configuration-it-requirements/${encodeURIComponent(CONFIG)}`
		);
		await expect(page.getByTestId("kt-cl-cfg03-root")).toBeVisible({ timeout: 30_000 });
		const continueBtn = page.getByTestId("kt-cl-cfg03-continue");
		if (await continueBtn.isDisabled()) {
			// Ensure CFG-03 can continue if prior suite left incomplete state
			await page.getByTestId("kt-cl-cfg03-add").click();
			await page.getByTestId("kt-cl-cfg03-drawer-title-input").fill("Compute Node Performance");
			await page.getByTestId("kt-cl-cfg03-drawer-category").selectOption("Technical Requirement");
			await page.getByTestId("kt-cl-cfg03-drawer-treatment").selectOption("Mandatory");
			await page
				.getByTestId("kt-cl-cfg03-drawer-response-format")
				.selectOption("Yes/No confirmation");
			await page
				.getByTestId("kt-cl-cfg03-drawer-response-instruction")
				.fill("Confirm compliance.");
			await page
				.getByTestId("kt-cl-cfg03-drawer-evidence-requirement")
				.selectOption("Evidence required");
			await page
				.getByTestId("kt-cl-cfg03-drawer-evidence-instruction")
				.fill("Datasheet required");
			await page
				.getByTestId("kt-cl-cfg03-drawer-delivery-method")
				.fill("Commissioning test report");
			await page.getByTestId("kt-cl-cfg03-drawer-save").click();
			await expect(page.getByTestId("kt-cl-cfg03-continue")).toBeEnabled({ timeout: 15_000 });
		}
		await page.getByTestId("kt-cl-cfg03-continue").click();
		await expect(page).toHaveURL(new RegExp(`${PAGE_SLUG}/${CONFIG}`), { timeout: 20_000 });
		await expect(page.locator(ROOT)).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId("it-std-wizard-retired")).toHaveCount(0);
	});
});
