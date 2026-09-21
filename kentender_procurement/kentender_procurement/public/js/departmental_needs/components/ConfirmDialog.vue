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
					<svg
						v-if="confirmLabel === 'Withdraw need'"
						width="15"
						height="15"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					><path d="M3 6h18" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" /><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
					<svg
						v-else-if="confirmLabel === 'Cancel update'"
						width="15"
						height="15"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					><path d="M18 6 6 18M6 6l12 12" /></svg>
					<svg
						v-else-if="confirmLabel === 'Approve withdrawal'"
						width="15"
						height="15"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					><path d="M20 6 9 17l-5-5" /></svg
					>{{ confirmLabel }}
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
