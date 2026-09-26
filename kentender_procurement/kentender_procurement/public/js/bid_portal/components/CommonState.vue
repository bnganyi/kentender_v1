<script setup>
// BDS-CHG-001 v0.8 §10.17 BDS-DES-16 — one common state replacing the
// affected content surface: heading, message and one action, with copy from
// the §10.17 catalogue passed in by the caller.
defineProps({
	state: { type: String, required: true },
	heading: { type: String, required: true },
	message: { type: String, default: "" },
	actionLabel: { type: String, default: "" },
	actionHref: { type: String, default: "" },
});
const emit = defineEmits(["action"]);
</script>

<template>
	<div class="kt-page bds-state" :data-testid="'bds-state-' + state">
		<h1 class="bds-state-heading">{{ __(heading) }}</h1>
		<p v-if="message" class="bds-state-message">{{ __(message) }}</p>
		<div v-if="actionLabel" class="bds-state-action">
			<a v-if="actionHref" class="kt-btn kt-btn-secondary" :href="actionHref">{{ __(actionLabel) }}</a>
			<button v-else type="button" class="kt-btn kt-btn-secondary" @click="emit('action')">{{ __(actionLabel) }}</button>
		</div>
	</div>
</template>
