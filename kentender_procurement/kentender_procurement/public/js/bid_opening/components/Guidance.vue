<!-- The shared guidance region below the page head (KT-STD-001 v1.10 §2.9;
     boards draw it as .kt-guidance with the journey above the next step). -->
<template>
	<div ref="host" class="bop-guidance-host" data-testid="bop-guidance"></div>
</template>

<script setup>
import { ref } from "vue";
import { useGuidance } from "../composables/useGuidance.js";

const props = defineProps({ answer: { type: Object, default: null }, journey: { type: Object, default: null }, pending: Boolean });
const emit = defineEmits(["fix"]);
const host = ref(null);
useGuidance(host, { answer: () => props.answer, journey: () => props.journey, pending: () => props.pending }, { onFix: (fix) => emit("fix", fix) });
</script>
