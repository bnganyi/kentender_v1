<!-- A left-ruled block of labelled facts (the board's kt-meta-row groups).
     `rows` is a list of rows; each row is a list of {label, value}. -->
<template>
	<div class="req-rule">
		<div v-for="(row, i) in rows" :key="i" class="kt-meta-row">
			<div v-for="fact in row" :key="fact.label + fact.value">
				<span class="kt-label">{{ fact.label || " " }}</span>
				<span class="kt-meta-value" :class="fact.cls" :style="fact.style">{{ fact.value }}</span>
			</div>
		</div>
		<slot />
	</div>
</template>

<script setup>
defineProps({ rows: { type: Array, required: true } });
</script>
