<!-- PLN-CHG-001 v1.18 §5.1.4, ported class-for-class from U03's overlaid
     dialog. Confirms `SetNeedPlanningDisposition` (Do not proceed) for one
     Need-origin entry; the caller owns the actual API call, idempotency key
     and entry id. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-not-proceed-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-not-proceed-title">
			<div id="pln-not-proceed-title" class="kt-dialog-title">Do not proceed this financial year?</div>
			<div class="pln-field">
				<label for="pln-not-proceed-reason">Reason for not proceeding</label>
				<input
					id="pln-not-proceed-reason" class="kt-input" type="text"
					data-testid="pln-not-proceed-reason" v-model="reason"
				>
			</div>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-not-proceed-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="pln-not-proceed-confirm"
					:disabled="pending || reason.trim().length < 20"
					@click="$emit('confirm', reason.trim())"
				>
					Do not proceed
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";

defineProps({
	pending: Boolean,
	error: String,
});
defineEmits(["confirm", "cancel"]);

const reason = ref("");
</script>
