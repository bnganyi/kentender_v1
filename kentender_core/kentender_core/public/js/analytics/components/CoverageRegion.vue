<script setup>
// ANL §10A.3 — Plan coverage: the result line, the planned-value line, one segmented bar with its legend, the
// item sentence and a link to annual planning. When the read is unavailable the region says so with Try again
// and shows no percentage, bar or item sentence (31E). When it is incomplete the percentage is withheld (§8).
import { computed } from "vue";
import { SegmentedBar } from "./charts/index.js";
import RegionHeading from "./RegionHeading.vue";
import RegionMessage from "./RegionMessage.vue";
import { isPlainClick, splitLead } from "./presentation.js";

const props = defineProps({
	coverage: { type: Object, required: true },
	hrefFor: { type: Function, required: true },
	busy: { type: Boolean, default: false },
	failed: { type: Boolean, default: false },
});
const emit = defineEmits(["open", "retry"]);

// "81% of planned value is covered…": the percentage in display size, the sentence beside it.
const lead = computed(() => splitLead(props.coverage.result, props.coverage.percent === null || props.coverage.percent === undefined ? "" : props.coverage.percent + "%"));
const segments = computed(() => (props.coverage.segments || []).map((s) => ({ key: s.key, label: s.label, count: s.value, text: s.text, tone: s.tone })));
function open(event) {
	if (!isPlainClick(event)) return;
	event.preventDefault();
	emit("open", props.coverage.link.tab);
}
</script>

<template>
	<div class="kt-ap-region is-14" data-testid="kt-anl-coverage">
		<RegionHeading icon="calendar-days" :title="__('Plan coverage')" />
		<RegionMessage v-if="coverage.status === 'unavailable'" :message="coverage.message" :busy="busy" :failed="failed" @retry="emit('retry')" />
		<template v-else>
			<div class="kt-ap-result-lines">
				<span v-if="coverage.result" class="kt-ap-result-line">
					<span v-if="lead.figure" class="kt-result-value">{{ lead.figure }}</span>
					<span class="kt-ap-result-text">{{ lead.rest }}</span>
				</span>
				<span class="kt-ap-note">{{ coverage.planned }}</span>
			</div>
			<SegmentedBar :segments="segments" size="sm" :title="__('Plan coverage')" :table-headers="[__('Item'), __('Value')]" />
			<p class="kt-ap-text">{{ coverage.items }}</p>
			<p v-if="coverage.incomplete_text" class="kt-ap-incomplete" role="status">{{ coverage.incomplete_text }}</p>
			<a v-if="coverage.link" class="kt-ap-link" :href="hrefFor(coverage.link.tab)" @click="open">{{ coverage.link.label }}</a>
		</template>
	</div>
</template>
