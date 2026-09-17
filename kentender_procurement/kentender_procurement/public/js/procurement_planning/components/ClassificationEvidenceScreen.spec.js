// PLN-CHG-001 v1.23 §10.5 — ClassificationEvidenceScreen component tests
// (U06-ACCEPTED-CLASSIFICATION and U06-CORRECT-CLASSIFICATION).
//
// The screen has to keep two things unmistakable: correcting a classification
// never reopens the departmental submission, and the correction's consequence
// depends entirely on what already consumed the source. Each of the four
// recovery routes says something different, so each is pinned.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ClassificationEvidenceScreen from "./ClassificationEvidenceScreen.vue";

const TYPES = [
	{ requirement_type: "Consulting services", procurement_category: "Services" },
	{ requirement_type: "Goods", procurement_category: "Goods" },
	{ requirement_type: "Non-consulting services", procurement_category: "Services" },
	{ requirement_type: "Works", procurement_category: "Works" },
];

function classification(overrides = {}) {
	return {
		evidence_id: "DPPV-MOH-DHI-2027-001-V3",
		requirement_type: "Works",
		procurement_category: "Works",
		actor_name: "Mercy Kilonzo",
		at_display: "29 Nov 2026, 15:00 EAT",
		corrected: false,
		corrections: [],
		original: { requirement_type: "Works", procurement_category: "Works" },
		...overrides,
	};
}

function row(overrides = {}) {
	return {
		dpp_entry_id: "DPPE-MOH-DHI-2027-001",
		title: "National digital health infrastructure upgrade",
		excluded: false,
		can_correct: true,
		classification: classification(),
		affected: { recovery: "none", draft_items: [], governed_items: [], locked_items: [] },
		...overrides,
	};
}

function evidence(overrides = {}) {
	return {
		ok: true,
		dpp_submission: "DPPS-MOH-DHI-2027-001-V3",
		dpp_reference: "DPP-MOH-DHI-2027-001",
		submission_number: 3,
		rows: [row()],
		requirement_types: TYPES,
		can_correct: true,
		...overrides,
	};
}

function make(props = {}) {
	return mount(ClassificationEvidenceScreen, {
		props: { evidence: evidence(), panel: null, newType: "", reason: "", error: "", pending: false, ...props },
	});
}

describe("ClassificationEvidenceScreen — U06-ACCEPTED-CLASSIFICATION", () => {
	it("shows the accepted type, derived category and who classified it when", () => {
		const w = make();
		expect(w.find('[data-testid="pln-class-title"]').text()).toBe("View accepted requirement classifications");
		expect(w.find('[data-testid="pln-class-context"]').text()).toContain("DPP-MOH-DHI-2027-001");
		const r = w.find('[data-testid="pln-class-row"]');
		expect(r.text()).toContain("Works");
		expect(r.text()).toContain("Mercy Kilonzo");
		expect(r.text()).toContain("29 Nov 2026, 15:00 EAT");
		expect(w.find('[data-testid="pln-class-correct"]').text()).toBe("Correct classification");
	});

	it("states that the departmental submission does not change", () => {
		const w = make();
		expect(w.find('[data-testid="pln-class-note"]').text()).toContain(
			"The certified departmental requirement will not change.",
		);
	});

	it("offers no correction on an excluded requirement", () => {
		const w = make({
			evidence: evidence({
				rows: [row({ excluded: true, can_correct: false, classification: null })],
			}),
		});
		const r = w.find('[data-testid="pln-class-row"]');
		expect(r.text()).toContain("Not applicable");
		expect(w.find('[data-testid="pln-class-correct"]').exists()).toBe(false);
	});

	it("offers no correction to a reader who holds no Planner assignment", () => {
		const w = make({ evidence: evidence({ can_correct: false }) });
		expect(w.find('[data-testid="pln-class-correct"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-class-row"]').exists()).toBe(true);
	});

	it("shows what a corrected row was corrected from, and why", () => {
		const corrected = row({
			classification: classification({
				requirement_type: "Non-consulting services",
				procurement_category: "Services",
				corrected: true,
				corrections: [
					{
						previous_requirement_type: "Works",
						previous_procurement_category: "Works",
						requirement_type: "Non-consulting services",
						procurement_category: "Services",
						reason: "The requirement is for a managed technical service and contains no construction work.",
					},
				],
			}),
		});
		const w = make({ evidence: evidence({ rows: [corrected] }) });
		const history = w.find('[data-testid="pln-class-history"]');
		expect(history.text()).toContain("Works / Works");
		expect(history.text()).toContain("managed technical service");
	});
});

