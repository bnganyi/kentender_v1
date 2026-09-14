<script setup>
// AGENTS.md §6.3: never frappe.confirm()/frappe.ui.Dialog on a Vue-owned
// surface — a small in-Vue dialog instead. Shared by every Strategy
// confirmation: destructive deletes, the unsaved-changes guard (three
// actions: primary / discard / stay), and the successor confirmation.
import { ref, nextTick, watch } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	title: { type: String, required: true },
	message: { type: String, default: "" },
	confirmLabel: { type: String, default: "Confirm" },
	// Optional destructive styling on the primary action (Delete …).
	danger: { type: Boolean, default: false },
	// Optional middle action (Discard unsaved changes) — emits "secondary".
	secondaryLabel: { type: String, default: "" },
	cancelLabel: { type: String, default: "" },
	testid: { type: String, default: "str-confirm" },
});
const emit = defineEmits(["confirm", "secondary", "cancel"]);

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
	<div v-if="open" class="kt-dialog-backdrop" tabindex="-1" @keydown="onKeydown">
		<div class="kt-dialog" role="dialog" aria-modal="true" style="width: 480px" :data-testid="testid">
			<h2 class="kt-dialog-title">{{ title }}</h2>
			<p v-if="message" class="kt-muted" style="margin: 0; font-size: 14px">{{ message }}</p>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="str-confirm-cancel" @click="$emit('cancel')">
					{{ cancelLabel || __("Cancel") }}
				</button>
				<button v-if="secondaryLabel" type="button" class="kt-btn kt-btn-secondary" data-testid="str-confirm-secondary" @click="$emit('secondary')">
					{{ secondaryLabel }}
				</button>
				<button
					ref="confirmBtn"
					type="button"
					class="kt-btn kt-btn-primary"
					:class="{ 'kt-danger': danger }"
					data-testid="str-confirm-ok"
					@click="$emit('confirm')"
				>
					{{ confirmLabel }}
				</button>
			</div>
		</div>
	</div>
</template>
