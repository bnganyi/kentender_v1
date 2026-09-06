<!-- One small governed-reason dialog reused for the two Version-level
     confirmations §4/§5 define without their own artboard: the contract-
     splitting confirmation (invariant 26, owner default O1) and the late-
     activation reason (invariant 27, O2). Same Industry dialog chrome as
     PLN-DES-15; no category, attachment, assignee or due date. -->
<template>
	<div class="kt-dialog-backdrop" :data-testid="testid">
		<div class="kt-dialog" role="dialog" aria-modal="true" :aria-labelledby="`${testid}-title`">
			<div :id="`${testid}-title`" class="kt-dialog-title">{{ title }}</div>
			<p class="pln-dialog-lede">{{ intro }}</p>
			<div class="pln-field">
				<label :for="`${testid}-reason`">{{ label }}</label>
				<textarea
					:id="`${testid}-reason`"
					ref="input"
					class="kt-input"
					rows="4"
					v-model="reason"
					:data-testid="`${testid}-reason`"
				></textarea>
			</div>
			<p v-if="error" class="pln-dialog-error" role="alert">{{ error }}</p>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">Cancel</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					:data-testid="`${testid}-confirm`"
					:disabled="pending || reason.trim().length < minLength"
					@click="$emit('confirm', reason.trim())"
				>
					{{ confirmLabel }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { onMounted, ref } from "vue";

defineProps({
	testid: { type: String, default: "pln-reason-dialog" },
	title: String,
	intro: String,
	label: { type: String, default: "Reason" },
	confirmLabel: { type: String, default: "Confirm" },
	minLength: { type: Number, default: 10 },
	pending: Boolean,
	error: String,
});

defineEmits(["confirm", "cancel"]);

const reason = ref("");
const input = ref(null);
onMounted(() => input.value?.focus());
</script>
