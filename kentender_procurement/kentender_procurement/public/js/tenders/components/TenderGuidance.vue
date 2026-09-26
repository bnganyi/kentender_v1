<!-- TPR-CHG-001 v0.12 §10.17 — the boards' `TenderGuidance` import: one
     guidance region (the five-stage Tender journey above the next-step
     block) directly below the record header and above the first working
     region. Drawn by kentender_core's shared components through the
     mount helper; everything shown is the server's `guidance` answer, and a
     fix is handed to the root, which owns every command. An answer passed
     explicitly (a refused command's blocked answer, §10.17 DES-08) replaces
     the read's own until the next reload. -->
<template>
	<div ref="hostEl" class="tnd-guidance" data-testid="tnd-guidance"></div>
</template>

<script setup>
import { ref } from "vue";
import { useGuidance } from "../../tnd_shared/composables/useGuidance.js";

const props = defineProps({
	guidance: { type: Object, default: null },
	answer: { type: Object, default: null },
	pending: Boolean,
});
const emit = defineEmits(["fix", "link"]);

const hostEl = ref(null);
useGuidance(
	hostEl,
	{
		answer: () => props.answer || (props.guidance || {}).next_step || null,
		journey: () => (props.guidance || {}).journey || null,
		pending: () => props.pending,
	},
	{ onFix: (fix) => emit("fix", fix), onLink: (link) => emit("link", link) },
);
</script>
