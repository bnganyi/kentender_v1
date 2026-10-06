<script setup>
// ANL §10A.7 — "Tender invitation timing": horizontal bars from a zero line, later to the right and earlier
// to the left, a value label on each row. `halfRange` is the number of days at either edge of the track.
// A zero value draws a hairline at the zero line (as the board does); a row with `value: null` (for example
// "No date recorded") has no bar. The labels are the server's words.
import { computed } from "vue";
import ChartTable from "./ChartTable.vue";
import { t, toneClass } from "./chartUtil.js";

const HAIRLINE = 0.6;

const props = defineProps({
	// [{ key, label, value: number | null (days, negative = earlier), text, tone? }]
	rows: { type: Array, required: true },
	// days at each edge of the track; the zero line sits in the middle
	halfRange: { type: Number, required: true },
	tone: { type: String, default: "cat-1" },
	// the words under the two ends of the track
	earlierLabel: { type: String, default: "" },
	laterLabel: { type: String, default: "" },
	caption: { type: String, default: "" },
	title: { type: String, default: "" },
	// [row heading, value heading]
	tableHeaders: { type: Array, default: null },
});

const hasBar = (row) => row.value !== null && row.value !== undefined;
const barStyle = (row) => {
	const width = row.value === 0 ? HAIRLINE : Math.min(50, (Math.abs(row.value) / props.halfRange) * 50);
	return { width: Math.round(width * 100) / 100 + "%" };
};
const headers = computed(() => props.tableHeaders || [t("Item"), t("Value")]);
const tableRows = computed(() => props.rows.map((row) => [row.label, row.text]));
</script>

<template>
	<div class="kt-anl-chart" data-chart="from-zero-bars">
		<div class="kt-anl-fromzero" aria-hidden="true">
			<template v-for="row in rows" :key="row.key">
				<span class="kt-anl-fromzero-label">{{ row.label }}</span>
				<span class="kt-anl-fromzero-track">
					<span
						v-if="hasBar(row)"
						class="kt-anl-fromzero-bar"
						:class="[toneClass(row.tone || tone), row.value < 0 ? 'is-earlier' : 'is-later']"
						:style="barStyle(row)"
					></span>
					<span class="kt-anl-fromzero-zero"></span>
				</span>
				<span class="kt-anl-fromzero-value" :class="{ 'is-none': !hasBar(row) }">{{ row.text }}</span>
			</template>
		</div>
		<div v-if="earlierLabel || laterLabel" class="kt-anl-fromzero-ends" aria-hidden="true">
			<span>{{ earlierLabel }}</span>
			<span>{{ laterLabel }}</span>
		</div>
		<p v-if="caption" class="kt-anl-caption" aria-hidden="true">{{ caption }}</p>
		<ChartTable :caption="title || caption" :headers="headers" :rows="tableRows" />
	</div>
</template>
