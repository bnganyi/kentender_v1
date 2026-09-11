// REQ-CHG-001 v1.6 §13.4 — StartScreen component tests. Exact fields,
// read-only source panel, allocation table, product panel, the
// cross-department notice and its absence for a single-department item, and
// the three named §13.13 states this screen renders.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import StartScreen from "./StartScreen.vue";

const PROJECTION = {
	outcome: "OK",
	eligible: true,
	plan_item_id: "PPI-MOH-2027-033",
	title: "Clinical training and deployment laptops for digital health rollout",
	procurement_method: "Open Tender",
	strategic_objective: "OBJ-MOH-2023-001",
	objective_path: "Digital health systems › Health policy, standards and regulation › Digital health governance",
	strategic_objective_path: "Digital health systems › Health policy, standards and regulation › Digital health governance",
	plan_horizon: "Single year",
	multi_year_justification: "",
	contributing_org_unit_ids: ["OU-DH", "OU-HRMD"],
	total_value: 50000000,
	planned_dates: { delivery_completion_date: "2027-09-30" },
	sources: [
		{ plan_source_allocation_id: "PIL-MOH-033-001", organisation_unit: "OU-HRMD", title: "Business laptops", remaining_quantity: 100, unit: "Each", remaining_amount: 20000000 },
		{ plan_source_allocation_id: "PIL-MOH-033-002", organisation_unit: "OU-DH", title: "Business laptops", remaining_quantity: 150, unit: "Each", remaining_amount: 30000000 },
	],
};

const DETAIL = {
	outcome: "OK",
	projection: PROJECTION,
	contributing_departments_label: "Digital Health · Human Resources Management and Development",
	organisation_unit_labels: { "OU-DH": "Digital Health", "OU-HRMD": "Human Resources Management and Development" },
	strategic_objective_title: "Strengthen interoperable national digital health services",
	business_need: "Equip clinical training and field deployment staff with a common laptop specification for the national digital health rollout.",
	expected_operational_result: "Staff can use secure, supported equipment for training and field digital-health work.",
	compatibility: [],
	is_compatible: true,
	open_requisition: "",
	can_prepare: true,
};

function make(overrides = {}) {
	return mount(StartScreen, {
		props: { loading: false, error: "", supportRef: "", detail: DETAIL, planItemId: "PPI-MOH-2027-033", pending: false, ...overrides },
	});
}

