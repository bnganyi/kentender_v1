<script setup>
// KT-STD-001 v1.8 §2.9 / §3B on the supplier portal (BDS-CHG-001 v0.8
// §10.19): the server's `journey` and `next_step`, drawn by kentender_core's
// shared guidance region (kt_industry_guidance.bundle.js, loaded by the
// portal page) — the boards' `.kt-guidance` block. A portal screen passes the
// read's answers unchanged; nothing here derives a stage or a headline.
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps({
	journey: { type: Object, default: null },
	answer: { type: Object, default: null },
	label: { type: String, default: "Journey" },
	pending: { type: Boolean, default: false },
});
const emit = defineEmits(["fix", "link"]);
const host = ref(null);
let handle = null;

function state() {
	return { journey: props.journey, answer: props.answer, label: props.label, pending: props.pending };
}
onMounted(() => {
	const industry = window.kentender_core && window.kentender_core.industry;
	if (host.value && industry && industry.mountGuidance) {
		handle = industry.mountGuidance(host.value, { ...state(), onFix: (fix) => emit("fix", fix), onLink: (link) => emit("link", link) });
	}
});
watch(() => [props.journey, props.answer, props.pending], () => handle && handle.update(state()), { deep: true });
onBeforeUnmount(() => handle && handle.unmount());
</script>

<template>
	<div ref="host" class="kt-guidance-host" data-kt="guidance"></div>
</template>
