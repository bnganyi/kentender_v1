<!-- §13.13 "Request upstream correction?" — ported class-for-class from
     the reference dialogs artboard: a required Reason (20-1,000 characters,
     §7.4A step 1) and the fixed notice that Requisitions cannot edit an
     approved Planning fact and this Version will be preserved. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-upstream-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">Request upstream correction?</div>
			<div class="kt-field">
				<label for="upstream-reason">Reason</label>
				<textarea id="upstream-reason" class="kt-input" rows="3" minlength="20" maxlength="1000" :value="reason" @input="reason = $event.target.value"></textarea>
				<p v-if="fieldError" class="req-field-error">{{ fieldError }}</p>
			</div>
			<div class="req-notice">Requisitions cannot edit an approved Planning fact. This Requisition Version will be preserved.</div>
			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-upstream-dialog-confirm" @click="confirm">Request correction</button>
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
const reason = ref("The Plan Item's authorised warranty period does not match what the department actually needs; this must be corrected in Planning.");
const fieldError = ref("");

function confirm() {
	const trimmed = reason.value.trim();
	if (trimmed.length < 20 || trimmed.length > 1000) {
		fieldError.value = "A reason of 20-1,000 characters identifying the wrong Planning fact is required.";
		return;
	}
	fieldError.value = "";
	emit("confirm", trimmed);
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
