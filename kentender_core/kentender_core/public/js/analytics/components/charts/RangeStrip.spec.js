// ANL §10A.3 — "Time between key steps", rows T1 to T5, columns Step / chart / Completed / Median / Shortest / Longest.
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import RangeStrip from "./RangeStrip.vue";
import { RANGE_AXIS, RANGE_COLUMNS, RANGE_ROWS } from "./fixtures.js";

const strip = (props = {}) =>
	mount(RangeStrip, {
		props: { columns: RANGE_COLUMNS, rows: RANGE_ROWS, axis: RANGE_AXIS, caption: "Calendar days, last 12 months.", medianLabel: "Median", rangeLabel: "Shortest to longest", title: "Time between key steps", ...props },
	});
const dataRows = (wrapper) => wrapper.findAll(".kt-anl-range-row").filter((row) => !row.classes().includes("is-head") && !row.classes().includes("is-axis"));
const rounded = (value) => Math.round(parseFloat(value) * 100) / 100;

describe("RangeStrip", () => {
	it("has the six columns in order", () => {
		expect(strip().findAll(".kt-anl-range-row.is-head > span").map((n) => n.text())).toEqual(["Step", "", "Completed", "Median", "Shortest", "Longest"]);
	});

	it("writes the five steps and every value column as the server's text", () => {
		const rows = dataRows(strip()).map((row) => row.findAll(":scope > span").map((n) => (n.classes().includes("kt-anl-range-track") ? "chart" : n.text())));
		expect(rows).toEqual([
			["Requisition submitted to authorised", "chart", "6", "8.5 days", "6 days", "14 days"],
			["Requisition authorised to Tender started", "chart", "6", "3.5 days", "1 day", "5 days"],
			["Tender started to published", "chart", "5", "26 days", "21 days", "56 days"],
			["Bid opening complete to evaluation report sent", "chart", "2", "32.5 days", "28 days", "37 days"],
			["Evaluation report sent to AO decision recorded", "chart", "1", "13 days", "13 days", "13 days"],
		]);
	});

	it("places the line from shortest to longest and the median marker on the shared 0 to 60 axis", () => {
		const geometry = dataRows(strip()).map((row) => ({
			left: rounded(row.get(".kt-anl-range-line").element.style.left),
			marker: rounded(row.get(".kt-anl-range-median").element.style.left),
			width: row.get(".kt-anl-range-line").attributes("style").match(/width:\s*([^;]+);/)[1].replace(/\s+/g, ""),
		}));
		expect(geometry).toEqual([
			{ left: 10, marker: 14.17, width: "max(6px,13.33%)" },
			{ left: 1.67, marker: 5.83, width: "max(6px,6.67%)" },
			{ left: 35, marker: 43.33, width: "max(6px,58.33%)" },
			{ left: 46.67, marker: 54.17, width: "max(6px,15%)" },
			{ left: 21.67, marker: 21.67, width: "max(6px,0%)" },
		]);
	});

	it("draws the axis ticks every 10 days from 0 to 60, the first and last pinned to the edges", () => {
		const ticks = strip().findAll(".kt-anl-range-axis > span");
		expect(ticks.map((n) => n.text())).toEqual(["0", "10", "20", "30", "40", "50", "60"]);
		expect(ticks.map((n) => rounded(n.element.style.left))).toEqual([0, 16.67, 33.33, 50, 66.67, 83.33, 100]);
		expect(ticks[0].classes()).toContain("is-first");
		expect(ticks[6].classes()).toContain("is-last");
	});

	it("states the caption and the two legend labels", () => {
		const note = strip().get(".kt-anl-range-note");
		expect(note.get("p").text()).toBe("Calendar days, last 12 months.");
		expect(note.findAll(":scope > span").map((n) => n.text())).toEqual(["Median", "Shortest to longest"]);
	});

	it("draws a subset of steps (the Requisitions tab shows two) on the same axis", () => {
		const wrapper = strip({ rows: RANGE_ROWS.slice(0, 2) });
		expect(dataRows(wrapper)).toHaveLength(2);
		expect(wrapper.findAll(".kt-anl-range-axis > span")).toHaveLength(7);
	});

	it("exposes the same values as a hidden table without the empty chart column", () => {
		const table = strip().get("table.sr-only");
		expect(table.get("caption").text()).toBe("Time between key steps");
		expect(table.findAll("thead th").map((n) => n.text())).toEqual(["Step", "Completed", "Median", "Shortest", "Longest"]);
		const rows = table.findAll("tbody tr").map((tr) => tr.findAll("th,td").map((n) => n.text()));
		expect(rows[0]).toEqual(["Requisition submitted to authorised", "6", "8.5 days", "6 days", "14 days"]);
		expect(rows).toHaveLength(5);
		expect(strip().get(".kt-anl-range").attributes("aria-hidden")).toBe("true");
	});
});
