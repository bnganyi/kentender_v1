import { test, expect } from "@playwright/test";

const ASSET_BASE = "/assets/kentender_procurement/std_prod_impl";

test.describe("STD prod static screens — preview index", () => {
	test("index lists all screen links", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/index.html`);
		await expect(page.getByRole("heading", { name: /STD Engine Production UI/i })).toBeVisible();
		await expect(page.getByRole("link", { name: "STD Library" })).toBeVisible();
		await expect(page.getByRole("link", { name: "STD Family Detail" })).toBeVisible();
		await expect(page.getByRole("link", { name: "STD Version Detail" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Source Document & Traceability" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Section and Clause Map" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Clause Detail" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Parameter Dictionary" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Parameter Detail" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Rule Dictionary" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Rule Detail" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Form Schema Manager" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Form Detail & Field Builder" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Requirement Schema Manager" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Price Schedule Schema" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Evaluation Schema" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Render Blocks" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Validation Report" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Review and Approval" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Usage and Tender Bindings" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Import Package Review" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Version Diff and Supersession" })).toBeVisible();
		await expect(page.getByRole("link", { name: "Audit Log" })).toBeVisible();
	});
});

test.describe("STD prod static screens — library", () => {
	test("library screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_library.html`);
		await expect(page).toHaveTitle(/STD Library \| KenTender STD Engine/);
		await expect(page.getByRole("heading", { name: "Standard Tender Documents" })).toBeVisible();
		await expect(page.getByText("STD FAMILIES", { exact: true })).toBeVisible();
		await expect(page.getByRole("columnheader", { name: "Family Code" })).toBeVisible();
		await page.getByRole("button", { name: "filter_list Filters" }).click();
		await expect(page.getByRole("heading", { name: "Filters" })).toBeVisible();
	});
});

test.describe("STD prod static screens — family detail", () => {
	test("family detail screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_family_detail.html`);
		await expect(page).toHaveTitle(/STD Family Detail/);
		await expect(page.getByText(/Family Code: KE-PPRA-IT/i)).toBeVisible();
		await expect(page.getByRole("heading", { name: /VERSIONS REPOSITORY/i })).toBeVisible();
		await expect(page.getByText("REVIEW POLICY")).toBeVisible();
	});
});

test.describe("STD prod static screens — version detail", () => {
	test("version detail screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_version_detail.html`);
		await expect(page).toHaveTitle(/STD Version Detail/);
		await expect(page.getByText("ACTIVE VERSION — READ ONLY")).toBeVisible();
		await expect(page.getByRole("heading", { name: /Module Integrity Status/i })).toBeVisible();
		await expect(page.getByText("Operational Integrity")).toBeVisible();
	});
});

test.describe("STD prod static screens — source document", () => {
	test("source document screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_source_doc.html`);
		await expect(page).toHaveTitle(/Source Document & Traceability/);
		await expect(
			page.getByRole("heading", {
				name: /KE-PPRA-IT-2024-01 — Source Documents & Traceability/i,
			}),
		).toBeVisible();
		await expect(page.getByRole("heading", { name: "Source Document Summary" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Official Source Files" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Traceability Anchor Map" })).toBeVisible();
	});
});

test.describe("STD prod static screens — section clauses", () => {
	test("section and clause map screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_section_clauses.html`);
		await expect(page).toHaveTitle(/Section and Clause Map/);
		await expect(page.getByRole("heading", { name: "Section and Clause Map", exact: true })).toBeVisible();
		await expect(page.getByText("Section 1: Instructions to Tenderers")).toBeVisible();
		await expect(page.getByText("Clause Map: Section 1")).toBeVisible();
	});
});

test.describe("STD prod static screens — clause detail", () => {
	test("clause detail screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_clause_detail.html`);
		await expect(page).toHaveTitle(/Clause Detail/);
		await expect(page.getByRole("heading", { name: "Eligible Tenderers" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Audit History" })).toBeVisible();
		await expect(page.getByText("Clause Topology")).toBeVisible();
	});
});

test.describe("STD prod static screens — parameter dictionary", () => {
	test("parameter dictionary screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_parameter_dictionary.html`);
		await expect(page).toHaveTitle(/Parameter Dictionary/);
		await expect(page.getByRole("heading", { name: "Parameter Dictionary", exact: true })).toBeVisible();
		await expect(page.getByText("tender_ref_id")).toBeVisible();
	});
});

test.describe("STD prod static screens — parameter detail", () => {
	test("parameter detail screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_parameter_detail.html`);
		await expect(page).toHaveTitle(/Parameter Detail/);
		await expect(page.getByRole("heading", { name: /Tender Reference ID/i })).toBeVisible();
		await expect(page.getByText("FIELD DEFINITION")).toBeVisible();
		await expect(page.getByText("VALIDATION RULES")).toBeVisible();
	});
});

test.describe("STD prod static screens — rule dictionary", () => {
	test("rule dictionary screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_rule_dictionary.html`);
		await expect(page).toHaveTitle(/Rule Dictionary/);
		await expect(page.getByRole("heading", { name: "Rule Dictionary", exact: true })).toBeVisible();
		await expect(page.getByText("Rule Tests Summary")).toBeVisible();
	});
});

