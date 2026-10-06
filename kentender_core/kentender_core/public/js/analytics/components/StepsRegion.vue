<script setup>
// ANL §10A.3 — Time between key steps: a range strip with value columns (Step, chart, Completed, Median,
// Shortest, Longest) on one shared axis, then the caption and the two chart keys. A step with no completed
// events has no median to draw; a step whose read failed is named with the server's own sentence.
import { computed } from "vue";
import { RangeStrip } from "./charts/index.js";
import RegionHeading from "./RegionHeading.vue";

const props = defineProps({ steps: { type: Object, required: true } });

const drawn = computed(() =>
	(props.steps.rows || [])
		.filter((row) => row.status === "ok" && row.median_text)
		.map((row) => ({
			key: row.key,
			label: row.label,
			completed: String(row.completed),
			median: { value: row.median, text: row.median_text },
			shortest: { value: row.shortest, text: row.shortest_text },
			longest: { value: row.longest, text: row.longest_text },
		})),
);
const unavailable = computed(() => (props.steps.rows || []).filter((row) => row.status === "unavailable"));
const axis = computed(() => ({ max: props.steps.axis.max, ticks: (props.steps.axis.ticks || []).map((value) => ({ value, label: String(value) })) }));
</script>

<template>
	<section class="kt-ap-section is-steps is-ruled" data-testid="kt-anl-steps">
		<RegionHeading icon="timer" :title="__('Time between key steps')" />
		<RangeStrip
			v-if="drawn.length"
			:columns="[__('Step'), '', __('Completed'), __('Median'), __('Shortest'), __('Longest')]"
			:rows="drawn"
			:axis="axis"
			:caption="steps.caption"
			:median-label="__('Median')"
			:range-label="__('Shortest to longest')"
			:title="__('Time between key steps')"
		/>
		<p v-else-if="steps.empty_text" class="kt-ap-text-md" data-testid="kt-anl-steps-empty">{{ steps.empty_text }}</p>
		<ul v-if="unavailable.length" class="kt-ap-filter-messages">
			<li v-for="row in unavailable" :key="row.key" class="kt-ap-text">{{ row.label }}: {{ row.message }}</li>
		</ul>
		<p v-if="steps.incomplete_text" class="kt-ap-incomplete" role="status">{{ steps.incomplete_text }}</p>
		<p v-if="!drawn.length && steps.caption" class="kt-ap-note">{{ steps.caption }}</p>
	</section>
</template>
