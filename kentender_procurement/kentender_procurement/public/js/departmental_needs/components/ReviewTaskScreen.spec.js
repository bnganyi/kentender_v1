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
		const w = make({ permitted: [], makerCheckerBlocked: true });
		expect(w.find('[data-testid="nds-review-changed"]').exists()).toBe(false);
		expect(w.text()).toContain("You submitted this revision, so it must be decided by another Head of User Department.");
	});
});