test.describe("STD prod static screens — rule detail", () => {
	test("rule detail screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_rule_detail.html`);
		await expect(page).toHaveTitle(/Rule Detail/);
		await expect(page.getByRole("heading", { name: /String Length Check/i })).toBeVisible();
		await expect(page.getByText("Rule Definition")).toBeVisible();
		await expect(page.getByText("Execution History")).toBeVisible();
	});
});

test.describe("STD prod static screens — form schema manager", () => {
	test("form schema manager screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_form_schema_manager.html`);
		await expect(page).toHaveTitle(/Form Schema Manager/);
		await expect(page.getByRole("heading", { name: "Form Schema Manager", exact: true })).toBeVisible();
		await expect(page.getByText("TOTAL FORMS")).toBeVisible();
		await expect(page.getByText("FORM-TECH-01")).toBeVisible();
	});
});

test.describe("STD prod static screens — form detail field builder", () => {
	test("form detail field builder screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_form_detail_field_builder.html`);
		await expect(page).toHaveTitle(/Form Detail & Field Builder/);
		await expect(page.getByRole("heading", { name: "Technical Proposal Submission" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Field Configuration" })).toBeVisible();
	});
});

test.describe("STD prod static screens — requirement schema manager", () => {
	test("requirement schema manager screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_requirement_schema_manager.html`);
		await expect(page).toHaveTitle(/Requirement Schema Manager/);
		await expect(page.getByRole("heading", { name: "Requirement Schema Manager" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Requirement Categories" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Evaluation Linkage Model" })).toBeVisible();
	});
});

test.describe("STD prod static screens — price schedule schema", () => {
	test("price schedule schema screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_price_schedule_schema.html`);
		await expect(page).toHaveTitle(/Price Schedule Schema/);
		await expect(page.getByRole("heading", { name: "Price Schedule Master Definition" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "System Integrity Log" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "REVISION CONTEXT" })).toBeVisible();
	});
});

test.describe("STD prod static screens — evaluation schema", () => {
	test("evaluation schema screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_evaluation_schema.html`);
		await expect(page).toHaveTitle(/Evaluation Schema/);
		await expect(page.getByText("TOTAL CRITERIA", { exact: true })).toBeVisible();
		await expect(page.getByText("Evaluation Schema").first()).toBeVisible();
	});
});

test.describe("STD prod static screens — render blocks", () => {
	test("render blocks screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_render_blocks.html`);
		await expect(page).toHaveTitle(/Render Blocks/);
		await expect(page.getByRole("heading", { name: "Render Blocks" })).toBeVisible();
		await expect(page.getByText("TOTAL RENDER BLOCKS", { exact: true })).toBeVisible();
		await expect(page.getByText("RB-001")).toBeVisible();
	});
});

test.describe("STD prod static screens — validation report", () => {
	test("validation report screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_validation_report.html`);
		await expect(page).toHaveTitle(/Validation Report/);
		await expect(page.getByRole("heading", { name: "Validation Report" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Standard Validation Audit" })).toBeVisible();
	});
});

test.describe("STD prod static screens — review and approval", () => {
	test("review and approval screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_review_and_approval.html`);
		await expect(page).toHaveTitle(/Review and Approval/);
		await expect(page.getByRole("heading", { name: "Review and Approval" })).toBeVisible();
		await expect(page.getByText("REVIEW STAGE TIMELINE")).toBeVisible();
		await expect(page.getByText("ENHANCED DECISION PANEL")).toBeVisible();
	});
});

test.describe("STD prod static screens — usage and tender bindings", () => {
	test("usage and tender bindings screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_usage_and_tender_bindings.html`);
		await expect(page).toHaveTitle(/Usage and Tender Bindings/);
		await expect(page.getByRole("heading", { name: "Usage and Tender Bindings" })).toBeVisible();
		await expect(page.getByText("TENDER BINDINGS REGISTRY")).toBeVisible();
		await expect(page.getByText("ACTIVE TENDERS (THIS VERSION)")).toBeVisible();
	});
});

test.describe("STD prod static screens — import package review", () => {
	test("import package review screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_import_package_review.html`);
		await expect(page).toHaveTitle(/Import Package Review/);
		await expect(page.getByRole("heading", { name: "Import Package Review" })).toBeVisible();
		await expect(page.getByRole("heading", { name: "Upload Standardized Package" })).toBeVisible();
		await expect(page.getByText("EXPANDED PACKAGE MANIFEST")).toBeVisible();
	});
});

test.describe("STD prod static screens — version diff and supersession", () => {
	test("version diff and supersession screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_version_diff_and_supersession.html`);
		await expect(page).toHaveTitle(/Version Diff and Supersession/);
		await expect(page.getByRole("heading", { name: "Supersession Decision" })).toBeVisible();
		await expect(page.getByText("Version Diff and Supersession").first()).toBeVisible();
	});
});

test.describe("STD prod static screens — audit log", () => {
	test("audit log screen renders design regions", async ({ page }) => {
		await page.goto(`${ASSET_BASE}/std_audit_log.html`);
		await expect(page).toHaveTitle(/Audit Log/);
		await expect(page.getByRole("heading", { name: "Audit Log" })).toBeVisible();
		await expect(page.getByText("Audit Events")).toBeVisible();
		await expect(page.getByRole("heading", { name: "Immutable Integrity Hash Verification" })).toBeVisible();
	});
});
