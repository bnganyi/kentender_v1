<script setup>
// AGENTS.md §6.3: never frappe.confirm()/frappe.ui.Dialog on a Vue-owned
// surface (renders outside the Vue root, inherits neither state nor styles)
// — a small in-Vue dialog instead. Shared by the Plan workspace (Submit for
// approval / Create successor) and Approval task (Approve / Return)
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
		class="kt-dialog-backdrop"
		@keydown="onKeydown"
		tabindex="-1"
	>
		<div class="kt-dialog" style="width: 420px" data-testid="str-confirm">
			<h2 class="kt-dialog-title">{{ title }}</h2>
			<p v-if="message" class="kt-muted">{{ message }}</p>
			<textarea
				v-if="requireReason"
				ref="reasonInput"
				v-model="reason"
				class="kt-input"
				style="width: 100%"
				rows="3"
				data-testid="str-confirm-reason"
				:placeholder="reasonPlaceholder"
				:maxlength="reasonMaxLength"
			></textarea>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-ghost" @click="$emit('cancel')">{{ __("Cancel") }}</button>
				<button ref="confirmBtn" type="button" class="kt-btn kt-btn-primary" :disabled="!reasonValid" data-testid="str-confirm-ok" @click="onConfirm">
					{{ confirmLabel }}
				</button>
			</div>
		</div>
	</div>
</template>
