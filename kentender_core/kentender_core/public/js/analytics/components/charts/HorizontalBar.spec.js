// ANL §10A.4 — "Tenders by stage" (A1: 1 / 1 / 1 / 2 / 1) and §10A.6 "Requisitions by current state".
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import HorizontalBar from "./HorizontalBar.vue";
import { REQUISITION_STATES, TENDER_STAGES } from "./fixtures.js";

const stage = (props = {}) => mount(HorizontalBar, { props: { rows: TENDER_STAGES, valueHeading: "Authorised requisition value", title: "Tenders by stage", ...props } });
const widths = (wrapper) => wrapper.findAll(".kt-anl-hbars-track > span").map((bar) => bar.element.style.width);

describe("HorizontalBar", () => {
	it("draws one bar per stage, sized by count against the largest", () => {
		expect(widths(stage())).toEqual(["50%", "50%", "50%", "100%", "50%"]);
	});

	it("writes the label, count and the server's value text on every row, in order", () => {
		const wrapper = stage();
		expect(wrapper.findAll(".kt-anl-hbars-label").map((n) => n.text())).toEqual(TENDER_STAGES.map((r) => r.label));
		expect(wrapper.findAll(".kt-anl-hbars-count").map((n) => n.text())).toEqual(["1", "1", "1", "2", "1"]);
		expect(wrapper.findAll(".kt-anl-hbars-value").map((n) => n.text())).toEqual(["KES 6,500,000", "KES 8,000,000", "KES 3,500,000", "KES 12,500,000", "KES 25,000,000"]);
		expect(wrapper.find(".kt-anl-hbars-head").text()).toBe("Authorised requisition value");
	});

	it("colours each stage with its categorical tone class", () => {
		const classes = stage().findAll(".kt-anl-hbars-track > span").map((bar) => bar.classes().filter((c) => c.startsWith("is-")));
		expect(classes).toEqual([["is-cat-1"], ["is-cat-2"], ["is-cat-3"], ["is-cat-4"], ["is-cat-5"]]);
	});

	it("exposes the same values as a hidden table with a caption, in visual order", () => {
		const table = stage().get("table.sr-only");
		expect(table.get("caption").text()).toBe("Tenders by stage");
		const head = table.findAll("thead th").map((n) => n.text());
		expect(head).toEqual(["Item", "Count", "Authorised requisition value"]);
		const body = table.findAll("tbody tr").map((tr) => tr.findAll("th,td").map((n) => n.text()));
		expect(body).toEqual([
			["Tender preparation and publication", "1", "KES 6,500,000"],
			["Open for bids", "1", "KES 8,000,000"],
			["Evaluation", "1", "KES 3,500,000"],
			["Award", "2", "KES 12,500,000"],
			["Closed", "1", "KES 25,000,000"],
		]);
		expect(table.find("tbody th").attributes("scope")).toBe("row");
	});

	it("hides the visual rows from assistive technology so the table is read once", () => {
		expect(stage().get(".kt-anl-hbars").attributes("aria-hidden")).toBe("true");
	});

	it("marks the selected stage on the label and the bar, and nothing else", () => {
		const wrapper = stage({ selected: "award" });
		expect(wrapper.findAll(".kt-anl-hbars-label.is-selected").map((n) => n.text())).toEqual(["Award"]);
		expect(wrapper.findAll(".kt-anl-hbars-track > span.is-selected")).toHaveLength(1);
		expect(widths(wrapper)).toEqual(["50%", "50%", "50%", "100%", "50%"]);
	});

	it("emits select with the row key only when selectable", async () => {
		const quiet = stage();
		await quiet.findAll(".kt-anl-hbars-label")[3].trigger("click");
		expect(quiet.emitted("select")).toBeUndefined();

		const wrapper = stage({ selectable: true });
		expect(wrapper.get(".kt-anl-hbars").classes()).toContain("is-selectable");
		await wrapper.findAll(".kt-anl-hbars-label")[3].trigger("click");
		await wrapper.findAll(".kt-anl-hbars-track")[0].trigger("click");
		expect(wrapper.emitted("select")).toEqual([["award"], ["preparation"]]);
	});

	it("draws the Requisitions chart (1 and 6) against its own largest count", () => {
		const wrapper = mount(HorizontalBar, { props: { rows: REQUISITION_STATES, valueHeading: "Requisition value", title: "Requisitions by current state" } });
		expect(widths(wrapper)).toEqual(["16.67%", "100%"]);
		expect(wrapper.findAll(".kt-anl-hbars-value").map((n) => n.text())).toEqual(["KES 12,000,000 requested", "KES 55,500,000 authorised"]);
	});

	it("draws no header row without a value heading", () => {
		expect(stage({ valueHeading: "" }).find(".kt-anl-hbars-head").exists()).toBe(false);
	});

	it("draws a zero row as an empty bar with its count", () => {
		const wrapper = mount(HorizontalBar, { props: { rows: [{ key: "a", label: "A", count: 0, tone: "cat-1" }, { key: "b", label: "B", count: 2, tone: "cat-2" }] } });
		expect(widths(wrapper)).toEqual(["0%", "100%"]);
		expect(wrapper.findAll(".kt-anl-hbars-count").map((n) => n.text())).toEqual(["0", "2"]);
	});
});
