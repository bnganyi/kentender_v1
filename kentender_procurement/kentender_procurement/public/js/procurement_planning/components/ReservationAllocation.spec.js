// PLN-CHG-001 v1.25 §5.5.3.1 / RES-IMP-001 — the plan-level Reservation
// allocation block (U07 base/ready, U11, U21), verified against the boards'
// canonical fixture: 30% of KES 130,000,000 eligible = KES 39,000,000;
// KES 50,000,000 Youth = 38.46%. The KES 160,000,000 Budget ceiling is a
// Funding fact and must never appear here.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ReservationAllocation from "./ReservationAllocation.vue";
import { BASE, READY } from "./ReservationAllocation.fixtures.js";

const labels = (el) => el.findAll(".kt-label").map((l) => l.text());

describe("ReservationAllocation", () => {
	it("leads with the result: remaining, required, qualifying, then share", () => {
		const w = mount(ReservationAllocation, { props: { block: READY } });
		expect(w.text()).toContain("Reservation allocation");
		const status = w.find('[data-testid="reservation-status"]');
		expect(status.text()).toBe("Required allocation met");
		expect(status.classes()).toContain("is-live");
		const result = w.find('[data-testid="reservation-result"]');
		expect(labels(result)).toEqual(["Remaining allocation", "Required allocation", "Planned qualifying allocation", "Qualifying share"]);
		expect(result.text()).toContain("KES 39,000,000");
		expect(result.text()).toContain("38.46%");
	});

	it("drops the share and flags attention while nothing qualifies (base scenario)", () => {
		const w = mount(ReservationAllocation, { props: { block: BASE } });
		expect(w.find('[data-testid="reservation-status"]').classes()).toContain("is-attention");
		expect(labels(w.find('[data-testid="reservation-result"]'))).toEqual(["Remaining allocation", "Required allocation", "Planned qualifying allocation"]);
		expect(w.find('[data-testid="reservation-result"]').text()).toContain("KES 39,000,000");
	});

	it("shows the calculation basis, the exact versions and every purchase with its reason", () => {
		const w = mount(ReservationAllocation, { props: { block: READY } });
		const basis = w.find('[data-testid="reservation-basis"]');
		expect(basis.text()).toContain("Eligible planned procurement");
		expect(basis.text()).toContain("KES 130,000,000");
		expect(basis.text()).toContain("30%");
		const scope = w.find('[data-testid="reservation-scope"]');
		expect(labels(scope)).toEqual(["Plan basis", "Rule version", "County requirement", "Mandatory restrictions"]);
		expect(scope.text()).toContain("PLN-MOH-2027-001, Version 1");
		expect(scope.text()).toContain("Reservation rules, Version 9");
		expect(scope.text()).toContain("Not applicable");
		const rows = w.findAll('[data-testid="reservation-items"] tbody tr');
		expect(rows).toHaveLength(2);
		expect(rows[1].text()).toContain("Included");
		expect(rows[1].text()).toContain("Counted: the reservation rule includes all planned procurement");
		expect(rows[1].text()).toContain("Youth");
		expect(rows[0].findAll("td")[5].classes()).toContain("is-zero");
		expect(rows[1].findAll("td")[5].classes()).not.toContain("is-zero");
		expect(w.text()).toContain("The approved budget is a separate funding ceiling, checked under Funding, and is not used here.");
		// Never a placeholder, never the Budget as the measure.
		expect(w.text()).not.toContain("Awaiting fixture");
		expect(w.text()).not.toContain("160,000,000");
		expect(w.text()).not.toContain("Budget basis");
	});

	it("hides the working under its own closed disclosure on the preparation screen", () => {
		const w = mount(ReservationAllocation, { props: { block: BASE, collapsible: true } });
		const details = w.find('[data-testid="reservation-details"]');
		expect(details.element.tagName).toBe("DETAILS");
		expect(details.classes()).toContain("kt-disclosure");
		expect(details.attributes("open")).toBeUndefined();
		expect(details.find(".kt-disclosure-title").text()).toBe("Reservation allocation details");
	});

	it("shows the working inline where an outer disclosure already hides it (review)", () => {
		const w = mount(ReservationAllocation, { props: { block: READY } });
		const details = w.find('[data-testid="reservation-details"]');
		expect(details.element.tagName).toBe("DIV");
		expect(details.find(".kt-disclosure-title").exists()).toBe(false);
	});
});
