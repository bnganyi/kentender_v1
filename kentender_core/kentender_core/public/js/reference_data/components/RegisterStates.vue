<script setup>
// §12.9 — the four non-happy-path register states (Loading / No matches / Forbidden /
// Server error), shared across the PE, FY and Context tabs so each register table only
// has to render its real rows.
const props = defineProps({
	loading: { type: Boolean, default: false },
	error: { type: Object, default: null }, // { type: 'forbidden' | 'server', message }
	isEmpty: { type: Boolean, default: false },
});
const emit = defineEmits(["clear-filters", "retry"]);
</script>

<template>
	<div v-if="loading" style="margin:36px 48px 0;display:flex;flex-direction:column">
		<div
			v-for="n in 5"
			:key="n"
			style="height:64px;display:flex;align-items:center;border-top:1px solid var(--kt-color-divider)"
			:style="n === 5 ? 'border-bottom:1px solid var(--kt-color-divider)' : ''"
		>
			<div class="kt-skel" style="width:100%"></div>
		</div>
	</div>

	<div v-else-if="error && error.type === 'forbidden'" class="kt-empty">
		<h2>{{ error.message }}</h2>
		<p>{{ __("Ask your KenTender administrator to review your configuration assignment.") }}</p>
	</div>

	<div v-else-if="error" class="kt-empty">
		<h2>{{ error.message }}</h2>
		<p>{{ __("Try again. If the problem continues, contact KenTender support.") }}</p>
		<button type="button" class="kt-btn kt-btn-secondary" @click="emit('retry')">{{ __("Try again") }}</button>
	</div>

	<div v-else-if="isEmpty" class="kt-empty">
		<h2>{{ __("No records match these filters.") }}</h2>
		<p>{{ __("Change or clear the filters to see other records.") }}</p>
		<button type="button" class="kt-btn kt-btn-secondary" @click="emit('clear-filters')">{{ __("Clear filters") }}</button>
	</div>

	<slot v-else></slot>
</template>
