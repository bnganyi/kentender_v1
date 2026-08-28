<script setup>
// Themed, dismissible page-level error banner — replaces Frappe's generic
// frappe.throw() popup for reference-data screens. Used for errors that aren't
// tied to one form field (AUTH_ROLE_REQUIRED, VERSION_CONFLICT, REFERENCE_IN_USE,
// and any error not registered in a screen's field map).
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