describe("ClassificationEvidenceScreen — U06-CORRECT-CLASSIFICATION", () => {
	function panelProps(extra = {}) {
		return { panel: row(), ...extra };
	}

	it("shows the current classification read-only and derives the new category", () => {
		const w = make(panelProps({ newType: "Non-consulting services" }));
		const panel = w.find('[data-testid="pln-class-panel"]');
		expect(panel.text()).toContain("Current requirement type");
		expect(panel.text()).toContain("Works");
		expect(w.find('[data-testid="pln-class-new-category"]').text()).toBe("Services");
	});

	it("does not offer the current type as a correction target", () => {
		const w = make(panelProps());
		const options = w.findAll('[data-testid="pln-class-new-type"] option').map((o) => o.text());
		expect(options).not.toContain("Works");
		expect(options).toContain("Non-consulting services");
	});

	it("keeps Save disabled until a different type and a real reason are given", async () => {
		const w = make(panelProps());
		expect(w.find('[data-testid="pln-class-save"]').attributes("disabled")).toBeDefined();

		const short = make(panelProps({ newType: "Goods", reason: "wrong" }));
		expect(short.find('[data-testid="pln-class-save"]').attributes("disabled")).toBeDefined();

		const ok = make(
			panelProps({
				newType: "Non-consulting services",
				reason: "The requirement is for a managed technical service and contains no construction work.",
			}),
		);
		expect(ok.find('[data-testid="pln-class-save"]').attributes("disabled")).toBeUndefined();
	});

	it("names the consequence for a source already in a draft purchase", () => {
		const w = make({
			panel: row({
				affected: {
					recovery: "dissolve_and_reform",
					draft_items: [{ plan_item_id: "PPI-MOH-2027-044", plan_version_status: "Draft" }],
					governed_items: [],
					locked_items: [],
				},
			}),
		});
		expect(w.find('[data-testid="pln-class-impact"]').text()).toContain(
			"This requirement is already in a draft purchase. The purchase will need to be rebuilt",
		);
		expect(w.find('[data-testid="pln-class-impact"]').text()).toContain(
			"The accepted departmental submission will not change.",
		);
	});

	it("names the consequence for a source in a plan already under governance", () => {
		const w = make({
			panel: row({
				affected: {
					recovery: "plan_successor",
					draft_items: [],
					governed_items: [{ plan_item_id: "PPI-MOH-2027-021", plan_version_status: "Active" }],
					locked_items: [],
				},
			}),
		});
		expect(w.find('[data-testid="pln-class-impact"]').text()).toContain("That plan stays exactly as it is");
	});

	it("says plainly that a scope-locked purchase cannot be reclassified through Planning", () => {
		const w = make({
			panel: row({
				affected: {
					recovery: "downstream_owner",
					draft_items: [],
					governed_items: [],
					locked_items: [{ plan_item_id: "PPI-MOH-2027-033", plan_version_status: "Active" }],
				},
			}),
		});
		const impact = w.find('[data-testid="pln-class-impact"]').text();
		expect(impact).toContain("already in procurement and cannot be reclassified through Planning");
		expect(impact).toContain("it has not changed the existing procurement");
	});

	it("says an unused source simply becomes available corrected", () => {
		const w = make(panelProps());
		expect(w.find('[data-testid="pln-class-impact"]').text()).toContain(
			"Nothing has used this requirement yet",
		);
	});
});

describe("ClassificationEvidenceScreen — affected-work notices", () => {
	it("names the affected purchase and its recovery route on the record itself", () => {
		const corrected = row({
			classification: classification({ corrected: true, corrections: [{ previous_requirement_type: "Works", previous_procurement_category: "Works", reason: "r" }] }),
			affected: {
				recovery: "dissolve_and_reform",
				draft_items: [{ plan_item_id: "PPI-MOH-2027-044", plan_version_status: "Draft" }],
				governed_items: [],
				locked_items: [],
			},
		});
		const w = make({ evidence: evidence({ rows: [corrected] }) });
		const notice = w.find('[data-testid="pln-class-affected"]');
		expect(notice.text()).toContain("PPI-MOH-2027-044");
		expect(notice.text()).toContain("Remove that purchase and add its requirements again");
	});

	it("raises a scope-locked notice at critical weight", () => {
		const corrected = row({
			classification: classification({ corrected: true, corrections: [{ previous_requirement_type: "Works", previous_procurement_category: "Works", reason: "r" }] }),
			affected: {
				recovery: "downstream_owner",
				draft_items: [],
				governed_items: [],
				locked_items: [{ plan_item_id: "PPI-MOH-2027-033", plan_version_status: "Active" }],
			},
		});
		const w = make({ evidence: evidence({ rows: [corrected] }) });
		const notice = w.find('[data-testid="pln-class-affected"]');
		expect(notice.classes()).toContain("is-critical");
		expect(notice.text()).toContain("already has an authorised requisition");
	});
});
