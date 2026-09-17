// PLN-CHG-001 v1.23 §10.8 — PlanItemEditorScreen component tests (U09).
//
// This screen was cut hardest by v1.22, so most of these tests are about what
// is *not* there: no resolver status or rule version as ordinary fields, no
// plan-level reservation arithmetic, no None / Single lot / Lot count 1 shown
// to prove a stored value exists. What must be there is the handful of
// decisions the Planner actually makes, and every material issue in plain
// sight rather than inside the disclosure.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import PlanItemEditorScreen from "./PlanItemEditorScreen.vue";

const SOURCES = [
	{
		requirement: "Clinical training laptops for digital health rollout",
		department: "Human Resources Management and Development",
		quantity_number: "100",
		unit_label: "Each",
		required_by_display: "31 Dec 2027",
		amount_display: "KES 20,000,000",
	},
	{
		requirement: "Clinical deployment laptops for digital health rollout",
		department: "Digital Health",
		quantity_number: "150",
		unit_label: "Each",
		required_by_display: "31 Dec 2027",
		amount_display: "KES 30,000,000",
	},
];

function item(overrides = {}) {
	return {
		outcome: "OK",
		plan_item_id: "PPI-MOH-2027-033",
		record_version: 2,
		mutable: true,
		combined: true,
		is_active: false,
		header: {
			title: "Clinical training and deployment laptops for digital health rollout",
			reference_line: "PPI-MOH-2027-033 · Draft Version 1",
			item_state_badge: "Draft",
		},
		summary_line: "Goods · 250 each · Required by 31 Dec 2027",
		method_issue: "",
		planned_value_display: "KES 50,000,000",
		aggregation_reason_preview: "Both departments require the same laptop specification for the same…",
		estimate_basis_preview: "Market survey estimate includes delivery, installation…",
		sources: SOURCES,
		identity: {
			title: "Clinical training and deployment laptops for digital health rollout",
			description: "Procure and deploy one common laptop specification.",
			requirement_type: "Goods",
			procurement_category: "Goods",
			aggregation_reason: "Both departments require the same laptop specification for the same national digital-health rollout.",
		},
		classification: {
			procurement_method: "Open Tender",
			admissible_methods: ["Open Tender", "Request for Quotations"],
			strategic_objective: "OBJ-1",
			strategic_objectives: [{ id: "OBJ-1", title: "Strengthen interoperable national digital health services" }],
			objective_path: "Digital health systems › Health policy",
			estimate_basis: "Market survey estimate includes delivery, installation where applicable and other identified incidental costs.",
			estimate_basis_reference: "Market survey working paper",
			method_profile: { profile: "MPR-OPEN-TENDER-V18", verification_status: "Fixture-verified — not production law", found: true },
		},
		preference: {
			reservation_category: "",
			reservation_categories: ["None", "Youth", "Women"],
			county_resident_reservation: false,
			county_control_available: false,
			lotting_indicator: "Single lot",
			lot_count: 0,
		},
		baseline: {
			target_invitation_date: "2027-05-15",
			estimated_delivery_period_days: 60,
			estimated_completion_display: "24 Sep 2027",
			delivery_boundary_ok: true,
			rows: [
				{ milestone: "invitation", label: "Invitation or advertisement", date_display: "15 May 2027", source_boundary: false },
				{ milestone: "delivery_completion", label: "Delivery or implementation completion", date_display: "31 Dec 2027", source_boundary: true },
			],
		},
		scope_lock: { locked: false },
		notices: [],
		blockers: [],
		...overrides,
	};
}

function make(props = {}) {
	return mount(PlanItemEditorScreen, { props: { item: item(), pending: false, errorSummary: "", ...props } });
}

describe("PlanItemEditorScreen — U09 first view", () => {
	it("shows the five decision sections and the derived summary line", () => {
		const w = make();
		const text = w.text();
		expect(text).toContain("Purchase details");
		expect(text).toContain("Included requirements");
		expect(text).toContain("Estimated cost");
		expect(text).toContain("Procurement approach");
		expect(text).toContain("Dates");
		expect(w.find('[data-testid="ppi-summary-line"]').text()).toBe("Goods · 250 each · Required by 31 Dec 2027");
	});

	it("never shows system internals as ordinary business fields", () => {
		const w = make();
		// PLN22-AC-005. The rule version and source check exist, but only
		// inside Supporting details for authorised inspection.
		const supporting = w.find('[data-testid="ppi-supporting"]');
		expect(supporting.attributes("open")).toBeUndefined();
		expect(w.find('[data-testid="ppi-rule-evidence"]').text()).toContain("MPR-OPEN-TENDER-V18");
		expect(w.text()).not.toContain("Procedure — Planning example");
		expect(w.text()).not.toContain("Method support");
	});

	it("omits plan-level reservation arithmetic entirely", () => {
		const w = make();
		// PLN22-AC-006 — that calculation happens once, at plan level.
		expect(w.text()).not.toContain("Required allocation");
		expect(w.text()).not.toContain("Planned qualifying allocation");
		expect(w.text()).not.toContain("Shortfall");
	});

	it("omits None, Single lot, Lot count 1 and an inapplicable county field", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-reservation"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-lot-count"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-county"]').exists()).toBe(false);
		expect(w.text()).not.toContain("Single lot");
		// It can still be added deliberately.
		expect(w.find('[data-testid="ppi-add-reservation"]').exists()).toBe(true);
	});

	it("does not display the fixed single-year horizon", () => {
		const w = make();
		expect(w.text()).not.toContain("Plan horizon");
		expect(w.text()).not.toContain("Single year");
	});

	it("shows the designation when one is set or required", () => {
		const set = make({ item: item({ preference: { ...item().preference, reservation_category: "Youth" } }) });
		expect(set.find('[data-testid="ppi-reservation"]').exists()).toBe(true);

		const required = make({ item: item({ blockers: [{ code: "PLN_RESERVATION_REQUIRED", message: "Choose who this is reserved for." }] }) });
		expect(required.find('[data-testid="ppi-reservation"]').exists()).toBe(true);
	});

	it("shows lots only when there are several", () => {
		const w = make({ item: item({ preference: { ...item().preference, lotting_indicator: "Packaged into lots", lot_count: 3 } }) });
		expect(w.find('[data-testid="ppi-lot-count"]').exists()).toBe(true);
	});
});

