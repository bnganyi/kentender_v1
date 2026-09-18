<!-- PLN-CHG-001 v1.23 §10.15 U16-COMPLETE — confirm that an activated plan
     version has corrected this request.

     The dialog names the exact request and the exact correcting version,
     because recording completion lifts this request's share of the hold and
     tells the requesting module it may start fresh work. Nothing here is
     editable: the plan was corrected elsewhere, and this only records that
     it was. -->
<template>
	<div class="kt-dialog-backdrop" data-testid="cor-complete-dialog">
		<div class="kt-dialog" role="dialog" aria-modal="true" aria-labelledby="cor-complete-title">
			<div id="cor-complete-title" class="kt-dialog-title">Record correction completed</div>
			<p class="pln-dialog-lede">{{ request.change_required }}</p>
			<div class="kt-meta-row">
				<div>
					<span class="kt-label">Request</span>
					<span class="kt-meta-value">{{ request.request }}</span>
				</div>
				<div>
					<span class="kt-label">Correcting plan</span>
					<span class="kt-meta-value">{{ correctingPlan.plan_reference }}</span>
				</div>
				<div>
					<span class="kt-label">Version</span>
					<span class="kt-meta-value">{{ correctingPlan.version_number }}</span>
				</div>
				<div>
					<span class="kt-label">Activation date</span>
					<span class="kt-meta-value">{{ correctingPlan.activated_display }}</span>
				</div>
			</div>
			<!-- Said before the action, not after it: this resolves one request
			     only, and the requesting module starts its own new work. -->
			<p class="pln-dialog-lede" data-testid="cor-complete-consequence">
				This resolves only this request. Any other unresolved request keeps the purchase on hold.
			</p>
			<p v-if="error" class="pln-dialog-error" role="alert">{{ error }}</p>
			<div class="kt-dialog-actions">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('cancel')">Cancel</button>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="cor-complete-confirm"
					:disabled="pending"
					@click="$emit('confirm')"
				>
					Record correction completed
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
defineProps({
	request: { type: Object, default: () => ({}) },
	correctingPlan: { type: Object, default: () => ({}) },
	pending: Boolean,
	error: String,
});

defineEmits(["confirm", "cancel"]);
</script>
