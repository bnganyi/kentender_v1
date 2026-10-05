<script setup>
// ANL §10A.1 rule 4 — vertical grouped bars by calendar month: always the twelve slots the server sends
// (`Jul 2026` to `Jun 2027 (to date)`), one bar per series in a slot. A month with a zero (or no) value
// shows no bar and no value label. Bar height is its count over the largest count (or `axisMax`) times a
// fixed plot height: geometry only. The axis shows the server's `axisLines` (for example ["Jul", "2026"]),
// falling back to the full label; the table always carries the full label.
import { computed } from "vue";
import ChartLegend from "./ChartLegend.vue";
import ChartTable from "./ChartTable.vue";
import { t, toneClass } from "./chartUtil.js";

const PLOT_HEIGHT = 90;

const props = defineProps({
	// twelve of { key, label, axisLines?: string[], values: { [seriesKey]: number | { count, text? } } }
	slots: { type: Array, required: true },
	// [{ key, label, tone }] in legend order
	series: { type: Array, required: true },
	// show the legend (default: only when there is more than one series)
	legend: { type: Boolean, default: null },
	axisMax: { type: Number, default: null },
	title: { type: String, default: "" },
	// [month heading] — one more heading per series follows, taken from the series labels
	tableHeaders: { type: Array, default: null },
});

const cell = (slot, series) => {
	const value = slot.values ? slot.values[series.key] : undefined;
	const count = value && typeof value === "object" ? value.count : value;
	const text = value && typeof value === "object" && value.text ? String(value.text) : count === undefined || count === null ? "" : String(count);
	return { count: Number(count) > 0 ? Number(count) : 0, text };
};
const full = computed(() => props.axisMax || Math.max(0, ...props.slots.flatMap((slot) => props.series.map((series) => cell(slot, series).count))));
const barWidth = computed(() => (props.series.length >= 3 ? 40 / props.series.length : 16));
const showLegend = computed(() => (props.legend === null ? props.series.length > 1 : props.legend));
const bars = (slot) =>
	props.series
		.map((series) => ({ series, ...cell(slot, series) }))
		.filter((bar) => bar.count > 0)
		.map((bar) => ({ ...bar, height: Math.round((bar.count / full.value) * PLOT_HEIGHT * 100) / 100 }));
const lines = (slot) => (slot.axisLines && slot.axisLines.length ? slot.axisLines : [slot.label]);
const headers = computed(() => [(props.tableHeaders && props.tableHeaders[0]) || t("Month"), ...props.series.map((series) => series.label)]);
const tableRows = computed(() => props.slots.map((slot) => [slot.label, ...props.series.map((series) => cell(slot, series).text || "0")]));
</script>

<template>
	<div class="kt-anl-chart" data-chart="monthly-grouped-bars">
		<ChartLegend v-if="showLegend" :items="series" aria-hidden="true" />
		<div class="kt-anl-vbars" aria-hidden="true">
			<div v-for="slot in slots" :key="slot.key" class="kt-anl-vbars-slot">
				<div v-for="bar in bars(slot)" :key="bar.series.key" class="kt-anl-vbars-bar" :style="{ width: barWidth + 'px' }">
					<b>{{ bar.text }}</b>
					<span :class="toneClass(bar.series.tone)" :style="{ height: bar.height + 'px' }"></span>
				</div>
			</div>
		</div>
		<div class="kt-anl-vbars-axis" aria-hidden="true">
			<span v-for="slot in slots" :key="slot.key"><template v-for="(line, i) in lines(slot)" :key="i"><br v-if="i > 0" />{{ line }}</template></span>
		</div>
		<ChartTable :caption="title" :headers="headers" :rows="tableRows" />
	</div>
</template>
