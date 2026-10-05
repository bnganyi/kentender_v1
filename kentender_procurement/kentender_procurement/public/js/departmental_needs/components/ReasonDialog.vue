<!-- NDS-DES-11 / NDS-DES-13 RETURN-INITIAL / RETURN-UPDATE / DECLINE-INITIAL /
     DECLINE-UPDATE / DECLINE-WITHDRAWAL — the reason dialogs, ported from
     NDS Artboards.dc.html (content and structure; the mockup's own raw
     `dialog`/`field`/`btn` classes are not carried over). One component:
     every artboard differs only in title, subject/meta, lede, field label,
     button label and tone, and §11.13 forbids any extra control in all of
     them.

     §12.8 requires focus to be trapped and restored. -->
<template>
	<div class="dialog-backdrop" data-testid="nds-dialog" @mousedown.self="$emit('cancel')">
		<div
			ref="dialogEl"
			class="dialog"
			role="dialog"
			aria-modal="true"
			:aria-labelledby="titleId"
			@keydown.esc.prevent="$emit('cancel')"
			@keydown.tab="trapFocus"
		>
			<div :id="titleId" class="dialog-title">{{ title }}</div>
			<div class="kt-dialog-body">
				<!-- NDS-DES-11 / 13 — the requirement name/reference/revision, so the
				     target is unambiguous before the reason field. `meta` (an ordered
				     [{label, value}] list) renders each fact as its own labelled row,
				     matching the artboard's own `.kt-meta-row` — the same convention
				     WithdrawalDialog.vue (Procurement Planning) and
				     WithdrawalReviewScreen.vue already use for label/value pairs.
				     `subjectMeta` (a single pre-joined string) is unused by every
				     current caller (NDS-DES-11 request-withdrawal was the last one
				     still on it) but kept as a fallback rather than removed, so a
				     future one-off caller isn't forced to build a `meta` array for a
				     single fact. -->
				<p v-if="subject" style="margin: 8px 0 0; font-size: 14.5px; font-weight: 500">{{ subject }}</p>
				<div v-if="meta.length" class="kt-meta-row" style="margin: 14px 0 8px">
					<div v-for="row in meta" :key="row.label">
						<span class="kt-label">{{ row.label }}</span>
						<span class="kt-meta-value" style="font-size: 15px">{{ row.value }}</span>
					</div>
				</div>
				<div v-else-if="subjectMeta" class="kt-label" style="margin-bottom: 16px">{{ subjectMeta }}</div>
				<p v-if="lede" style="margin: 0 0 16px; font-size: 14.5px; color: var(--color-neutral-700)">
					{{ lede }}
				</p>
				<div class="field">
					<label :for="fieldId">{{ fieldLabel }}</label>
					<textarea
						:id="fieldId"
						ref="reasonEl"
						data-testid="nds-dialog-reason"
						class="input"
						rows="4"
						:value="modelValue"
						@input="$emit('update:modelValue', $event.target.value)"
					></textarea>
					<div v-if="error" class="kt-field-error">{{ error }}</div>
					<div v-else style="font-size: 12.5px; color: var(--color-neutral-600); margin-top: 6px">
						{{ minLength }}–{{ maxLength }} characters.
					</div>
				</div>
			</div>
			<div class="dialog-actions">
				<button class="btn btn-secondary" data-testid="nds-dialog-cancel" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					:class="destructive ? 'btn-destructive' : 'btn btn-primary'"
					data-testid="nds-dialog-confirm"
					:disabled="pending"
					@click="$emit('confirm')"
				>
					<svg
						v-if="confirmLabel === 'Return for correction'"
						width="15"
						height="15"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					><path d="M3 7v6h6" /><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" /></svg>
					<svg
						v-else-if="confirmLabel === 'Request withdrawal'"
						width="15"
						height="15"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					><rect width="20" height="5" x="2" y="3" rx="1" /><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" /><path d="M10 12h4" /></svg>
					<svg
						v-else-if="['Do not take forward', 'Decline proposed changes', 'Decline withdrawal'].includes(confirmLabel)"
						width="15"
						height="15"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-linecap="round"
						stroke-linejoin="round"
					><path d="M18 6 6 18M6 6l12 12" /></svg
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
	subject: { type: String, default: "" },
	subjectMeta: { type: String, default: "" },
	// [{label, value}], e.g. [{label:"Reference", value:"NDS-MOH-2027-0003"},
	// {label:"Revision", value:"1"}] — NDS-DES-13's own `.kt-meta-row`.
	meta: { type: Array, default: () => [] },
	lede: { type: String, default: "" },
	fieldLabel: { type: String, default: "Reason" },
	confirmLabel: { type: String, required: true },
	modelValue: { type: String, default: "" },
	error: { type: String, default: "" },
	pending: Boolean,
	destructive: Boolean,
	minLength: { type: Number, default: 20 },
	maxLength: { type: Number, default: 1000 },
});
defineEmits(["update:modelValue", "confirm", "cancel"]);

const dialogEl = ref(null);
const reasonEl = ref(null);
const titleId = `nds-dialog-title-${Math.random().toString(16).slice(2)}`;
const fieldId = `nds-dialog-reason-${Math.random().toString(16).slice(2)}`;
let restoreTo = null;

onMounted(() => {
	restoreTo = document.activeElement;
	reasonEl.value?.focus();
});
onBeforeUnmount(() => {
	// §12.8 — focus returns to whatever opened the dialog.
	if (restoreTo && typeof restoreTo.focus === "function") restoreTo.focus();
});

function trapFocus(event) {
	const focusable = dialogEl.value?.querySelectorAll(
		'button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
	);
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
