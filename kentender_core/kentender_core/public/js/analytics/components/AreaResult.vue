<script setup>
// ANL §10A.4 to §10A.8 — the area result: the count in display size beside the server's sentence, the quiet
// "No outstanding matters recorded in this selection." line, and (annual planning) the plan's source line.
// A partial list has no complete total, so no display figure stands in for one (§8).
import { computed } from "vue";
import { splitLead } from "./presentation.js";

const props = defineProps({ area: { type: Object, required: true } });
const lead = computed(() => (props.area.partial ? { figure: "", rest: props.area.result_text } : splitLead(props.area.result_text, props.area.figure)));
</script>

<template>
	<section class="kt-ap-section is-tight" data-testid="kt-anl-area-result">
		<span class="kt-ap-result-line is-area">
			<span v-if="lead.figure" class="kt-result-value">{{ lead.figure }}</span>
			<span class="kt-ap-result-text">{{ lead.rest }}</span>
		</span>
		<p v-if="area.incomplete_text" class="kt-ap-incomplete" role="status">{{ area.incomplete_text }}</p>
		<p v-if="area.secondary" class="kt-ap-text-md">{{ area.secondary }}</p>
		<p v-if="area.source" class="kt-ap-note">{{ area.source }}</p>
	</section>
</template>
