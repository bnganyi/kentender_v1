<!-- PLN-CHG-001 v1.18 §8.2/invariant 21, ported class-for-class from
     U21-cancel-update. Confirms `CancelPlanUpdate`; the caller owns the
     actual API call and idempotency key. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-cancel-update-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-cancel-update-title">
			<div id="pln-cancel-update-title" class="kt-dialog-title">Cancel Plan update?</div>
			<p class="pln-dialog-lede">
				The open update will be cancelled. The Active Plan and existing procurement proceedings will remain unchanged.
			</p>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-cancel-update-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Keep update
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="pln-cancel-update-confirm"
					:disabled="pending" @click="$emit('confirm')"
				>
					Cancel update
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
defineProps({
	pending: Boolean,
	error: String,
});
defineEmits(["confirm", "cancel"]);
</script>
