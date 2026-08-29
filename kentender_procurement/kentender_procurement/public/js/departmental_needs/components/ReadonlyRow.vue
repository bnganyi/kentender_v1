<!-- One labelled read-only value (NDS-DES-03/05/06/07/12). -->
<template>
	<div class="kt-readonly-row">
		<div class="kt-readonly-label">{{ label }}</div>
		<div class="kt-readonly-value" :class="{ 'is-strong': strong }">
			<slot>{{ value }}</slot>
		</div>
	</div>
</template>

<script setup>
defineProps({
	label: { type: String, required: true },
	value: { type: [String, Number], default: "" },
	strong: { type: Boolean, default: false },
});
</script>
