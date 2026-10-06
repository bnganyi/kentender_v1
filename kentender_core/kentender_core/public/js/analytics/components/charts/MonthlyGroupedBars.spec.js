// ANL §10A.1 rule 4 and §10A.4 — "Recorded each month": Apr 2027 Published 4; May 2027 Published 1;
// Jun 2027 (to date) Cancelled 1 and AO award decisions 1; every other month zero.
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import MonthlyGroupedBars from "./MonthlyGroupedBars.vue";
import { TENDER_MONTH_SERIES, TENDER_MONTH_VALUES, monthSlots } from "./fixtures.js";

const tender = (props = {}) =>
	mount(MonthlyGroupedBars, { props: { slots: monthSlots(TENDER_MONTH_VALUES), series: TENDER_MONTH_SERIES, title: "Recorded each month", ...props } });
const slotBars = (wrapper) => wrapper.findAll(".kt-anl-vbars-slot").map((slot) => slot.findAll(".kt-anl-vbars-bar").map((bar) => [bar.get("b").text(), bar.get("span").element.style.height]));

describe("MonthlyGroupedBars", () => {
	it("always draws twelve slots", () => {
		expect(tender().findAll(".kt-anl-vbars-slot")).toHaveLength(12);
		expect(tender().findAll(".kt-anl-vbars-axis > span")).toHaveLength(12);
	});

	it("draws bars only in Apr, May and Jun, with the value on each bar", () => {
		const bars = slotBars(tender());
		expect(bars.slice(0, 9).every((slot) => slot.length === 0)).toBe(true);
		expect(bars[9]).toEqual([["4", "90px"]]);
		expect(bars[10]).toEqual([["1", "22.5px"]]);
		expect(bars[11]).toEqual([["1", "22.5px"], ["1", "22.5px"]]);
	});

	it("shows no bar and no label for a zero month, even when the server sends the zero", () => {
		const slots = monthSlots({ "2027-04": { published: 4, cancelled: 0 }, "2027-05": { published: 0 } });
		const wrapper = tender({ slots });
		const bars = slotBars(wrapper);
		expect(bars[9]).toEqual([["4", "90px"]]);
		expect(bars[10]).toEqual([]);
		expect(wrapper.findAll(".kt-anl-vbars b").map((n) => n.text())).toEqual(["4"]);
	});

	it("colours the bars by series tone, in the series order within a month", () => {
		const jun = tender().findAll(".kt-anl-vbars-slot")[11].findAll(".kt-anl-vbars-bar > span");
		expect(jun.map((n) => n.classes().find((c) => c.startsWith("is-")))).toEqual(["is-cat-5", "is-cat-4"]);
	});

	it("labels the axis as the board does and the table with the full labels", () => {
		const wrapper = tender();
		expect(wrapper.findAll(".kt-anl-vbars-axis > span").map((n) => n.text())).toEqual(["Jul2026", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan2027", "Feb", "Mar", "Apr", "May", "Jun(to date)"]);
		expect(wrapper.findAll(".kt-anl-vbars-axis > span")[0].findAll("br")).toHaveLength(1);
		const rows = wrapper.findAll("table.sr-only tbody tr").map((tr) => tr.get("th").text());
		expect(rows[0]).toBe("Jul 2026");
		expect(rows[11]).toBe("Jun 2027 (to date)");
		expect(rows).toHaveLength(12);
	});

	it("writes the legend of three series by label, and the table carries one column per series", () => {
		const wrapper = tender();
		expect(wrapper.findAll(".kt-anl-legend > span").map((n) => n.text())).toEqual(["Published", "Cancelled", "AO award decisions"]);
		expect(wrapper.findAll("table.sr-only thead th").map((n) => n.text())).toEqual(["Month", "Published", "Cancelled", "AO award decisions"]);
		const body = wrapper.findAll("table.sr-only tbody tr").map((tr) => tr.findAll("th,td").map((n) => n.text()));
		expect(body[9]).toEqual(["Apr 2027", "4", "0", "0"]);
		expect(body[11]).toEqual(["Jun 2027 (to date)", "0", "1", "1"]);
		expect(wrapper.get("table.sr-only caption").text()).toBe("Recorded each month");
	});

	it("draws narrower bars for three series than for one or two", () => {
		const three = tender().get(".kt-anl-vbars-bar").element.style.width;
		expect(parseFloat(three)).toBeCloseTo(13.333, 2);
		const one = mount(MonthlyGroupedBars, { props: { slots: monthSlots({ "2026-11": { n: 2 } }), series: [{ key: "n", label: "Accepted for planning", tone: "cat-1" }] } });
		expect(one.get(".kt-anl-vbars-bar").element.style.width).toBe("16px");
	});

	it("draws a single series without a legend, as the Needs chart does", () => {
		const one = mount(MonthlyGroupedBars, { props: { slots: monthSlots({ "2026-11": { n: 2 } }), series: [{ key: "n", label: "Accepted for planning", tone: "cat-1" }], title: "Accepted for planning each month" } });
		expect(one.find(".kt-anl-legend").exists()).toBe(false);
		expect(slotBars(one)[4]).toEqual([["2", "90px"]]);
	});

	it("draws the Requisitions chart (6 and 6 in Mar, 1 in Jun) against its own tallest bar", () => {
		const wrapper = mount(MonthlyGroupedBars, {
			props: {
				slots: monthSlots({ "2027-03": { submitted: 6, authorised: 6 }, "2027-06": { submitted: 1 } }),
				series: [{ key: "submitted", label: "Submitted to Procurement", tone: "cat-3" }, { key: "authorised", label: "Authorised", tone: "cat-1" }],
			},
		});
		const bars = slotBars(wrapper);
		expect(bars[8]).toEqual([["6", "90px"], ["6", "90px"]]);
		expect(bars[11]).toEqual([["1", "15px"]]);
	});

	it("has no interaction", async () => {
		const wrapper = tender();
		await wrapper.get(".kt-anl-vbars-bar").trigger("click");
		expect(wrapper.emitted("select")).toBeUndefined();
	});
});
