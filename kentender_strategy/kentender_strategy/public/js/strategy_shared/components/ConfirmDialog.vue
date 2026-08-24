<script setup>
// AGENTS.md §6.3: never frappe.confirm()/frappe.ui.Dialog on a Vue-owned
// surface (renders outside the Vue root, inherits neither state nor styles)
// — a small in-Vue dialog instead. Shared by the Plan workspace (Activate /
// Submit for review) and Review task (Approve / Recommend for approval)
// lifecycle actions.
import { ref, nextTick, watch } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	title: { type: String, required: true },
	message: { type: String, default: "" },
	confirmLabel: { type: String, default: "Confirm" },
});
const emit = defineEmits(["confirm", "cancel"]);

const confirmBtn = ref(null);
watch(
	() => props.open,
	async (isOpen) => {
		if (!isOpen) return;
		await nextTick();
		confirmBtn.value?.focus();
	}
);

function onKeydown(e) {
	if (e.key === "Escape") emit("cancel");
}
</script>

<template>
	<div
		v-if="open"
		class="kt-confirm-backdrop"
		@keydown="onKeydown"
		tabindex="-1"
	>
		<div class="kt-confirm-box kt-card">
			<div class="kt-card-title">{{ title }}</div>
			<p v-if="message" class="kt-text-muted">{{ message }}</p>
			<div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 12px">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button ref="confirmBtn" type="button" class="kt-btn kt-btn-primary" @click="$emit('confirm')">
					{{ confirmLabel }}
				</button>
			</div>
		</div>
	</div>
</template>

<style scoped>
.kt-confirm-backdrop {
	position: fixed;
	inset: 0;
	background: color-mix(in srgb, #000 40%, transparent);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 1000;
}
.kt-confirm-box {
	width: 420px;
	max-width: calc(100vw - 40px);
}
</style>
