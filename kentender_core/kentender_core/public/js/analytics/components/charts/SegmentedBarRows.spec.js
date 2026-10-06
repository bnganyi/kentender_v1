// ANL §10A.3 waiting bands, §10A.7 "Coverage by Plan item" and "Coverage by department".
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import SegmentedBarRows from "./SegmentedBarRows.vue";
import { DEPARTMENTS, PLAN_ITEMS, PLAN_LEGEND, WAITING_LEGEND, WAITING_ROWS } from "./fixtures.js";

const widthsOf = (wrapper) => wrapper.findAll(".kt-anl-segrow-bar").map((n) => n.element.style.width);
const tableRows = (wrapper) => wrapper.findAll("table.sr-only tbody tr").map((tr) => tr.findAll("th,td").map((n) => n.text()));

describe("SegmentedBarRows — waiting bands", () => {
	const wrapper = () => mount(SegmentedBarRows, { props: { rows: WAITING_ROWS, variant: "bands", legend: WAITING_LEGEND, title: "Outstanding matters by waiting time" } });

	it("shows a shared legend of the four bands in band order, labels only", () => {
		expect(wrapper().findAll(".kt-anl-legend > span").map((n) => n.text())).toEqual(["0–7 days", "8–30 days", "31–90 days", "Over 90 days"]);
	});

	it("sizes each row against the largest row total (1 of 4, 4 of 4) and writes the counts inside the bars", () => {
		const w = wrapper();
		expect(widthsOf(w)).toEqual(["25%", "100%"]);
		expect(w.findAll(".kt-anl-seg > span").map((n) => n.text())).toEqual(["1", "3", "1"]);
		expect(w.findAll(".kt-anl-segrow-label").map((n) => n.text())).toEqual(["Requisitions", "Tender proceedings"]);
	});

	it("uses the sequential ramp in its own hue, never a categorical tone", () => {
		const classes = wrapper().findAll(".kt-anl-seg > span").map((n) => n.classes().find((c) => c.startsWith("is-")));
		expect(classes).toEqual(["is-seq-1", "is-seq-1", "is-seq-2"]);
	});

	it("exposes row, band and count in a hidden table", () => {
		expect(tableRows(wrapper())).toEqual([
			["Requisitions", "0–7 days", "1"],
			["Tender proceedings", "0–7 days", "3"],
			["Tender proceedings", "8–30 days", "1"],
		]);
	});
});

describe("SegmentedBarRows — coverage by Plan item", () => {
	const wrapper = () => mount(SegmentedBarRows, { props: { rows: PLAN_ITEMS, variant: "items", legend: PLAN_LEGEND, title: "Coverage by Plan item" } });

	it("orders rows as given, largest first, and scales widths to the largest item", () => {
		const w = wrapper();
		expect(w.findAll(".kt-anl-segrow-label").map((n) => n.text())).toEqual(["Servers", "Clinic equipment", "Network switches", "Monitors", "IT peripherals", "Printers", "Office desks"]);
		expect(widthsOf(w)).toEqual(["100%", "48%", "36%", "30%", "26%", "20%", "14%"]);
	});

	it("states the value of each segment as text and mutes the not-yet-covered amounts", () => {
		const values = wrapper().findAll(".kt-anl-segrow-values");
		expect(values.map((v) => v.findAll("span").map((n) => n.text()))).toEqual([
			["Covered KES 25,000,000"],
			["Not yet covered KES 12,000,000"],
			["Covered KES 8,000,000", "Not yet covered KES 1,000,000"],
			["Covered KES 7,500,000"],
			["Covered KES 6,500,000"],
			["Covered KES 5,000,000"],
			["Covered KES 3,500,000"],
		]);
		expect(values[2].findAll("span.is-muted").map((n) => n.text())).toEqual(["Not yet covered KES 1,000,000"]);
	});

	it("draws no segment inside the bars and uses the paired tones", () => {
		const w = wrapper();
		expect(w.findAll(".kt-anl-seg > span").every((n) => n.text() === "")).toBe(true);
		expect(w.findAll(".kt-anl-seg > span")[1].classes()).toContain("is-pair-tint");
	});
});

describe("SegmentedBarRows — coverage by department", () => {
	const wrapper = () => mount(SegmentedBarRows, { props: { rows: DEPARTMENTS, variant: "stacked", legend: PLAN_LEGEND, title: "Coverage by department" } });

	it("scales to the larger department and writes each end label", () => {
		const w = wrapper();
		expect(widthsOf(w)).toEqual(["100%", "48.91%"]);
		expect(w.findAll(".kt-anl-segrow-values b").map((n) => n.text())).toEqual(["74%", "96%"]);
	});

	it("states covered and not-yet-covered values for each department", () => {
		const values = wrapper().findAll(".kt-anl-segrow-values");
		expect(values[0].findAll("span").map((n) => n.text())).toEqual(["Covered KES 34,000,000", "Not yet covered KES 12,000,000"]);
		expect(values[1].findAll("span").map((n) => n.text())).toEqual(["Covered KES 21,500,000", "Not yet covered KES 1,000,000"]);
	});

	it("adds the end label to the hidden table", () => {
		const w = wrapper();
		expect(w.findAll("table.sr-only thead th").map((n) => n.text())).toEqual(["Item", "Segment", "Value", "Note"]);
		expect(tableRows(w)[0]).toEqual(["Digital Health", "Covered", "KES 34,000,000", "74%"]);
		expect(tableRows(w)[1]).toEqual(["Digital Health", "Not yet covered", "KES 12,000,000", ""]);
	});
});
