import { test, expect } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";

const SCHEDULE_ROUTE = "/desk/it-tender-configuration-implementation-schedule";
const INVENTORY_ROUTE = "/desk/it-tender-configuration-system-inventory";
const SEED_CODE = "ITCFG-DASH-SEED-001";

const INVENTORY_PAYLOAD = {
	configuration_id: SEED_CODE,
	title: "Data Center Hardware Refresh",
	planning_package: { code: "PKG-ICT-001", name: "ICT Modernization Package" },
	procuring_entity: { code: "PE-NATIONAL-TREASURY", name: "National Treasury" },
	method: { code: "OPEN_NATIONAL", name: "Open Tender" },
	state_label: "In Configuration",
	validation: { blockers: 0, warnings: 1 },
	completion: { completed: 1, total: 1, percent: 100 },
	requirement_options: [
		{ id: "REQ-TECH-001", code: "REQ-TECH-001", name: "Finance integration requirement" },
		{ id: "REQ-TECH-002", code: "REQ-TECH-002", name: "Data migration requirement" },
	],
	schedule_options: [
		{ id: "PHASE_2", code: "PHASE_2", name: "Integration and migration" },
		{ id: "PH2-MIGRATION", code: "PH2-MIGRATION", name: "Data migration complete" },
	],
	categories: [
		{
			category: "SYSTEMS_IN_SCOPE",
			label: "Systems in Scope",
			item_count: 1,
			items: [
				{
					item_id: "INV-CORE-FINANCE",
					item_code: "INV-CORE-FINANCE",
					title: "Core Finance System",
					category: "SYSTEMS_IN_SCOPE",
					category_label: "Systems in Scope",
					description: "Production finance platform.",
					scope_status: "IN_SCOPE",
					required_action: "MIGRATE",
					bidder_consideration: "Provide a controlled migration approach.",
					data_volume: "500 GB",
					integration_requirement: "API",
					confidentiality_level: "CONFIDENTIAL",
					review_status: "APPROVED",
					pricing_policy: "REQUIRED",
					requirement_refs: ["REQ-TECH-001", "REQ-TECH-002"],
					schedule_refs: ["PHASE_2", "PH2-MIGRATION"],
					contract_carry_forward: 1,
				},
			],
		},
	],
};

async function mockInventoryApi(page: import("@playwright/test").Page) {
	await page.route("**/api/method/**get_system_inventory_api", async (route) => {
		await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: { data: INVENTORY_PAYLOAD } }) });
	});
	await page.route("**/api/method/**save_system_inventory_api", async (route) => {
		await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ message: { data: INVENTORY_PAYLOAD } }) });
	});
}

