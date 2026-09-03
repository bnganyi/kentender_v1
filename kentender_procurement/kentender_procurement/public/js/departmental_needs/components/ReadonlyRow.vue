<!-- One labelled read-only value (NDS-DES-03/05/06/07/12). -->
<template>
	<div class="kt-readonly-row">
		<div class="kt-readonly-label">{{ label }}</div>
		<!-- `volatile` marks a value that legitimately differs between runs — an
		     audit instant, which is fixture-build time. The visual-regression
		     spec masks [data-volatile] so a baseline cannot be made stable by
		     loosening its pixel budget, which would blind it to real changes. -->
		<div
			class="kt-readonly-value"
			:class="{ 'is-strong': strong }"
			:data-volatile="volatile ? 'true' : null"
		>
			<slot>{{ value }}</slot>
		</div>
	</div>
</template>

<script setup>
defineProps({
	label: { type: String, required: true },
	value: { type: [String, Number], default: "" },
	strong: { type: Boolean, default: false },
	volatile: { type: Boolean, default: false },
});
</script>
