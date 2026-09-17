<!-- PLN-CHG-001 v1.18 §5.6.3/§5.4.6, ported class-for-class from
     U21-dissolve-item. Confirms `DissolvePlanItem` on a Draft item; the
     caller owns the actual API call and idempotency key. A locked item
     (an authorised Requisition already drawn against it) cannot reach
     this dialog — the caller gates that before offering it. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="pln-dissolve-item-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="pln-dissolve-item-title">
			<div id="pln-dissolve-item-title" class="kt-dialog-title">Dissolve Plan Item?</div>
			<p class="pln-dialog-lede">
				Its eligible sources will return to this Draft's unallocated requirements. This action does not release Budget funds.
			</p>
			<p v-if="error" class="pln-dialog-error" role="alert" data-testid="pln-dissolve-item-error">
				{{ error }}
			</p>
			<div class="kt-dialog-actions">
				<button class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					class="kt-btn kt-btn-primary" data-testid="pln-dissolve-item-confirm"
					:disabled="pending" @click="$emit('confirm')"
				>
					Dissolve Plan Item
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
