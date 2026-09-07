<!-- §13.13 "Return Requisition for correction?" — ported class-for-class:
     a required "Correction required" textarea (20-1,000 characters) and
     Cancel/Return actions. Reused by both the Department task (§13.10) and
     Procurement task (§13.11) screens — the artboard draws one dialog, not
     two near-identical copies. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="req-return-dialog" @keydown.esc="$emit('cancel')">
		<div class="kt-dialog" role="dialog" aria-modal="true" ref="dialogEl" tabindex="-1">
			<div class="kt-dialog-title">Return Requisition for correction?</div>
			<div class="kt-field">
				<label for="return-reason">Correction required</label>
				<textarea id="return-reason" class="kt-input" rows="3" minlength="20" maxlength="1000" placeholder="20–1,000 characters" :value="reason" @input="reason = $event.target.value"></textarea>
				<p v-if="fieldError" class="req-field-error">{{ fieldError }}</p>
			</div>
			<p v-if="error" class="req-field-error" role="alert">{{ error }}</p>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" @click="$emit('cancel')">Cancel</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="req-return-dialog-confirm" @click="confirm">Return</button>
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
		fieldError.value = "A correction reason of 20-1,000 characters is required.";
		return;
	}
	fieldError.value = "";
	emit("confirm", trimmed);
}

onMounted(() => {
	nextTick(() => dialogEl.value && dialogEl.value.focus());
});
</script>
