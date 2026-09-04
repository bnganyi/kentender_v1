<script setup>
// Themed, dismissible page-level error banner — ported from
// kentender_core's reference_data KtErrorBanner.vue. Physically duplicated
// rather than imported across the app boundary (AGENTS.md §2: no deep
// import into another app's internals — same reason frappeCall.js is its
// own copy per app, not a shared cross-app import). Replaces a plain muted
// <p> for save/submit failures, which read as too easy to miss — this
// renders as a tinted box with role="alert" instead.
defineProps({ message: { type: String, default: "" } });
const emit = defineEmits(["dismiss"]);
</script>

<template>
	<div v-if="message" class="kt-error-banner" role="alert">
		<span>{{ message }}</span>
		<button type="button" class="kt-error-banner-dismiss" @click="emit('dismiss')" :aria-label="__('Dismiss')">×</button>
	</div>
</template>

<style scoped>
.kt-error-banner {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 12px;
	padding: 12px 16px;
	border-radius: 8px;
	background: #e11d481a;
	color: #b0143a;
	font-size: 14px;
	line-height: 1.5;
}
.kt-error-banner-dismiss {
	background: none;
	border: none;
	color: inherit;
	font-size: 18px;
	line-height: 1;
	cursor: pointer;
	padding: 0;
	flex: none;
}
</style>
