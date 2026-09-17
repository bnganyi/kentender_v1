// PLN-CHG-001 v1.23 §10.5 — DppValidationScreen component tests (U06).
//
// Two rules carry most of the weight here. Requirement type is the only
// classification input, and Category is derived text the client never sends.
// And when the evidence for a positive decision is the thing that is wrong,
// Accept goes away but Return must not — otherwise the plan is stuck.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import DppValidationScreen from "./DppValidationScreen.vue";

const TYPES = [
	{ requirement_type: "Consulting services", procurement_category: "Services" },
	{ requirement_type: "Goods", procurement_category: "Goods" },
	{ requirement_type: "Non-consulting services", procurement_category: "Services" },
	{ requirement_type: "Works", procurement_category: "Works" },
];

const INFRASTRUCTURE = {
	entry_id: "DPPE-MOH-DHI-2027-001",
	title: "National digital health infrastructure upgrade",
	quantity_number: "1",
	unit_label: "Programme",
	required_by_display: "31 Aug 2027",
	amount_display: "KES 80,000,000",
	budget_line_display: "MOH-BL-DHI-2027",
	not_proceeding: false,
	not_proceeding_reason: "",
};

const LAPTOPS = {
	entry_id: "DPPE-MOH-DHI-2027-002",
	title: "Clinical deployment laptops for digital health rollout",
	quantity_number: "150",
	unit_label: "Each",
	required_by_display: "31 Dec 2027",
	amount_display: "KES 30,000,000",
	budget_line_display: "MOH-BL-HWD-2027",
	not_proceeding: false,
	not_proceeding_reason: "",
};

function task(overrides = {}) {
	return {
		outcome: "OK",
		task: "DPPT-MOH-DHI-2027-001-V1",
		status: "Open",
		can_decide: true,
		maker_checker_blocked: false,
		header: {
			reference_line: "DPP-MOH-DHI-2027-001 · Submission 1",
			badge: "Awaiting validation",
			badge_kind: "pending",
		},
		context: {
			department: "Digital Health",
			financial_year: "FY 2027/28",
			submitted_by: "Julia Njeri",
			submitted_at: "25 Nov 2026, 10:30 EAT",
		},
		summary: {
			included_requirements: 2,
			included_cost_display: "KES 110,000,000",
			excluded_requirements: 0,
		},
		entries: [INFRASTRUCTURE, LAPTOPS],
		requirement_types: TYPES,
		stale_sources: [],
		certification: { text: "I certify that this plan records Digital Health's requirements for FY 2027/28." },
		...overrides,
	};
}

function make(props = {}) {
	return mount(DppValidationScreen, {
		props: { task: task(), classifications: {}, pending: false, ...props },
	});
}

describe("DppValidationScreen — U06 BASE", () => {
	it("leads with the certified content and the included/excluded summary", () => {
		const w = make();
		expect(w.find('[data-testid="pln-review-title"]').text()).toBe("Review Digital Health's departmental plan");
		expect(w.find('[data-testid="pln-review-context"]').text()).toContain("DPP-MOH-DHI-2027-001");
		expect(w.find('[data-testid="pln-review-context"]').text()).toContain("Awaiting Procurement review");
		expect(w.find('[data-testid="pln-review-certified"]').text()).toContain("Julia Njeri");
		const summary = w.find('[data-testid="pln-review-summary"]').text();
		expect(summary).toContain("Included requirements");
		expect(summary).toContain("KES 110,000,000");
		expect(summary).toContain("Excluded requirements");
	});

	it("says plainly what accepting does and does not do", () => {
		const w = make();
		expect(w.find('[data-testid="pln-review-consequence"]').text()).toContain(
			"It does not approve the Annual Procurement Plan.",
		);
	});
});

