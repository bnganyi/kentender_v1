// NDS-DES-14-REVIEW-CHANGED — literal copy this component renders, ported
// class-for-class from NDS Artboards.dc.html. The design-fidelity gate's
// landmark check sees the "Refresh" button but not the notice sentence
// itself; pinned here instead.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ReviewTaskScreen from "./ReviewTaskScreen.vue";

function baseProps(overrides = {}) {
	return {
		need: { need_reference: "NDS-MOH-2027-0002" },
		revision: { revision_number: 1, title: "Digital health workforce certification programme" },
		acceptedRevision: {},
		scope: { organisation_unit: "Digital Health", financial_year: "FY 2027/28" },
		requesterLabel: "Grace Wanjiku",
		openedAt: "2026-11-24T10:00:00",
		taskType: "Initial acceptance",
		permitted: ["accept", "return", "decline"],
		makerCheckerBlocked: false,
		errorSummary: "",
		pending: false,
		...overrides,
	};
}

const make = (overrides) => mount(ReviewTaskScreen, { props: baseProps(overrides) });

describe("ReviewTaskScreen — NDS-DES-14-REVIEW-CHANGED", () => {
	it("names the stale result and offers Refresh once nothing is left to decide", () => {
		const w = make({ permitted: [] });
		const notice = w.get('[data-testid="nds-review-changed"]');
		expect(notice.text()).toContain("This review has already changed. Refresh to see the current result.");
		expect(w.get('[data-testid="nds-review-refresh"]').text()).toBe("Refresh");
		expect(w.find('[data-testid="nds-decision-accept"]').exists()).toBe(false);
		expect(w.find('[data-testid="nds-decision-return"]').exists()).toBe(false);
		expect(w.find('[data-testid="nds-decision-decline"]').exists()).toBe(false);
	});

	it("emits refresh when the button is clicked", async () => {
		const w = make({ permitted: [] });
		await w.get('[data-testid="nds-review-refresh"]').trigger("click");
		expect(w.emitted("refresh")).toHaveLength(1);
	});

	it("does not show the stale notice while a real decision is still available", () => {
		const w = make({ permitted: ["accept"] });
		expect(w.find('[data-testid="nds-review-changed"]').exists()).toBe(false);
		expect(w.find('[data-testid="nds-decision-accept"]').exists()).toBe(true);
	});

	it("does not show the stale notice for the maker-checker block either (a different, already-covered reason)", () => {
		// NDS-CHG-001 v1.15 §5.5 — the maker's reason is the next step's
		// sentence, drawn once in the guidance region.
		const w = make({
			permitted: [],
			makerCheckerBlocked: true,
			nextStep: {
				kind: "waiting",
				label: "Waiting on someone",
				headline: "Waiting for another Head of User Department to review this requirement",
				sentence: "You submitted this revision, so it must be decided by another Head of User Department.",
				stage: "review",
				holder: null,
				since: null,
				blockers: [],
				fixes: [],
				primary_action: "",
			},
		});
		expect(w.find('[data-testid="nds-review-changed"]').exists()).toBe(false);
		const region = w.get('[data-testid="nds-guidance"]');
		expect(region.text()).toContain("Waiting for another Head of User Department to review this requirement");
		expect(w.text().split("You submitted this revision, so it must be decided by another Head of User Department.").length - 1).toBe(1);
	});
});

// NDS-CHG-001 v1.17 §11.19 / NDS17-AC-007 — the estimate is read before the decision area,
// and a changed estimate leads the update comparison.
describe("ReviewTaskScreen — Estimated cost", () => {
	it("shows the estimate beneath the requirement, before the decision actions", () => {
		const w = make({ revision: { revision_number: 1, title: "Certification", description: "A programme to certify staff.", expected_operational_result: "Staff are certified.", estimated_total_cost: "12000000", estimated_total_cost_label: "KES 12,000,000" } });
		const html = w.html();
		expect(w.get('[data-testid="nds-estimated-cost-line"]').text()).toBe("Estimated costKES 12,000,000");
		expect(html.indexOf("nds-estimated-cost-line")).toBeLessThan(html.indexOf("nds-decision-accept"));
	});

	it("says No estimate recorded for a revision that predates the field", () => {
		const w = make({ revision: { revision_number: 1, title: "Old", description: "An older requirement.", expected_operational_result: "Done.", estimated_total_cost: null, estimated_total_cost_label: "" } });
		expect(w.get('[data-testid="nds-estimated-cost-line"]').text()).toContain("No estimate recorded");
	});

	it("lists a changed estimate first in the update comparison", () => {
		const w = make({
			taskType: "Successor acceptance",
			acceptedRevision: { name: "R1", revision_number: 1, title: "Infra", required_by_date: "2027-08-31", estimated_total_cost: "80000000", estimated_total_cost_label: "KES 80,000,000" },
			revision: { name: "R2", revision_number: 2, title: "Infra", required_by_date: "2027-09-15", estimated_total_cost: "85000000", estimated_total_cost_label: "KES 85,000,000" },
		});
		const rows = w.findAll("tbody tr").map((r) => r.text());
		expect(rows[0]).toContain("Estimated cost");
		expect(rows[0]).toContain("KES 80,000,000");
		expect(rows[0]).toContain("KES 85,000,000");
		expect(rows[1]).toContain("Required by");
	});

	it("shows no estimate row when it did not change", () => {
		const w = make({
			taskType: "Successor acceptance",
			acceptedRevision: { name: "R1", revision_number: 1, title: "Infra", required_by_date: "2027-08-31", estimated_total_cost: "80000000", estimated_total_cost_label: "KES 80,000,000" },
			revision: { name: "R2", revision_number: 2, title: "Infra", required_by_date: "2027-09-15", estimated_total_cost: "80000000", estimated_total_cost_label: "KES 80,000,000" },
		});
		expect(w.findAll("tbody tr").some((r) => r.text().includes("Estimated cost"))).toBe(false);
	});
});
