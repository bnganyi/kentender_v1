<!-- PLN-CHG-001 v1.23 §10.17 U21-CANCEL-UPDATE. Confirms `CancelPlanUpdate`;
     the caller owns the API call and the idempotency key.

     The reassurance is the point of this dialog: cancelling an update changes
     nothing about the plan currently in force or any procurement already under
     way. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-cancel-update-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-cancel-update-title">
			<div id="pln-cancel-update-title" class="kt-dialog-title">Cancel this plan update?</div>
			<p class="pln-dialog-lede">
				The current plan and existing procurement will remain unchanged.
			</p>
			<div class="kt-field">
				<label for="pln-cancel-update-reason" class="kt-label">Reason</label>
				<textarea
					id="pln-cancel-update-reason"
					class="kt-input"
					rows="2"
					data-testid="pln-cancel-update-reason"
					:value="reason"
					@input="$emit('update:reason', $event.target.value)"
				></textarea>
			</div>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-cancel-update-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Keep update
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="pln-cancel-update-confirm"
					:disabled="pending || reason.trim().length < 20" @click="$emit('confirm')"
				>
					Cancel plan update
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
defineProps({
	pending: Boolean,
	error: String,
	reason: { type: String, default: "" },
});
defineEmits(["confirm", "cancel", "update:reason"]);
</script>
