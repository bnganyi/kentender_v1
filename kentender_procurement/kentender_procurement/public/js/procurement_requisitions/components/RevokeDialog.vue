<!-- §13.13 "Revoke unconsumed authorisation?" — ported class-for-class: a
     required reason (20-1,000 characters), the fixed reversal notice, and
     Cancel/Revoke authorisation actions. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-revoke-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">Revoke unconsumed authorisation?</div>
			<div class="kt-field">
				<label for="revoke-reason">Reason</label>
				<textarea id="revoke-reason" class="kt-input" rows="3" minlength="20" maxlength="1000" placeholder="20–1,000 characters" :value="reason" @input="reason = $event.target.value"></textarea>
				<p v-if="fieldError" class="req-field-error">{{ fieldError }}</p>
			</div>
			<div class="req-context-body">The Planning drawdown and both Budget reservations will be reversed. The authorised Version remains in history.</div>
			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary kt-danger" :disabled="pending" data-testid="req-revoke-dialog-confirm" @click="confirm">Revoke authorisation</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onMounted, ref } from "vue";

defineProps({
	pending: Boolean,
	error: { type: String, default: "" },
});

const emit = defineEmits(["confirm", "cancel"]);

const dialogEl = ref(null);
const reason = ref("");
const fieldError = ref("");

function confirm() {
	const trimmed = reason.value.trim();
	if (trimmed.length < 20 || trimmed.length > 1000) {
		fieldError.value = "A reason of 20-1,000 characters is required.";
		return;
	}
	fieldError.value = "";
	emit("confirm", trimmed);
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
