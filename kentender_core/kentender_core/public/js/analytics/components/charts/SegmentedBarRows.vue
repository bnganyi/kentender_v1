<script setup>
// ANL §10A.1 and §10A.3/§10A.7 — several segmented bars on one scale, one per row. Three layouts, all
// drawn by the boards:
//   bands    "Outstanding matters by waiting time": a label column, then the bar with each count inside it;
//   items    "Coverage by Plan item": a label column, the bar, then a value column of segment values;
//   stacked  "Coverage by department": the label above its bar, the values and an end label beneath.
// A row's bar width is its total over the largest total (or `scaleMax`): geometry from the numbers given.
// A shared legend (labels only, in the stated order) may sit above the rows. Zero segments are not drawn
// and carry no value text.
import { computed } from "vue";
import ChartLegend from "./ChartLegend.vue";
import ChartTable from "./ChartTable.vue";
import { percent, t, textOf, toneClass } from "./chartUtil.js";

const props = defineProps({
	// [{ key, label, segments: [{ key, label, count, text?, tone, muted? }], endLabel? }]
	rows: { type: Array, required: true },
	variant: { type: String, default: "items" }, // "bands" | "items" | "stacked"
	// shared legend above the rows: [{ key, label, tone, text? }]
	legend: { type: Array, default: () => [] },
	// override the scale: the total that is a full-width bar
	scaleMax: { type: Number, default: null },
	title: { type: String, default: "" },
	// [row heading, segment heading, value heading, end-label heading (only when a row has an end label)]
	tableHeaders: { type: Array, default: null },
});

const totalOf = (row) => row.segments.reduce((sum, segment) => sum + (segment.count > 0 ? segment.count : 0), 0);
const full = computed(() => props.scaleMax || Math.max(0, ...props.rows.map(totalOf)));
const widthOf = (row) => percent(totalOf(row), full.value);
const drawn = (row) => row.segments.filter((segment) => segment.count > 0);
const hasEnd = computed(() => props.rows.some((row) => row.endLabel));
const headers = computed(() => {
	const base = props.tableHeaders || [t("Item"), t("Segment"), t("Value")];
	return hasEnd.value && base.length < 4 ? [...base, t("Note")] : base;
});
const tableRows = computed(() =>
	props.rows.flatMap((row) =>
		drawn(row).map((segment, index) => {
			const cells = [row.label, segment.label, textOf(segment)];
			return hasEnd.value ? [...cells, index === 0 ? row.endLabel || "" : ""] : cells;
		}),
	),
);
</script>

<template>
	<div class="kt-anl-chart" data-chart="segmented-bar-rows">
		<ChartLegend v-if="legend.length" :items="legend" aria-hidden="true" />
		<div class="kt-anl-segrows" :class="'is-' + variant" aria-hidden="true">
			<template v-if="variant === 'stacked'">
				<div v-for="row in rows" :key="row.key" class="kt-anl-segrow">
					<span class="kt-anl-segrow-label">{{ row.label }}</span>
					<div class="kt-anl-segrow-bar" :style="{ width: widthOf(row) }">
						<div class="kt-anl-seg">
							<span v-for="segment in drawn(row)" :key="segment.key" :class="toneClass(segment.tone)" :style="{ flex: segment.count + ' 1 0' }"></span>
						</div>
					</div>
					<span class="kt-anl-segrow-values">
						<span v-for="segment in drawn(row)" :key="segment.key" :class="{ 'is-muted': segment.muted }">{{ segment.label }} {{ textOf(segment) }}</span>
						<b v-if="row.endLabel">{{ row.endLabel }}</b>
					</span>
				</div>
			</template>
			<template v-else v-for="row in rows" :key="row.key">
				<span class="kt-anl-segrow-label">{{ row.label }}</span>
				<div class="kt-anl-segrow-barcell">
					<div class="kt-anl-segrow-bar" :style="{ width: widthOf(row) }">
						<div class="kt-anl-seg">
							<span
								v-for="segment in drawn(row)"
								:key="segment.key"
								:class="toneClass(segment.tone)"
								:style="{ flex: segment.count + ' 1 0' }"
							>{{ variant === "bands" ? textOf(segment) : "" }}</span>
						</div>
					</div>
				</div>
				<span v-if="variant === 'items'" class="kt-anl-segrow-values">
					<span v-for="segment in drawn(row)" :key="segment.key" :class="{ 'is-muted': segment.muted }">{{ segment.label }} {{ textOf(segment) }}</span>
				</span>
			</template>
		</div>
		<ChartTable :caption="title" :headers="headers" :rows="tableRows" />
	</div>
</template>
