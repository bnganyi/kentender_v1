<script setup>
// ANL §10A.3 — "Time between key steps": a range strip with value columns. Columns, left to right: Step,
// the chart, Completed, Median, Shortest, Longest. The chart draws a line from the shortest to the longest
// value with a marker at the median, all on one shared axis (0 to `axis.max` days, ticks the server names).
// Geometry is each number over `axis.max`; every word and number shown is the server's text.
import { computed } from "vue";
import ChartTable from "./ChartTable.vue";
import { percent } from "./chartUtil.js";

const props = defineProps({
	// the six column headings, the second (the chart) usually empty: ["Step", "", "Completed", "Median", "Shortest", "Longest"]
	columns: { type: Array, required: true },
	// [{ key, label, completed (text), median: { value, text }, shortest: { value, text }, longest: { value, text } }]
	rows: { type: Array, required: true },
	// { max: number, ticks: [{ value, label }] }
	axis: { type: Object, required: true },
	caption: { type: String, default: "" },
	medianLabel: { type: String, default: "" },
	rangeLabel: { type: String, default: "" },
	title: { type: String, default: "" },
});

const pos = (value) => percent(value, props.axis.max);
const lineStyle = (row) => ({
	left: pos(row.shortest.value),
	width: "max(6px," + percent(row.longest.value - row.shortest.value, props.axis.max) + ")",
});
const tickClass = (index) => ({ "is-first": index === 0, "is-last": index === props.axis.ticks.length - 1 });
const headers = computed(() => props.columns.filter((_, i) => i !== 1));
const tableRows = computed(() => props.rows.map((row) => [row.label, String(row.completed), row.median.text, row.shortest.text, row.longest.text]));
</script>

<template>
	<div class="kt-anl-chart" data-chart="range-strip">
		<div class="kt-anl-range" aria-hidden="true">
			<div class="kt-anl-range-row is-head">
				<span v-for="(heading, i) in columns" :key="i" :class="{ 'kt-anl-num': i > 1 }">{{ heading }}</span>
			</div>
			<div v-for="row in rows" :key="row.key" class="kt-anl-range-row">
				<span>{{ row.label }}</span>
				<span class="kt-anl-range-track">
					<span class="kt-anl-range-base"></span>
					<span class="kt-anl-range-line" :style="lineStyle(row)"></span>
					<span class="kt-anl-range-median" :style="{ left: pos(row.median.value) }"></span>
				</span>
				<span class="kt-anl-num">{{ row.completed }}</span>
				<span class="kt-anl-num is-median">{{ row.median.text }}</span>
				<span class="kt-anl-num">{{ row.shortest.text }}</span>
				<span class="kt-anl-num">{{ row.longest.text }}</span>
			</div>
			<div class="kt-anl-range-row is-axis">
				<span></span>
				<span class="kt-anl-range-axis">
					<span v-for="(tick, i) in axis.ticks" :key="tick.value" :class="tickClass(i)" :style="{ left: pos(tick.value) }">{{ tick.label }}</span>
				</span>
				<span></span>
				<span></span>
				<span></span>
				<span></span>
			</div>
		</div>
		<div v-if="caption || medianLabel || rangeLabel" class="kt-anl-range-note" aria-hidden="true">
			<p v-if="caption" class="kt-anl-caption">{{ caption }}</p>
			<span v-if="medianLabel"><i class="is-median"></i>{{ medianLabel }}</span>
			<span v-if="rangeLabel"><i class="is-range"></i>{{ rangeLabel }}</span>
		</div>
		<ChartTable :caption="title || caption" :headers="headers" :rows="tableRows" />
	</div>
</template>