describe("StartScreen — REQ-DES-02", () => {
	it("renders the exact title and read-only Planning source panel", () => {
		const w = make();
		expect(w.find(".req-start-title").text()).toBe("Prepare Requisition from approved Plan Item");
		const card = w.find('[data-testid="req-planning-source"]');
		expect(card.text()).toContain("PPI-MOH-2027-033 — Clinical training and deployment laptops for digital health rollout");
		expect(card.text()).toContain("Digital Health · Human Resources Management and Development");
		expect(card.text()).toContain("Open Tender");
		expect(card.text()).toContain("30 Sep 2027");
		expect(card.text()).toContain("KES 50,000,000.00");
		expect(card.find('[data-testid="req-plan-horizon"]').text()).toBe("Single year");
		expect(card.text()).toContain("OBJ-MOH-2023-001 — Strengthen interoperable national digital health services");
		expect(card.text()).toContain("Digital health systems › Health policy, standards and regulation › Digital health governance");
		expect(card.text()).toContain("Equip clinical training and field deployment staff");
		expect(card.text()).toContain("Staff can use secure, supported equipment");
	});

	it("shows only the objective id, never a duplicated id, when its title cannot be resolved", () => {
		// a frozen Plan Item snapshot can outlive the Strategy Node it once
		// pointed to (confirmed live on a real fixture item) — the server
		// returns "" for strategic_objective_title in that case, and this
		// screen must never render "id — id".
		const w = make({ detail: { ...DETAIL, strategic_objective_title: "" } });
		const line = w.find(".req-objective-id");
		expect(line.text()).toBe("OBJ-MOH-2023-001");
		expect(line.text()).not.toContain("—");
	});

	it("shows the multi-year note only for a multi-year Plan Item", () => {
		const single = make();
		expect(single.text()).not.toContain("full multi-year allocation");
		const multi = make({
			detail: { ...DETAIL, projection: { ...PROJECTION, plan_horizon: "Multi-year", multi_year_justification: "Phased three-year rollout" } },
		});
		expect(multi.find('[data-testid="req-plan-horizon"]').text()).toBe("Multi-year · Phased three-year rollout");
		expect(multi.text()).toContain("The value above is this Plan Item's full multi-year allocation, not one year's worth.");
	});

	it("renders the two-row allocation table with department labels, not raw OU ids", () => {
		const w = make();
		const table = w.find('[data-testid="req-allocations"]');
		expect(table.findAll("thead th").map((th) => th.text())).toEqual(["Contributing department", "Source requirement", "Remaining quantity", "Remaining value"]);
		const rows = table.findAll("tbody tr");
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Human Resources Management and Development");
		expect(rows[0].text()).toContain("100 Each");
		expect(rows[0].text()).toContain("KES 20,000,000.00");
		expect(rows[1].text()).toContain("Digital Health");
	});

	it("renders the static Requirement product panel with no selector", () => {
		const w = make();
		const card = w.find('[data-testid="req-product-panel"]');
		expect(card.find(".req-product-value").text()).toBe("IT Equipment");
		expect(card.find("select").exists()).toBe(false);
		expect(card.text()).toContain("This release supports straightforward off-the-shelf IT equipment.");
	});

	it("shows the cross-department notice naming the larger contributor when more than one department contributed", () => {
		const w = make();
		const notice = w.find('[data-testid="req-cross-department-notice"]');
		expect(notice.text()).toContain("This Requisition draws from two departments because Planning combined their Needs into one Plan Item.");
		expect(notice.text()).toContain("Digital Health, as the larger contributor, certifies the departmental submission.");
	});

	it("omits the cross-department notice for a single-department item", () => {
		const w = make({ detail: { ...DETAIL, projection: { ...PROJECTION, contributing_org_unit_ids: ["OU-DH"] } } });
		expect(w.find('[data-testid="req-cross-department-notice"]').exists()).toBe(false);
	});

	it("emits prepare with the plan item id and navigate on cancel, with no template or STD selector anywhere", async () => {
		const w = make();
		expect(w.text()).not.toContain("Template");
		expect(w.text()).not.toContain("STD");
		const actions = w.find(".req-actions");
		await actions.findAll("button")[0].trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["procurement-requisitions"]);
		await w.find('[data-testid="req-prepare-requisition"]').trigger("click");
		expect(w.emitted("prepare")[0][0]).toBe("PPI-MOH-2027-033");
	});

	it("hides Prepare Requisition entirely for an actor the command gate would refuse (read-offer parity)", () => {
		// e.g. Head of Procurement Function / Procurement Planner / Auditor,
		// none of whom hold Departmental Author/Head of User Department —
		// confirmed live: this button previously reached a masked REQ_NOT_FOUND.
		const w = make({ detail: { ...DETAIL, can_prepare: false } });
		expect(w.find('[data-testid="req-prepare-requisition"]').exists()).toBe(false);
		expect(w.find(".req-actions button").text()).toBe("Cancel");
	});
});

describe("StartScreen — §13.13 named states", () => {
	it("shows the no-eligible-items state when the Plan Item is not eligible", () => {
		const w = make({ detail: { ...DETAIL, projection: { ...PROJECTION, eligible: false } } });
		expect(w.find('[data-testid="req-start-ineligible"]').text()).toContain("No Active Plan Items are ready for Requisition.");
		expect(w.find('[data-testid="req-planning-source"]').exists()).toBe(false);
	});

	it("shows the product-unsupported state with Return to workspace", async () => {
		const w = make({ detail: { ...DETAIL, is_compatible: false } });
		const card = w.find('[data-testid="req-start-unsupported"]');
		expect(card.text()).toContain("This Plan Item is not supported by the IT-equipment Requisition pattern.");
		await card.find("button").trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["procurement-requisitions"]);
	});

	it("shows the open-requisition-exists state, with Open it only when authorised", () => {
		const w = make({ detail: { ...DETAIL, open_requisition: "PRQ-0099" } });
		const card = w.find('[data-testid="req-start-open-exists"]');
		expect(card.text()).toContain("This Plan Item already has an open Requisition.");
		expect(card.find('[data-testid="req-start-open-existing"]').exists()).toBe(true);

		const notAuthorised = make({ detail: { ...DETAIL, open_requisition: "PRQ-0099" }, canOpenExisting: false });
		expect(notAuthorised.find('[data-testid="req-start-open-existing"]').exists()).toBe(false);
	});

	it("renders the load-error state with Try again and the support reference", async () => {
		const w = make({ error: "boom", supportRef: "REQ-ERR-20261201-0917" });
		const card = w.find('[data-testid="req-start-error"]');
		expect(card.text()).toContain("Support reference: REQ-ERR-20261201-0917");
		await card.find("button").trigger("click");
		expect(w.emitted("reload")).toHaveLength(1);
	});

	it("renders the loading skeleton and nothing else", () => {
		const w = make({ loading: true });
		expect(w.find('[data-testid="req-start-loading"]').exists()).toBe(true);
		expect(w.find('[data-testid="req-planning-source"]').exists()).toBe(false);
	});
});
