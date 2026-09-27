<script setup>
// BDS-CHG-001 v0.8 §10.13 BDS-DES-12 confirmation dialog, ported from "Bid
// Board v3 - D": the four facts the signatory is submitting and what
// happens next. The screen runs the command; this dialog only confirms.
import { nextTick, onMounted, ref } from "vue";

defineProps({
	dialog: { type: Object, required: true },
	pending: { type: Boolean, default: false },
});
const emit = defineEmits(["close", "confirm"]);
const first = ref(null);
onMounted(() => nextTick(() => first.value && first.value.focus()));
</script>

<template>
	<div class="kt-dialog-backdrop" data-testid="bds-submit-dialog" @keydown.esc.stop="!pending && emit('close')">
		<div class="kt-dialog bds-dialog" role="dialog" aria-modal="true" aria-labelledby="bds-submit-dialog-title">
			<div id="bds-submit-dialog-title" class="kt-dialog-title">{{ __(dialog.title) }}</div>
			<div class="bds-dialog-facts">
				<div v-for="fact in dialog.facts" :key="fact.label" class="bds-dialog-fact"><span class="kt-label">{{ __(fact.label) }}</span><span>{{ fact.value }}</span></div>
			</div>
			<p class="bds-dialog-text">{{ dialog.text }}</p>
			<div class="kt-dialog-actions">
				<button ref="first" type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="emit('close')">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bds-submit-confirm" @click="emit('confirm')">{{ pending ? __("Submitting bid…") : __("Submit bid") }}</button>
			</div>
		</div>
	</div>
</template>