describe("DppValidationScreen — classification input", () => {
	it("offers only Requirement type, and derives Category from the selection", async () => {
		const w = make({ classifications: { [INFRASTRUCTURE.entry_id]: "Non-consulting services" } });
		const selects = w.findAll('[data-testid="pln-review-type"]');
		expect(selects).toHaveLength(2);
		// Category is text, never a control: a client cannot submit one (§4.4).
		const categories = w.findAll('[data-testid="pln-review-category"]');
		expect(categories[0].text()).toBe("Services");
		expect(categories[0].element.tagName).not.toBe("SELECT");
		expect(w.find('[data-testid="pln-review-helper"]').text()).toBe(
			"Choose the requirement type. Category is set automatically.",
		);
	});

	it("emits the entry and the selected type only", async () => {
		const w = make();
		await w.findAll('[data-testid="pln-review-type"]')[1].setValue("Goods");
		expect(w.emitted("set-classification")[0][0]).toEqual({
			entry_id: LAPTOPS.entry_id,
			requirement_type: "Goods",
		});
	});

	it("derives Works from Works and Services from either services type", async () => {
		const w = make({
			classifications: { [INFRASTRUCTURE.entry_id]: "Works", [LAPTOPS.entry_id]: "Consulting services" },
		});
		const categories = w.findAll('[data-testid="pln-review-category"]');
		expect(categories[0].text()).toBe("Works");
		expect(categories[1].text()).toBe("Services");
	});
});

describe("DppValidationScreen — U06-EXCLUDED", () => {
	it("shows an excluded row's reason and offers it no classification control", () => {
		const excluded = {
			...INFRASTRUCTURE,
			amount_display: "Not applicable",
			not_proceeding: true,
			not_proceeding_reason: "The department will pursue this requirement in a later annual planning cycle.",
		};
		const w = make({
			task: task({ entries: [excluded, LAPTOPS], summary: { included_requirements: 1, included_cost_display: "KES 30,000,000", excluded_requirements: 1 } }),
			classifications: { [LAPTOPS.entry_id]: "Goods" },
		});
		const row = w.find('[data-testid="pln-review-excluded"]');
		expect(row.text()).toContain("Not included this year");
		expect(row.text()).toContain("Not applicable");
		expect(row.text()).toContain("The department will pursue this requirement in a later annual planning cycle.");
		// One control, for the one included row.
		expect(w.findAll('[data-testid="pln-review-type"]')).toHaveLength(1);
		// An excluded row needs no classification, so Accept is available.
		expect(w.find('[data-testid="pln-review-accept"]').exists()).toBe(true);
	});
});

describe("DppValidationScreen — corrective actions stay available", () => {
	it("U06-CLASSIFICATION-MISSING: removes Accept, keeps Return, names the missing input", () => {
		const w = make({ classifications: { [LAPTOPS.entry_id]: "Goods" } });
		expect(w.find('[data-testid="pln-review-accept"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-review-return"]').attributes("disabled")).toBeUndefined();
		expect(w.find('[data-testid="pln-review-row-error"]').text()).toBe(
			"Select the requirement type before accepting this departmental plan.",
		);
	});

	it("U06-STALE-SOURCE: removes Accept, keeps Return, and shows the exact change", () => {
		const w = make({
			task: task({
				stale_sources: [
					{
						entry_id: INFRASTRUCTURE.entry_id,
						title: INFRASTRUCTURE.title,
						certified_revision_display: "Rev. 1 · certified 24 Nov 2026",
						current_revision_display: "Rev. 2 · updated 2 Dec 2026",
					},
				],
			}),
			classifications: { [INFRASTRUCTURE.entry_id]: "Works", [LAPTOPS.entry_id]: "Goods" },
		});
		expect(w.find('[data-testid="pln-review-stale"]').text()).toContain(
			"A source requirement changed after this submission was certified.",
		);
		expect(w.find('[data-testid="pln-review-stale-table"]').text()).toContain("Rev. 2 · updated 2 Dec 2026");
		expect(w.find('[data-testid="pln-review-accept"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-review-return"]').exists()).toBe(true);
	});

	it("U06-SEGREGATION: removes both decisions but keeps the content readable", () => {
		const w = make({ task: task({ maker_checker_blocked: true, can_decide: false }) });
		expect(w.find('[data-testid="pln-review-segregation"]').text()).toBe(
			"You cannot review a departmental plan you certified.",
		);
		expect(w.find('[data-testid="pln-review-accept"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-review-return"]').exists()).toBe(false);
		expect(w.findAll('[data-testid="pln-review-row"]')).toHaveLength(2);
	});
});
