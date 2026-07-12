import { test, expect } from "@playwright/test";

const ASSET_BASE = "/assets/kentender_procurement/it_tender_wizard_impl";

test.describe("IT Wizard static screens — preview index", () => {
	test("index lists all screen links", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/index.html`);
		await expect(
			page.getByRole("heading", { name: /IT Tender Configuration Wizard/i }),
		).toBeVisible();
		await expect(page.getByRole("link", { name: "Tender Configuration Dashboard" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Tender Profile" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Publication Readiness" })).toBeVisible();
	});
});

test.describe("IT Wizard static screens — dashboard", () => {
	test("dashboard renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_dashboard.html`);
		await expect(page.getByText("Tender Configuration Dashboard").first()).toBeVisible();
		await expect(page.getByRole("button", { name: /Create Tender Configuration/i })).toBeVisible();
	});
});

test.describe("IT Wizard static screens — std config overview", () => {
	test("overview renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_std_config_overview.html`);
		await expect(page.getByText("Tender STD Configuration Overview").first()).toBeVisible();
		await expect(page.getByText("Configuration Steps").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — tender profile", () => {
	test("profile renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_tender_profile.html`);
		await expect(page.getByText("Tender Profile").first()).toBeVisible();
		await expect(page.getByText("Continue to Tender Data Sheet").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — tds", () => {
	test("tds renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_tds.html`);
		await expect(page.getByText("Tender Data Sheet").first()).toBeVisible();
		await expect(page.getByText("1. Tender Identity").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — it requirements", () => {
	test("requirements renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_it_requirements.html`);
		await expect(page.getByText("IT Requirements Definition").first()).toBeVisible();
		await expect(page.getByText("3.0 Technical Requirements").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — implementation schedule", () => {
	test("schedule renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_implementation_schedule.html`);
		await expect(page.getByText("Implementation Schedule Definition").first()).toBeVisible();
		await expect(page.getByText("Implementation Approach").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — system inventory", () => {
	test("inventory renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_system_inventory.html`);
		await expect(page.getByText("Systems & Inventory Items").first()).toBeVisible();
		await expect(page.getByText("Continue to Price Schedule").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — price schedule", () => {
	test("price schedule renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_price_schedule.html`);
		await expect(page.getByText("Download Price Schedule Preview").first()).toBeVisible();
		await expect(page.getByText("CONTINUE TO EVALUATION SETUP").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — evaluation setup", () => {
	test("evaluation renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_evaluation_setup.html`);
		await expect(page.getByText("Evaluation Setup").first()).toBeVisible();
		await expect(page.getByText("CONTINUE TO FORMS & EVIDENCE").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — forms and evidence", () => {
	test("forms renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_forms_and_evidence.html`);
		await expect(page.getByText("Forms & Evidence").first()).toBeVisible();
		await expect(page.getByText("Standard Tender Forms").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — scc", () => {
	test("scc renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_scc.html`);
		await expect(page.getByText("SCC / Contract Carry-Forward").first()).toBeVisible();
		await expect(page.getByText("Continue to Validation Report").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — validation report", () => {
	test("validation renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_validation_report.html`);
		await expect(page.getByText("Validation Report").first()).toBeVisible();
		await expect(page.getByText("Run Full Validation").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — review and approval", () => {
	test("review renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_review_and_approval.html`);
		await expect(page.getByText("Review & Approval").first()).toBeVisible();
		await expect(page.getByText("Continue to Render Preview").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — render preview", () => {
	test("preview renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_render_preview.html`);
		await expect(page.getByText("Final Tender Preview").first()).toBeVisible();
		await expect(page.getByText("Preview — Not For Publication").first()).toBeVisible();
	});
});

test.describe("IT Wizard static screens — publication readiness", () => {
	test("publication renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/it_wizard_publication_readiness.html`);
		await expect(page.getByText("Publication Readiness").first()).toBeVisible();
		await expect(page.getByText("Mark as Publication Ready").first()).toBeVisible();
	});
});
