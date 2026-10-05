// Writes each chart's rendered markup (A1 fixture values) to the file named by KT_ANALYTICS_DUMP, for
// scripts/analytics_chart_fidelity_check.mjs, which draws it beside the board's own markup in Chromium and
// compares the pixels. Skipped unless the variable is set, so the normal run writes nothing.
import { mount } from "@vue/test-utils";
import { describe, it } from "vitest";
import fs from "node:fs";
import HorizontalBar from "./HorizontalBar.vue";
import SegmentedBar from "./SegmentedBar.vue";
import SegmentedBarRows from "./SegmentedBarRows.vue";
import MonthlyGroupedBars from "./MonthlyGroupedBars.vue";
import RangeStrip from "./RangeStrip.vue";
import FromZeroBars from "./FromZeroBars.vue";
import * as F from "./fixtures.js";

describe.skipIf(!process.env.KT_ANALYTICS_DUMP)("chart markup dump", () => it("dumps", () => {
	const out = {};
	out.stage = mount(HorizontalBar, { props: { rows: F.TENDER_STAGES, valueHeading: "Authorised requisition value", title: "x" } }).element.outerHTML;
	out.stageSelected = mount(HorizontalBar, { props: { rows: F.TENDER_STAGES, valueHeading: "Authorised requisition value", selected: "award", title: "x" } }).element.outerHTML;
	out.monthly = mount(MonthlyGroupedBars, { props: { slots: F.monthSlots(F.TENDER_MONTH_VALUES), series: F.TENDER_MONTH_SERIES, title: "x" } }).element.outerHTML;
	out.range = mount(RangeStrip, { props: { columns: F.RANGE_COLUMNS, rows: F.RANGE_ROWS, axis: F.RANGE_AXIS, caption: "Calendar days, last 12 months.", medianLabel: "Median", rangeLabel: "Shortest to longest", title: "x" } }).element.outerHTML;
	out.bands = mount(SegmentedBarRows, { props: { rows: F.WAITING_ROWS, variant: "bands", legend: F.WAITING_LEGEND, title: "x" } }).element.outerHTML;
	out.coverage = mount(SegmentedBar, { props: { segments: F.PLAN_COVERAGE, title: "x" } }).element.outerHTML;
	out.strip = mount(SegmentedBar, { props: { segments: F.TENDER_STRIP, size: "xs", title: "x" } }).element.outerHTML;
	out.items = mount(SegmentedBarRows, { props: { rows: F.PLAN_ITEMS, variant: "items", legend: F.PLAN_LEGEND, title: "x" } }).element.outerHTML;
	out.dept = mount(SegmentedBarRows, { props: { rows: F.DEPARTMENTS, variant: "stacked", title: "x" } }).element.outerHTML;
	out.timing = mount(FromZeroBars, { props: { rows: F.INVITATION_TIMING, halfRange: 30, earlierLabel: "Earlier", laterLabel: "Later", caption: "Actual invitation date compared with the date approved in the Active Plan.", title: "x" } }).element.outerHTML;
	out.funding = mount(SegmentedBar, { props: { segments: F.FUNDING, keepZero: "committed", title: "x" } }).element.outerHTML;
	fs.writeFileSync(process.env.KT_ANALYTICS_DUMP, JSON.stringify(out));
}));
