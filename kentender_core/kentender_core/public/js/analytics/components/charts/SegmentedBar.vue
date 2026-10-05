<script setup>
// ANL §10A.1 — one horizontal segmented bar with its legend (summary strip columns, Plan coverage,
// funding position). Segments are drawn in the order given, each sized by its numeric `count`; a
// zero segment has no width and no legend entry unless `keepZero` names its key (the funding bar keeps
// "Committed to contracts KES 0"). Every segment's value is also text (legend, and inside the bar when
// `inside` is set), so colour never carries meaning alone.
import { computed } from "vue";
import ChartLegend from "./ChartLegend.vue";
import ChartTable from "./ChartTable.vue";
import { keepSet, t, textOf, toneClass } from "./chartUtil.js";

const props = defineProps({
	// [{ key, label, count (number, geometry), text? (value text), tone }]
	segments: { type: Array, required: true },
	// the chart's name for assistive technology (the table caption)
	title: { type: String, default: "" },
	legend: { type: Boolean, default: true },
	// write each segment's value inside its segment (waiting bands)
	inside: { type: Boolean, default: false },
	// bar height: "xs" 10px, "sm" 14px, "md" 16px, "lg" 22px
	size: { type: String, default: "sm" },
	// segment key(s) whose legend entry stays when the count is zero
	keepZero: { type: [String, Array], default: () => [] },
	// [item heading, value heading]
	tableHeaders: { type: Array, default: null },
});

const kept = computed(() => keepSet(props.keepZero));
const drawn = computed(() => props.segments.filter((segment) => segment.count > 0));
const listed = computed(() => props.segments.filter((segment) => segment.count > 0 || kept.value.has(segment.key)));
const legendItems = computed(() => listed.value.map((segment) => ({ key: segment.key, label: segment.label, tone: segment.tone, text: textOf(segment) })));
const headers = computed(() => props.tableHeaders || [t("Item"), t("Value")]);
const rows = computed(() => listed.value.map((segment) => [segment.label, textOf(segment)]));
</script>

<template>
	<div class="kt-anl-chart" data-chart="segmented-bar">
		<div class="kt-anl-seg" :class="'is-' + size" aria-hidden="true">
			<span
				v-for="segment in drawn"
				:key="segment.key"
				:class="toneClass(segment.tone)"
				:style="{ flex: segment.count + ' 1 0' }"
			>{{ inside ? textOf(segment) : "" }}</span>
		</div>
		<ChartLegend v-if="legend" :items="legendItems" aria-hidden="true" />
		<ChartTable :caption="title" :headers="headers" :rows="rows" />
	</div>
</template>
