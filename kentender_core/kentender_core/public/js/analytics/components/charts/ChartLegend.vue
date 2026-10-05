<script setup>
// A chart legend: a swatch, the label and, when the server sent one, the value in bold. The swatch is
// the design system's tone class, so colour is only ever a second cue beside the text.
import { toneClass } from "./chartUtil.js";

defineProps({
	// [{ key, label, tone, text? }] in the order the brief states
	items: { type: Array, required: true },
});
</script>

<template>
	<div class="kt-anl-legend">
		<span v-for="item in items" :key="item.key" :class="toneClass(item.tone)"><i></i>{{ item.label }} <b v-if="item.text">{{ item.text }}</b></span>
	</div>
</template>
