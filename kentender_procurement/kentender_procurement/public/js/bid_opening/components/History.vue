<!-- A disclosure (boards a1–a5 "Appointment history", c1 "History", c4–c12
     "Evidence details", c11 "Problem details"): a title row with one summary
     tag; the rows open below. -->
<template>
	<div class="kt-disclosure" :data-testid="testid">
		<div class="kt-disclosure-head" role="button" tabindex="0" :aria-expanded="open ? 'true' : 'false'" @click="open = !open" @keydown.enter.prevent="open = !open">
			<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">{{ title }}</span><span class="tag tag-neutral">{{ summary }}</span></div>
			<svg class="kt-disclosure-chevron" :class="{ 'is-open': open }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 9l6 6 6-6"></path></svg>
		</div>
		<div v-if="open && rows.length" class="kt-disclosure-body">
			<table class="table"><tbody><tr v-for="(row, i) in rows" :key="i"><td v-for="(cell, j) in row" :key="j">{{ cell }}</td></tr></tbody></table>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";

defineProps({ title: { type: String, required: true }, summary: { type: String, default: "" }, rows: { type: Array, default: () => [] }, testid: { type: String, default: "bop-history" } });
const open = ref(false);
</script>
