<!-- The boards' plain confirmation dialogs (Submit for approval, Approve
     package, Authorise publication, Issue addendum, Cancel Tender): a title,
     an optional fact grid, a note, Cancel + one primary (or danger) action. -->
<template>
	<div class="kt-dialog-backdrop" :data-testid="testid" @keydown.esc="$emit('cancel')">
		<div ref="dialogEl" class="kt-dialog tnd-dialog" role="dialog" aria-modal="true" :aria-labelledby="`${testid}-title`" tabindex="-1">
			<div :id="`${testid}-title`" class="kt-dialog-title">{{ title }}</div>
			<div class="tnd-dialog-body">
				<p v-if="intro" class="tnd-small tnd-muted-700" style="margin: 0 0 12px">{{ intro }}</p>
				<div v-if="facts.length" class="tnd-grid-2" style="gap: 12px; margin-bottom: 12px">
					<div v-for="f in facts" :key="f.label" class="tnd-fact"><div class="kt-label">{{ f.label }}</div><div class="tnd-fact-value">{{ f.value }}</div></div>
				</div>
				<p v-if="note" class="tnd-small tnd-muted-700" style="margin: 0">{{ note }}</p>
				<p v-if="error" class="tnd-field-error" role="alert" :data-testid="`${testid}-error`">{{ error }}</p>
			</div>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">{{ cancelLabel }}</button>
				<button type="button" class="kt-btn" :class="danger ? 'tnd-btn-danger' : 'kt-btn-primary'" :disabled="pending" :data-testid="`${testid}-confirm`" @click="$emit('confirm')">{{ confirmLabel }}</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

defineProps({
	testid: { type: String, default: "tnd-confirm-dialog" },
	title: { type: String, required: true },
	intro: { type: String, default: "" },
	facts: { type: Array, default: () => [] },
	note: { type: String, default: "" },
	confirmLabel: { type: String, default: "Confirm" },
	cancelLabel: { type: String, default: "Cancel" },
	danger: Boolean,
	pending: Boolean,
	error: { type: String, default: "" },
});
defineEmits(["confirm", "cancel"]);
const dialogEl = ref(null);
onMounted(() => nextTick(() => dialogEl.value && dialogEl.value.focus()));
</script>