describe("PlanItemEditorScreen — included requirements and cost", () => {
	it("lists each source with separate quantity and unit", () => {
		const w = make();
		const rows = w.findAll('[data-testid="ppi-source-row"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Human Resources Management and Development");
		expect(rows[0].text()).toContain("100");
		expect(rows[0].text()).toContain("KES 20,000,000");
	});

	it("previews the aggregation reason with a disclosure to the full text", async () => {
		const w = make();
		expect(w.find('[data-testid="ppi-combined"]').text()).toContain("Combined purchase");
		expect(w.find('[data-testid="ppi-full-reason"]').exists()).toBe(false);
		await w.find('[data-testid="ppi-read-reason"]').trigger("click");
		expect(w.find('[data-testid="ppi-full-reason"]').text()).toContain("national digital-health rollout");
	});

	it("derives the planned amount rather than offering it as an input", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-planned-value"]').text()).toBe("KES 50,000,000");
		expect(w.find('[data-testid="ppi-planned-value"]').element.tagName).not.toBe("INPUT");
	});
});

describe("PlanItemEditorScreen — dates", () => {
	it("says the schedule meets the departmental deadline", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-completion"]').text()).toBe("24 Sep 2027");
		expect(w.find('[data-testid="ppi-deadline"]').text()).toBe("31 Dec 2027");
		expect(w.find('[data-testid="ppi-boundary"]').text()).toBe("Expected to meet the departmental deadline");
	});

	it("U09-INVALID-SCHEDULE: blocks Save and offers Review dates", () => {
		const w = make({
			item: item({
				baseline: { ...item().baseline, estimated_completion_display: "2 Jan 2028", delivery_boundary_ok: false },
				blockers: [{ code: "PLN_DELIVERY_BOUNDARY_INSUFFICIENT", message: "Estimated completion is after the department's required date." }],
			}),
		});
		expect(w.find('[data-testid="ppi-boundary"]').text()).toBe(
			"Expected completion is after the department's required date.",
		);
		expect(w.find('[data-testid="ppi-save"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="ppi-review-dates"]').exists()).toBe(true);
	});
});

describe("PlanItemEditorScreen — material issues stay visible", () => {
	it("replaces resolver mechanics with one plain method issue and its owner", () => {
		const w = make({
			item: item({
				method_issue: "Open Tender cannot be confirmed until the applicable method rule is verified in System setup.",
			}),
		});
		const issue = w.find('[data-testid="ppi-method-issue"]');
		expect(issue.text()).toContain("cannot be confirmed until the applicable method rule is verified in System setup");
		expect(w.find('[data-testid="ppi-open-setup"]').text()).toBe("Go to System setup");
	});

	it("U09-LOCKED: shows the scope restriction and removes the remove control", () => {
		const w = make({
			item: item({
				mutable: false,
				scope_lock: { locked: true },
				notices: [
					{
						kind: "scope_lock",
						heading: "This item already has an authorised requisition",
						text: "Add extra requirements as a separate item in a plan update.",
					},
				],
			}),
		});
		expect(w.find('[data-testid="ppi-notice"]').text()).toContain("already has an authorised requisition");
		expect(w.find('[data-testid="ppi-remove"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-save"]').exists()).toBe(false);
	});

	it("keeps a material issue outside Supporting details", () => {
		const w = make({
			item: item({
				notices: [{ kind: "source_correction", heading: "A departmental requirement changed", text: "Rebuild this purchase." }],
			}),
		});
		const supporting = w.find('[data-testid="ppi-supporting"]');
		expect(supporting.attributes("open")).toBeUndefined();
		// The notice is in the page body, not inside the disclosure.
		expect(w.find('[data-testid="ppi-notice"]').exists()).toBe(true);
		expect(supporting.text()).not.toContain("A departmental requirement changed");
	});
});
