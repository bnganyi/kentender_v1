<script setup>
// CFG-CHG-002 v0.14 §8.1/§10.6 (C03BC #states; tracker CFG14-5D) — a refused
// rule save, shown as the board's state for it: a stale form offers "Review
// latest details", an undeclared overlap "Review versions"; anything else is
// the server's own sentence. Entries in the form are kept either way.
import { computed } from "vue";
import { CFG_SUPERSESSION_INVALID_MESSAGE, CFG_VERSION_CONFLICT_MESSAGE } from "../data/format.js";

const props = defineProps({
	error: { type: String, default: "" },
});
const emit = defineEmits(["refresh", "review"]);

const state = computed(() => {
	if (props.error === CFG_VERSION_CONFLICT_MESSAGE) return "stale";
	if (props.error === CFG_SUPERSESSION_INVALID_MESSAGE) return "overlap";
	return props.error ? "other" : "";
});
</script>

<template>
	<div v-if="state === 'stale'" class="kt-notice is-warning" role="alert" style="flex-direction:column;align-items:flex-start" data-testid="kt-rule-stale">
		<div style="display:flex;gap:12px;align-items:flex-start">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M21 12a9 9 0 1 1-2.64-6.36" /><path d="M21 3v6h-6" /></svg>
			<div class="kt-notice-body"><strong>{{ __("Stale.") }}</strong> {{ __("This information has changed since you opened it.") }}</div>
		</div>
		<a href="#" style="margin-left:30px;font-size:13px" data-testid="kt-rule-review-latest" @click.prevent="emit('refresh')">{{ __("Review latest details") }}</a>
	</div>
	<div v-else-if="state === 'overlap'" class="kt-notice is-critical" role="alert" style="flex-direction:column;align-items:flex-start" data-testid="kt-rule-overlap">
		<div style="display:flex;gap:12px;align-items:flex-start">
			<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M8 7h12M8 12h12M8 17h12M4 7h.01M4 12h.01M4 17h.01" /></svg>
			<div class="kt-notice-body"><strong>{{ __("Overlap.") }}</strong> {{ __("Rule versions overlap for the required date.") }}</div>
		</div>
		<a href="#" style="margin-left:30px;font-size:13px" data-testid="kt-rule-review-versions" @click.prevent="emit('review')">{{ __("Review versions") }}</a>
	</div>
	<div v-else-if="state === 'other'" class="kt-notice is-critical" role="alert" data-testid="kt-rule-error">
		<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>
		<div class="kt-notice-body">{{ error }}</div>
	</div>
</template>
