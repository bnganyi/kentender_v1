<!-- §12.5 — the acceptance confirmation. It collects no reason, score,
     recommendation or checklist; it states the fixed sentence and nothing
     more. Also used for the §12.3 withdraw/cancel-update confirmations. -->
<template>
	<div class="kt-dialog-backdrop" @mousedown.self="$emit('cancel')">
		<div
			ref="dialogEl"
			class="kt-dialog"
			role="dialog"
			aria-modal="true"
			:aria-labelledby="titleId"
			@keydown.esc.prevent="$emit('cancel')"
			@keydown.tab="trapFocus"
		>
			<div :id="titleId" class="kt-dialog-title">{{ title }}</div>
			<div class="kt-dialog-body">
				<p v-if="subject" style="margin: 0 0 8px; font-size: 14.5px; font-weight: 500">
					{{ subject }}
				</p>
				<p style="margin: 0; font-size: 14.5px; color: var(--color-neutral-700)">
					{{ message }}
				</p>
			</div>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" data-testid="nds-dialog-cancel" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					:class="destructive ? 'kt-btn-destructive' : 'kt-btn kt-btn-primary'"
					ref="confirmEl"
					data-testid="nds-dialog-confirm"
					:disabled="pending"
					@click="$emit('confirm')"
				>
					{{ confirmLabel }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue";

defineProps({
	title: { type: String, required: true },
	message: { type: String, required: true },
	subject: { type: String, default: "" },
	confirmLabel: { type: String, required: true },
	pending: Boolean,
	destructive: Boolean,
});
defineEmits(["confirm", "cancel"]);

const dialogEl = ref(null);
const confirmEl = ref(null);
const titleId = `nds-confirm-title-${Math.random().toString(16).slice(2)}`;
let restoreTo = null;

onMounted(() => {
	restoreTo = document.activeElement;
	confirmEl.value?.focus();
});
onBeforeUnmount(() => {
	if (restoreTo && typeof restoreTo.focus === "function") restoreTo.focus();
});

function trapFocus(event) {
	const focusable = dialogEl.value?.querySelectorAll("button:not([disabled])");
	if (!focusable || !focusable.length) return;
	const first = focusable[0];
	const last = focusable[focusable.length - 1];
	if (event.shiftKey && document.activeElement === first) {
		event.preventDefault();
		last.focus();
	} else if (!event.shiftKey && document.activeElement === last) {
		event.preventDefault();
		first.focus();
	}
}
</script>
