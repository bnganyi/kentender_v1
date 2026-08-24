<script setup>
// AGENTS.md §6.3: never frappe.confirm()/frappe.ui.Dialog on a Vue-owned
// surface (renders outside the Vue root, inherits neither state nor styles)
// — a small in-Vue dialog instead. Shared by the Plan workspace (Activate /
// Submit for review) and Review task (Approve / Recommend for approval)
// lifecycle actions.
import { ref, nextTick, watch, computed } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	title: { type: String, required: true },
	message: { type: String, default: "" },
	confirmLabel: { type: String, default: "Confirm" },
	// Optional reason textarea (STR-DES spec: Return opens a dialog with
	// only Return reason, Cancel and Return — reused here rather than a
	// bespoke dialog, since it's the same confirm/cancel shell).
	requireReason: { type: Boolean, default: false },
	reasonPlaceholder: { type: String, default: "" },
	reasonMinLength: { type: Number, default: 0 },
	reasonMaxLength: { type: Number, default: 500 },
});
const emit = defineEmits(["confirm", "cancel"]);

const reason = ref("");
const confirmBtn = ref(null);
const reasonInput = ref(null);
watch(
	() => props.open,
	async (isOpen) => {
		if (!isOpen) return;
		reason.value = "";
		await nextTick();
		(props.requireReason ? reasonInput.value : confirmBtn.value)?.focus();
	}
);

const reasonValid = computed(
	() => !props.requireReason || reason.value.trim().length >= props.reasonMinLength
);

function onKeydown(e) {
	if (e.key === "Escape") emit("cancel");
}

function onConfirm() {
	emit("confirm", props.requireReason ? reason.value.trim() : undefined);
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
			<textarea
				v-if="requireReason"
				ref="reasonInput"
				v-model="reason"
				class="kt-input"
				style="width: 100%; margin-top: 4px"
				rows="3"
				:placeholder="reasonPlaceholder"
				:maxlength="reasonMaxLength"
			></textarea>
			<div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 12px">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button ref="confirmBtn" type="button" class="kt-btn kt-btn-primary" :disabled="!reasonValid" @click="onConfirm">
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