test.describe("IT Wizard System Inventory Desk wiring", () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await mockInventoryApi(page);
		await page.evaluate(() => {
			localStorage.removeItem("_page:it-tender-configuration-system-inventory");
		});
	});

	test("direct route hydrates eight categories and inventory rows", async ({ page }) => {
		await page.goto(`${INVENTORY_ROUTE}?configuration_id=${SEED_CODE}`, { waitUntil: "domcontentloaded" });
		const inventory = page.frameLocator('[data-testid="it-wizard-system-inventory-iframe"]');
		await expect(inventory.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await expect(inventory.locator("[data-itw-inv-categories] button")).toHaveCount(8);
		await expect(inventory.locator("[data-itw-inv-table-host] [data-itw-inv-row]").first()).toBeVisible();
		await expect(inventory.locator("[data-itw-inv-row]").first()).toContainText("Core Finance System");
	});

	test("schedule continuation preserves configuration context", async ({ page }) => {
		await page.goto(`${SCHEDULE_ROUTE}?configuration_id=${SEED_CODE}`, { waitUntil: "domcontentloaded" });
		const schedule = page.frameLocator('[data-testid="it-wizard-implementation-schedule-iframe"]');
		await expect(schedule.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await schedule
			.locator("[data-itw-sched-actions]")
			.getByRole("button", { name: /Continue to System Inventory/i })
			.click();
		await expect(page).toHaveURL(
			new RegExp(`/desk/it-tender-configuration-system-inventory.*configuration_id=${SEED_CODE}`),
			{ timeout: 15_000 },
		);
	});

	test("drawer reuses one shell and exposes business references without pricing inputs", async ({ page }) => {
		await page.goto(`${INVENTORY_ROUTE}?configuration_id=${SEED_CODE}`, { waitUntil: "domcontentloaded" });
		const inventory = page.frameLocator('[data-testid="it-wizard-system-inventory-iframe"]');
		await expect(inventory.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const drawer = inventory.locator("[data-itw-inv-drawer]");
		await expect(drawer).toHaveCount(1);
		await inventory.locator("[data-itw-inv-row] [data-itw-inv-action='edit']").first().click();
		await expect(drawer).toHaveAttribute("data-itw-inv-drawer-open", "1");
		await expect(drawer.getByText("Related IT Requirement")).toBeVisible();
		await expect(drawer.getByText("Implementation Phase")).toBeVisible();
		await expect(drawer.getByText("Price Schedule Link")).toBeVisible();
		const priceLink = drawer.locator("[data-itw-inv-price-link]");
		await expect(priceLink).toHaveAttribute("aria-readonly", "true");
		await expect(priceLink).toHaveText(/Required|Optional|Not Priced/);
		await expect(drawer.locator('[data-itw-inv-field="requirement_ref"]')).toHaveValue("REQ-TECH-001");
		await expect(drawer.locator('[data-itw-inv-field="schedule_ref"]')).toHaveValue("PHASE_2");
		await expect(drawer.getByText(/Quantity|Unit Price|Pricing Class/)).toHaveCount(0);
		const saveRequest = page.waitForRequest((request) =>
			request.url().includes("save_system_inventory_api"),
		);
		await drawer.locator("[data-itw-inv-update]").click();
		const params = new URLSearchParams((await saveRequest).postData() || "");
		const saved = JSON.parse(params.get("inventory_json") || "{}");
		expect(saved.selected_item.requirement_refs).toEqual(["REQ-TECH-001", "REQ-TECH-002"]);
		expect(saved.selected_item.schedule_refs).toEqual(["PHASE_2", "PH2-MIGRATION"]);
	});

	test("add inventory item reuses the drawer with technical defaults", async ({ page }) => {
		await page.goto(`${INVENTORY_ROUTE}?configuration_id=${SEED_CODE}`, { waitUntil: "domcontentloaded" });
		const inventory = page.frameLocator('[data-testid="it-wizard-system-inventory-iframe"]');
		await expect(inventory.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		await inventory.locator("[data-itw-inv-add]").click();
		const drawer = inventory.locator("[data-itw-inv-drawer]");
		await expect(drawer).toHaveAttribute("data-itw-inv-drawer-open", "1");
		await expect(drawer.locator('[data-itw-inv-field="category"]')).toHaveValue("SYSTEMS_IN_SCOPE");
		await expect(drawer.locator('[data-itw-inv-field="scope_status"]')).toHaveValue("IN_SCOPE");
		await expect(drawer.locator("[data-itw-inv-price-link]")).toHaveText("Not Priced");
	});

	test("price schedule continuation remains disabled", async ({ page }) => {
		await page.goto(`${INVENTORY_ROUTE}?configuration_id=${SEED_CODE}`, { waitUntil: "domcontentloaded" });
		const inventory = page.frameLocator('[data-testid="it-wizard-system-inventory-iframe"]');
		await expect(inventory.locator("body")).toHaveAttribute("data-it-wizard-hydrated", "1", {
			timeout: 30_000,
		});
		const continueButton = inventory
			.locator("[data-itw-inv-actions]")
			.getByRole("button", { name: /Continue to Price Schedule/i });
		await expect(continueButton).toBeDisabled();
		await expect(continueButton).toHaveAttribute("aria-disabled", "true");
	});
});
