// PLN-CHG-001 v1.23 §10.11 — SourceEvidenceScreen component tests (U12).
//
// What was asked for, who is paying, who certified and accepted, then the
// identifiers. A newer accepted requirement is announced but never substituted,
// and a historical plan keeps its exact snapshot with no business control.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import SourceEvidenceScreen from "./SourceEvidenceScreen.vue";

function evidence(overrides = {}) {
	return {
		outcome: "OK",
		task: "PGT-0001",
		plan_reference: "PLN-MOH-2027-001",
		version_number: 1,
		plan_item_id: "PPI-MOH-2027-033",
		title: "Clinical training laptops for digital health rollout",
		description: "Provide the laptops required for clinical workforce training in the national digital-health rollout.",
		expected_operational_result: "Clinical training teams can use the common digital-health platform during training.",
		quantity_number: "100",
		unit_label: "Each",
		required_by_display: "31 Dec 2027",
		source_origin: "Accepted Departmental Need",
		department: "Human Resources Management and Development",
		need_reference: "NDS-MOH-2027-0003",
		need_revision_number: 2,
		departmental_plan_reference: "DPP-MOH-HRMD-2027-001",
		submission_number: 1,
		dpp_entry_id: "DPPE-MOH-HRMD-2027-001",
		budget_line_name: "Digital health workforce development",
		budget_line_reference: "MOH-BL-HWD-2027",
		planning_amount_display: "KES 20,000,000",
		certification_status: "Certified",
		certified: { actor_name: "Dr Peter Kimani", capacity: "Head of User Department", display: "25 Nov 2026, 11:00 EAT", attestation_text: "" },
		procurement_disposition: "Proceeding",
		accepted_for_planning: { actor_name: "Mercy Kilonzo", display: "27 Nov 2026, 14:05 EAT" },
		need_accepted: null,
		has_newer_revision: false,
		newer_revision_number: null,
		historical: false,
		current_plan_route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
		back_route: ["procurement-planning", "review", "PGT-0001"],
		...overrides,
	};
}

const make = (overrides) => mount(SourceEvidenceScreen, { props: { evidence: evidence(overrides) } });

describe("SourceEvidenceScreen — U12 BASE", () => {
	it("leads with the requirement and its acceptance status", () => {
		const w = make();
		expect(w.find('[data-testid="src-title"]').text()).toBe("Departmental requirement");
		const context = w.find('[data-testid="src-context"]');
		expect(context.text()).toContain("NDS-MOH-2027-0003");
		expect(context.text()).toContain("2");
		expect(context.text()).toContain("Accepted for planning");
	});

	it("shows the six requirement facts, with quantity and unit apart", () => {
		const text = make().find('[data-testid="src-requirement"]').text();
		expect(text).toContain("Clinical training laptops for digital health rollout");
		expect(text).toContain("Provide the laptops required for clinical workforce training");
		expect(text).toContain("Clinical training teams can use the common digital-health platform");
		expect(text).toContain("100");
		expect(text).toContain("Each");
		expect(text).toContain("31 Dec 2027");
		// Never "100 each" as one blob.
		expect(text).not.toContain("100 each");
	});

	it("names the budget line and what it is for, separately", () => {
		const text = make().find('[data-testid="src-funding"]').text();
		expect(text).toContain("Human Resources Management and Development");
		expect(text).toContain("Digital health workforce development");
		expect(text).toContain("MOH-BL-HWD-2027");
		expect(text).toContain("KES 20,000,000");
	});

	it("shows who certified in what capacity, and who accepted it", () => {
		const text = make().find('[data-testid="src-certification"]').text();
		expect(text).toContain("Certified");
		expect(text).toContain("Dr Peter Kimani");
		expect(text).toContain("Head of User Department");
		expect(text).toContain("25 Nov 2026, 11:00 EAT");
		expect(text).toContain("Proceeding");
		expect(text).toContain("Mercy Kilonzo");
		expect(text).toContain("27 Nov 2026, 14:05 EAT");
	});

	it("omits the capacity rather than guessing it", () => {
		const w = make({ certified: { actor_name: "Dr Peter Kimani", capacity: "", display: "25 Nov 2026, 11:00 EAT" } });
		expect(w.find('[data-testid="src-certification"]').text()).not.toContain("Capacity");
	});

	it("keeps the identifiers closed and offers no mutation", () => {
		const w = make();
		expect(w.find('[data-testid="src-record-details"]').attributes("open")).toBeUndefined();
		expect(w.find('[data-testid="src-record-details"]').text()).toContain("DPPE-MOH-HRMD-2027-001");
		expect(w.findAll("input")).toHaveLength(0);
		expect(w.findAll("textarea")).toHaveLength(0);
	});

	it("returns to the review it was opened from, above and below", async () => {
		const w = make();
		await w.find('[data-testid="src-back-top"]').trigger("click");
		await w.find('[data-testid="src-back-bottom"]').trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["procurement-planning", "review", "PGT-0001"]);
		expect(w.emitted("navigate")[1][0]).toEqual(["procurement-planning", "review", "PGT-0001"]);
	});
});

describe("SourceEvidenceScreen — U12-NEWER-SOURCE", () => {
	it("announces the newer requirement without replacing a single value", () => {
		const w = make({ has_newer_revision: true, newer_revision_number: 3 });
		const notice = w.find('[data-testid="src-newer-notice"]');
		expect(notice.text()).toContain("Revision 3");
		expect(notice.text()).toContain("The plan was reviewed on Revision 2");
		// The pinned evidence is untouched.
		expect(w.find('[data-testid="src-context"]').text()).toContain("2");
		expect(w.find('[data-testid="src-requirement"]').text()).toContain("100");
		expect(w.find('[data-testid="src-view-newer"]').exists()).toBe(true);
	});
});

describe("SourceEvidenceScreen — U12-HISTORICAL-PLAN", () => {
	it("says it is read only and offers the current plan, keeping the snapshot", () => {
		const w = make({ historical: true });
		expect(w.find('[data-testid="src-historical"]').text()).toContain("Historical plan — read only");
		expect(w.find('[data-testid="src-view-current"]').text()).toBe("View current plan");
		// Every value stays the exact historical snapshot.
		expect(w.find('[data-testid="src-requirement"]').text()).toContain("100");
		expect(w.find('[data-testid="src-funding"]').text()).toContain("KES 20,000,000");
	});
});

describe("SourceEvidenceScreen — U12-UNAVAILABLE", () => {
	it("says so plainly and offers the two things the reader can do", () => {
		const w = mount(SourceEvidenceScreen, { props: { evidence: { outcome: "UNAVAILABLE", back_route: ["procurement-planning", "review", "PGT-0001"] } } });
		expect(w.find('[data-testid="src-unavailable"]').text()).toBe(
			"Departmental requirement evidence could not be loaded.",
		);
		expect(w.find('[data-testid="src-retry"]').text()).toBe("Try again");
		expect(w.find('[data-testid="src-back-bottom"]').text()).toBe("Return to plan review");
		// No half-rendered evidence behind the failure.
		expect(w.find('[data-testid="src-requirement"]').exists()).toBe(false);
	});
});

describe("SourceEvidenceScreen — a direct departmental requirement", () => {
	it("says what it is instead of showing an empty Need field", () => {
		const w = make({ source_origin: "Direct requirement", need_reference: "", need_revision_number: null });
		const context = w.find('[data-testid="src-context"]').text();
		expect(context).toContain("Direct departmental requirement");
		expect(context).not.toContain("Revision");
	});
});
