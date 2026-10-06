<script setup>
// ANL §10A.4 — "Tenders by stage" and "Requisitions by current state": one horizontal bar per row sized by
// its count (largest count, or `max`, is full width), the count as text, and a value column the server
// words (for example "KES 6,500,000"). A row may be `selected`, which mirrors the stage select above the
// register: an accent ring on the bar and a rule on the label. When `selectable`, clicking a row emits
// `select` with its key; the page mirrors it into the select, which stays the keyboard route, so the rows
// are not focusable. No other interaction.
import { computed } from "vue";
import ChartTable from "./ChartTable.vue";
import { percent, t, toneClass } from "./chartUtil.js";

const props = defineProps({
	// [{ key, label, count (number), countText? (defaults to the count), valueText?, tone }]
	rows: { type: Array, required: true },
	// heading over the value column; the header row is drawn only when this is set
	valueHeading: { type: String, default: "" },
	selected: { type: String, default: null },
	selectable: { type: Boolean, default: false },
	// the count that is a full-width bar (default: the largest count)
	max: { type: Number, default: null },
	title: { type: String, default: "" },
	// [row heading, count heading, value heading]
	tableHeaders: { type: Array, default: null },
});
const emit = defineEmits(["select"]);

const full = computed(() => props.max || Math.max(0, ...props.rows.map((row) => row.count)));
const countText = (row) => (row.countText !== undefined && row.countText !== null ? String(row.countText) : String(row.count));
const headers = computed(() => props.tableHeaders || [t("Item"), t("Count"), props.valueHeading || t("Value")]);
const tableRows = computed(() => props.rows.map((row) => [row.label, countText(row), row.valueText || ""]));
const pick = (row) => {
	if (props.selectable) emit("select", row.key);
};
</script>

<template>
	<div class="kt-anl-chart" data-chart="horizontal-bar">
		<div class="kt-anl-hbars" :class="{ 'is-selectable': selectable }" aria-hidden="true">
			<template v-if="valueHeading">
				<span></span>
				<span></span>
				<span></span>
				<span class="kt-anl-hbars-head">{{ valueHeading }}</span>
			</template>
			<template v-for="row in rows" :key="row.key">
				<span class="kt-anl-hbars-label" :class="{ 'is-selected': selected === row.key }" :data-row="row.key" @click="pick(row)">{{ row.label }}</span>
				<span class="kt-anl-hbars-track" @click="pick(row)">
					<span :class="[toneClass(row.tone), { 'is-selected': selected === row.key }]" :style="{ width: percent(row.count, full) }"></span>
				</span>
				<b class="kt-anl-hbars-count">{{ countText(row) }}</b>
				<span class="kt-anl-hbars-value">{{ row.valueText }}</span>
			</template>
		</div>
		<ChartTable :caption="title" :headers="headers" :rows="tableRows" />
	</div>
</template>
