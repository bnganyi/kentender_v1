// ANL §10A.1 rule 2 and §10A.3 — summary-strip bars, Plan coverage, and the §10A.9 funding bar.
import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import SegmentedBar from "./SegmentedBar.vue";
import { FUNDING, PLAN_COVERAGE, TENDER_STRIP } from "./fixtures.js";

const bar = (props) => mount(SegmentedBar, { props });
const parts = (wrapper) => wrapper.findAll(".kt-anl-seg > span");
const flexes = (wrapper) => parts(wrapper).map((n) => n.attributes("style").match(/flex:\s*([^;]+);/)[1].trim().replace(/\s+/g, " ").replace(/ 0px$/, " 0"));
const legend = (wrapper) => wrapper.findAll(".kt-anl-legend > span").map((n) => n.text().replace(/\s+/g, " "));

describe("SegmentedBar", () => {
	it("sizes the Tender summary strip segments 1 / 1 / 1 / 2 / 1 in the stated order", () => {
		const wrapper = bar({ segments: TENDER_STRIP, size: "xs", title: "Tender proceedings by stage" });
		expect(flexes(wrapper)).toEqual(["1 1 0", "1 1 0", "1 1 0", "2 1 0", "1 1 0"]);
		expect(parts(wrapper).map((n) => n.classes().find((c) => c.startsWith("is-cat")))).toEqual(["is-cat-1", "is-cat-2", "is-cat-3", "is-cat-4", "is-cat-5"]);
		expect(wrapper.get(".kt-anl-seg").classes()).toContain("is-xs");
	});

	it("gives a legend entry with label and value for every drawn segment, in order", () => {
		const wrapper = bar({ segments: TENDER_STRIP });
		expect(legend(wrapper)).toEqual(["Preparation 1", "Open 1", "Evaluation 1", "Award 2", "Closed 1"]);
	});

	it("writes Plan coverage with the server's amounts and the paired tones", () => {
		const wrapper = bar({ segments: PLAN_COVERAGE, title: "Plan coverage" });
		expect(flexes(wrapper)).toEqual(["55500000 1 0", "13000000 1 0"]);
		expect(legend(wrapper)).toEqual(["Covered by authorised requisitions KES 55,500,000", "Not yet covered KES 13,000,000"]);
		expect(parts(wrapper).map((n) => n.classes().find((c) => c.startsWith("is-pair")))).toEqual(["is-pair-strong", "is-pair-tint"]);
	});

	it("omits a zero segment and its legend entry unless keepZero names it", () => {
		const omitted = bar({ segments: FUNDING });
		expect(parts(omitted)).toHaveLength(2);
		expect(legend(omitted)).toEqual(["Reserved for requisitions KES 55,500,000", "Available to reserve KES 94,500,000"]);
	});

	it("keeps the named zero segment's legend entry but gives it no width (funding bar)", () => {
		const wrapper = bar({ segments: FUNDING, keepZero: "committed", title: "Funding position" });
		expect(parts(wrapper)).toHaveLength(2);
		expect(legend(wrapper)).toEqual(["Reserved for requisitions KES 55,500,000", "Committed to contracts KES 0", "Available to reserve KES 94,500,000"]);
		const rows = wrapper.findAll("table.sr-only tbody tr").map((tr) => tr.findAll("th,td").map((n) => n.text()));
		expect(rows).toEqual([
			["Reserved for requisitions", "KES 55,500,000"],
			["Committed to contracts", "KES 0"],
			["Available to reserve", "KES 94,500,000"],
		]);
	});

	it("accepts several keepZero keys", () => {
		const segments = [
			{ key: "a", label: "A", count: 0, tone: "cat-1" },
			{ key: "b", label: "B", count: 0, tone: "cat-2" },
			{ key: "c", label: "C", count: 3, tone: "cat-3" },
		];
		expect(legend(bar({ segments, keepZero: ["a", "b"] }))).toEqual(["A 0", "B 0", "C 3"]);
		expect(legend(bar({ segments }))).toEqual(["C 3"]);
	});

	it("writes values inside the segments only when asked", () => {
		expect(parts(bar({ segments: TENDER_STRIP })).map((n) => n.text())).toEqual(["", "", "", "", ""]);
		expect(parts(bar({ segments: TENDER_STRIP, inside: true })).map((n) => n.text())).toEqual(["1", "1", "1", "2", "1"]);
	});

	it("draws no legend when told not to, and still exposes the table", () => {
		const wrapper = bar({ segments: PLAN_COVERAGE, legend: false, title: "Plan coverage" });
		expect(wrapper.find(".kt-anl-legend").exists()).toBe(false);
		expect(wrapper.get("table.sr-only caption").text()).toBe("Plan coverage");
		expect(wrapper.findAll("table.sr-only tbody tr")).toHaveLength(2);
	});

	it("exposes the values as a hidden table in visual order and hides the picture from assistive technology", () => {
		const wrapper = bar({ segments: TENDER_STRIP, title: "Tender proceedings by stage" });
		const table = wrapper.get("table.sr-only");
		expect(table.findAll("thead th").map((n) => n.text())).toEqual(["Item", "Value"]);
		expect(table.findAll("tbody tr").map((tr) => tr.findAll("th,td").map((n) => n.text()))).toEqual([
			["Preparation", "1"], ["Open", "1"], ["Evaluation", "1"], ["Award", "2"], ["Closed", "1"],
		]);
		expect(wrapper.get(".kt-anl-seg").attributes("aria-hidden")).toBe("true");
		expect(wrapper.get(".kt-anl-legend").attributes("aria-hidden")).toBe("true");
	});

	it("has no interaction", async () => {
		const wrapper = bar({ segments: TENDER_STRIP });
		await wrapper.get(".kt-anl-seg > span").trigger("click");
		expect(wrapper.emitted("select")).toBeUndefined();
	});
});
