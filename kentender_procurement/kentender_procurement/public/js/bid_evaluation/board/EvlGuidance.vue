<!-- The shared guidance region (KT-STD-001 §2.9): the journey tracker above the
     next step, drawn by kentender_core from the server's answers. -->
<template>
	<div ref="host" class="evl-guidance-host" data-testid="evl-guidance"></div>
</template>

<script setup>
import { ref } from "vue";
import { useGuidance } from "../composables/useGuidance.js";

const props = defineProps({ answer: { type: Object, default: null }, journey: { type: Object, default: null }, pending: Boolean });
const emit = defineEmits(["fix"]);
const host = ref(null);
useGuidance(host, { answer: () => props.answer, journey: () => props.journey, pending: () => props.pending }, { onFix: (fix) => emit("fix", fix) });
</script>
