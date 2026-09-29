<!-- The boards' page head: a title and one description line. After the
     preparation boards the line is "<Tender title> · <status>", where the
     status is the server's own words (reads.status_line). -->
<template>
	<div class="kt-page-head">
		<div><h1 class="kt-page-title" data-testid="bop-title">{{ title }}</h1><p class="kt-page-desc" data-testid="bop-desc">{{ lead }}<template v-if="status && status.label">{{ lead ? " · " : "" }}<span class="kt-status" :class="status.tone">{{ status.label }}</span><template v-if="status.since"> {{ status.since }}</template></template></p></div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({ title: { type: String, default: "" }, desc: { type: String, default: "" }, status: { type: Object, default: null } });
const lead = computed(() => [props.desc, props.status && props.status.text].filter(Boolean).join(" · "));
</script>
